import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import {paymentMessage,reusableCheckout} from '../src/native/cybersourceCheckout.js'

const source=fs.readFileSync(new URL('../src/native/CyberSourcePayment.vue',import.meta.url),'utf8')
  .match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')
function harness({request,loadCheckoutLibrary,now=Date.now}) {
 const props={invoice:'draft-test',kind:'subscription',visible:true,review:true}
 let formHeight=0,selectionHeight=0,sync,dispose,reloads=0,timerId=0
 const timers=new Map()
 const form={parentNode:{},getBoundingClientRect:()=>({height:formHeight})}
 const selection={getBoundingClientRect:()=>({height:selectionHeight})}
 const context=vm.createContext({ref:value=>({value}),computed:fn=>({get value(){return fn()}}),
  onMounted(){},onBeforeUnmount(fn){dispose=fn},watch(){},nextTick:async()=>{},
  defineProps:()=>props,defineEmits:()=>()=>{},crypto:{randomUUID:()=> 'test'},
  setInterval(){},clearInterval(){},location:{hostname:'unit.test',reload(){reloads++}},performance,
  setTimeout(fn,delay){timers.set(++timerId,{fn,delay});return timerId},clearTimeout(id){timers.delete(id)},
  document:{getElementById:id=>id.endsWith('-screen')?form:selection},
  MutationObserver:class{constructor(fn){sync=fn}observe(){}disconnect(){}},
  ResizeObserver:class{observe(){}disconnect(){}},
  Date:class extends Date{static now(){return now()}},request,loadCheckoutLibrary,paymentMessage,reusableCheckout})
 vm.runInContext(source+';globalThis.ui={pay,pause,verify,busy,preparing,retryLoading,retained,message,formOpen,observeScreen,needsReview,buttonLabel,awaitingVerification,verificationPaused,verificationIssue,resumeVerification,paid};',context)
 context.ui.observeScreen()
 return {ui:context.ui,props,timers,dispose:()=>dispose(),reloads:()=>reloads,resize:(button,screen)=>{selectionHeight=button;formHeight=screen;sync()}}
}
function sdk(onMount=()=>{}) {
 let finish
 const events={}
 const checkout={on(event,fn){events[event]=fn},
  mount(target){events.mounted();onMount(target,events);return new Promise(resolve=>finish=resolve)},
  unmount(){finish?.('detached')},destroy(){finish?.('detached')},complete(){throw Error('Must not charge')}}
 return {UnifiedCheckout:async()=>({createCheckout:async()=>checkout,destroy(){}})}
}
const response=()=>({name:'attempt-test',session:'signed-test-context',session_expires:Date.now()/1000+900,mode:'sandbox',status:'pending',submission_grant:'one-time-grant'})
test('a failed script download retries the same session without a second start or processing event',async()=>{
 let requests=0,loads=0
 const {ui,resize,dispose}=harness({request:async()=>{requests++;return response()},loadCheckoutLibrary:async()=>{if(++loads===1)throw Error('network');return sdk()}})
 await ui.pay()
 assert.equal(ui.retryLoading.value,true);assert.equal(ui.busy.value,false)
 const retry=ui.pay()
 await new Promise(setImmediate)
 assert.equal(ui.retained.value,true);assert.equal(ui.preparing.value,true)
 resize(83,0);assert.equal(ui.preparing.value,false)
 ui.pause();dispose();await retry
 assert.equal(requests,1);assert.equal(loads,2)
})
test('the secure form is embedded in the popup and provider back restores payment selection',async()=>{
 let events,containers
 const {ui,dispose}=harness({request:async()=>response(),loadCheckoutLibrary:async()=>sdk((target,listeners)=>{containers=target;events=listeners})})
 const pending=ui.pay();await new Promise(setImmediate)
 assert.equal(containers.paymentSelection,'#cybs-checkout-test')
 assert.equal(containers.paymentScreen,'#cybs-checkout-test-screen')
 events.paymentMethodSelected();assert.equal(ui.formOpen.value,true)
 events.paymentMethodCancelled();assert.equal(ui.formOpen.value,false)
 events.paymentMethodSelected();ui.pause()
 assert.equal(ui.formOpen.value,true)
 assert.equal(ui.busy.value,true)
 dispose();await pending
})
test('closing and immediately reopening during preparation does not duplicate a session',async()=>{
 let finishRequest,requests=0
 const {ui,props,resize,dispose}=harness({request:()=>{requests++;return new Promise(r=>finishRequest=r)},loadCheckoutLibrary:async()=>sdk()})
 const first=ui.pay();props.visible=false;ui.pause();props.visible=true
 await ui.pay()
 assert.equal(requests,1);assert.equal(ui.busy.value,true)
 finishRequest(response())
 await new Promise(setImmediate)
 resize(83,0)
 assert.equal(ui.retained.value,true);assert.equal(ui.preparing.value,false)
 ui.pause();dispose();await first
 assert.equal(requests,1)
})
test('frame resizing opens the popup form even when the SDK selection event is absent',()=>{
 const {ui,resize,dispose}=harness({request:async()=>response(),loadCheckoutLibrary:async()=>sdk()})
 resize(83,1);assert.equal(ui.formOpen.value,false)
 resize(0,420);assert.equal(ui.formOpen.value,true)
 resize(83,0);assert.equal(ui.formOpen.value,false)
})
test('an expired failed download returns to server recovery instead of replaying its context',async()=>{
 let now=Date.now(),requests=0,loads=0
 const {ui}=harness({now:()=>now,request:async()=>++requests===1?response():{name:'attempt-test',status:'pending',retry_after:now/1000+300},loadCheckoutLibrary:async()=>{loads++;throw Error('offline')}})
 await ui.pay();assert.equal(ui.retryLoading.value,true)
 now+=1000000
 await ui.pay()
 assert.equal(requests,2);assert.equal(loads,1)
 assert.equal(ui.retryLoading.value,false)
 assert.match(ui.message.value,/reserved/)
})

test('closing and reopening preserves the same form without a new session or mount',async()=>{
 let starts=0,mounts=0
 const {ui,props,resize,dispose}=harness({request:async()=>{starts++;return response()},loadCheckoutLibrary:async()=>sdk(()=>mounts++)})
 const pending=ui.pay();await new Promise(setImmediate)
 resize(83,420);assert.equal(ui.formOpen.value,true)
 props.visible=false;ui.pause();resize(0,0)
 assert.equal(ui.formOpen.value,true)
 props.visible=true;resize(83,420);await ui.pay()
 assert.equal(starts,1);assert.equal(mounts,1);assert.equal(ui.formOpen.value,true)
 dispose();await pending
})
test('a rejected submission grant prevents the SDK from processing payment',async()=>{
 let complete=0,claimed
 const library={UnifiedCheckout:async()=>({createCheckout:async()=>({on(){},mount:async()=> 'transient-test-token',destroy(){},complete:async()=>{complete++}}),destroy(){}})}
 const {ui}=harness({loadCheckoutLibrary:async()=>library,request:async(module,method,args)=>{
  if(method==='start')return response()
  if(args.event==='processing'){claimed=args.submission_grant;throw Error('Checkout reopened elsewhere')}
  return {}
 }})
 await ui.pay()
 assert.equal(claimed,'one-time-grant');assert.equal(complete,0)
})

test('session creation failure offers an explicit retry and opens on the next click',async()=>{
 let starts=0
 const {ui,dispose}=harness({request:async()=>++starts===1?{name:'failed-start',status:'failed',session_unavailable:true}:response(),loadCheckoutLibrary:async()=>sdk()})
 await ui.pay()
 assert.equal(ui.needsReview.value,false);assert.equal(ui.buttonLabel.value,'Retry opening checkout')
 assert.match(ui.message.value,/No payment was submitted/)
 const retry=ui.pay();await new Promise(setImmediate)
 assert.equal(starts,2);assert.equal(ui.retained.value,true)
 dispose();await retry
})
test('a genuine review state hides the misleading reopen action',async()=>{
 const {ui}=harness({request:async()=>({name:'submitted',status:'review',transaction_id:'123'}),loadCheckoutLibrary:async()=>{throw Error('Must not open')}})
 await ui.pay();assert.equal(ui.needsReview.value,true)
})

test('a genuinely different SDK offers reload instead of an endless download retry',async()=>{
 let requests=0
 const {ui,reloads}=harness({request:async()=>{requests++;return response()},loadCheckoutLibrary:async()=>{throw Object.assign(Error('Updated library'),{code:'CHECKOUT_RELOAD_REQUIRED'})}})
 await ui.pay()
 assert.equal(ui.buttonLabel.value,'Reload page');assert.equal(ui.retryLoading.value,false)
 assert.match(ui.message.value,/Reload this page/)
 await ui.pay()
 assert.equal(reloads(),1);assert.equal(requests,1)
})

test('submitted payments offer verification instead of another checkout',async()=>{
 const {ui}=harness({request:async()=>({name:'submitted',status:'pending',browser_event:'completed'}),loadCheckoutLibrary:async()=>{throw Error('Must not open')}})
 await ui.pay();assert.equal(ui.awaitingVerification.value,true)
})

test('submitted verification retries are bounded and never submit another payment',async()=>{
 const calls=[]
 const {ui,timers,dispose}=harness({request:async(service,method)=>{
  calls.push(method);return {name:'submitted',status:'pending',browser_event:'completed'}
 },loadCheckoutLibrary:async()=>{throw Error('Must not open')}})
 await ui.pay();await ui.verify()
 for(let i=0;i<12;i++){
  assert.equal(timers.size,1)
  const [id,timer]=[...timers][0];assert.ok(timer.delay>=15000)
  timers.delete(id);timer.fn();await new Promise(resolve=>setImmediate(resolve))
 }
 assert.equal(timers.size,0)
 assert.equal(calls.filter(x=>x==='start').length,1)
 assert.equal(calls.filter(x=>x==='reconcile').length,13)
 assert.ok(calls.every(x=>['start','reconcile'].includes(x)))
 dispose();assert.equal(timers.size,0)
})

test('verified or disposed checkout cancels further verification',async()=>{
 let status='pending'
 const {ui,timers,dispose}=harness({request:async()=>({name:'submitted',status,browser_event:'completed'})})
 await ui.pay();await ui.verify();assert.equal(timers.size,1)
 status='succeeded';await ui.verify();assert.equal(timers.size,0)
 dispose();assert.equal(timers.size,0)
})


test('transaction-backed pending payment polls without a completed browser event',async()=>{
 const {ui,timers}=harness({request:async()=>({name:'submitted',status:'pending',transaction_id:'123'})})
 await ui.pay();assert.equal(ui.awaitingVerification.value,true);assert.equal(timers.size,1)
})

test('verification network failure retries automatically without opening checkout',async()=>{
 const calls=[]
 const {ui,timers}=harness({request:async(service,method)=>{
  calls.push(method)
  if(method==='reconcile')throw Error('offline')
  return {name:'submitted',status:'pending',browser_event:'completed'}
 }})
 await ui.pay();await ui.verify()
 assert.equal(ui.verificationIssue.value,true);assert.equal(timers.size,1)
 assert.equal(ui.awaitingVerification.value,true);assert.deepEqual(calls,['start','reconcile'])
})

test('exhausted verification stops the spinner and resumes status reads only',async()=>{
 const calls=[];let status='pending'
 const {ui,timers}=harness({request:async(service,method)=>{calls.push(method);return {name:'submitted',status,browser_event:'completed'}}})
 await ui.pay()
 for(let i=0;i<12;i++){
  const [id,timer]=[...timers][0];timers.delete(id);timer.fn();await new Promise(setImmediate)
 }
 assert.equal(ui.verificationPaused.value,true);assert.equal(timers.size,0)
 status='succeeded';await ui.resumeVerification()
 assert.equal(ui.paid.value,true);assert.equal(ui.verificationPaused.value,false)
 assert.equal(calls.filter(x=>x==='start').length,1);assert.equal(timers.size,0)
})
