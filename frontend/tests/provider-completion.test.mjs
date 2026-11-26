import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('../src/native/ProviderFirstLogin.vue',import.meta.url),'utf8')
const setup=source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')
function harness(session,fail=false,unifiedTeacher=false){
 const events=[],calls=[],redirects=[],mounted=[]
 const dialog={open:false,showModal(){this.open=true},close(){this.open=false}}
 const c={ref:value=>({value}),nextTick:async()=>{},onMounted:fn=>mounted.push(fn),defineProps:()=>({session,unifiedTeacher}),defineEmits:()=>e=>events.push(e),
 request:async(...args)=>{calls.push(args);if(fail)throw Error('Please retry')},csrf:()=>'',decode:async()=>({}),fetch:async()=>({}),location:{assign:url=>redirects.push(url)}}
 vm.createContext(c);vm.runInContext(setup+'\nglobalThis.state={verified,saved,confirmation,showInstitutes,error,busy,completed,dashboard,chooseInstitutes,login}',c)
 c.state.confirmation.value=dialog
 return {...c.state,mounted,events,calls,redirects,dialog}
}
test('newly approved institute reconnects immediately without logout or pending popup',async()=>{
 const h=harness({onboarding_kind:'Institute'});h.verified.value=true
 await h.completed();assert.equal(h.dialog.open,false);assert.equal(h.redirects.length,0)
 assert.deepEqual(h.events,['completed']);assert.equal(h.calls.length,0)
})
test('returning completed providers resume workspace; institute teachers resume selection',async()=>{
 for(const kind of ['Teacher','Institute']){
  const h=harness({onboarding_kind:kind,provider_workspace_pending:true,teaching_path:'individual'})
  await h.mounted[0]();assert.deepEqual(h.events,['continue']);assert.equal(h.redirects.length,0)
 }
 const teacher=harness({onboarding_kind:'Teacher',provider_workspace_pending:true,teaching_path:'institute'})
 await teacher.mounted[0]();assert.equal(teacher.showInstitutes.value,true);assert.equal(teacher.calls.length,0)
})
test('workspace failure keeps the success state and allows retry or sign in',async()=>{
 const h=harness({provider_workspace_pending:true},true);await h.dashboard()
 assert.equal(h.events.length,0);assert.equal(h.busy.value,false);assert.equal(h.error.value,'Please retry')
 await h.login();assert.deepEqual(h.redirects,['/login?redirect-to=/campus'])
})

test('unified teacher completion continues immediately without the legacy popup',async()=>{
 const h=harness({onboarding_kind:'Teacher',teaching_path:'institute'},false,true)
 h.verified.value=true;await h.completed()
 assert.equal(h.dialog.open,false);assert.deepEqual(h.events,['completed'])
 assert.equal(h.calls.length,0);assert.equal(h.redirects.length,0)
 const returning=harness({onboarding_kind:'Teacher',provider_workspace_pending:true},false,true)
 await returning.mounted[0]()
 assert.equal(returning.calls[0][0],'teacher_workspace');assert.deepEqual(returning.events,['completed'])
})
