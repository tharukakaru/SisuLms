import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import {passwordStrength} from '../src/native/passwordStrength.js'

const source=fs.readFileSync(new URL('../src/native/VerifiedSignup.vue',import.meta.url),'utf8')
const setup=source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')
const settle=()=>new Promise(resolve=>setImmediate(resolve))
function harness(request=async()=>({challenge:'test-challenge'})){
 const redirects=[],calls=[],dialog={open:false,showModal(){this.open=true},close(){this.open=false}}
 let focused=0
 const c={location:{assign:url=>redirects.push(url)},passwordStrength,ref:value=>({value}),computed:fn=>({get value(){return fn()}}),nextTick:async fn=>fn?.(),onMounted:()=>{},onUnmounted:()=>{},setInterval:()=>0,clearInterval:()=>{},sessionStorage:{getItem:()=>null,setItem:()=>{}},defineProps:()=>({googleSession:true,policy:{privacy_policy_version:'test'}}),defineEmits:()=>()=>{},request:async(...args)=>{calls.push(args);return request(...args)},csrf:()=>'',fetch:async()=>({ok:true}),Intl,Date}
 vm.createContext(c)
 vm.runInContext(setup+'\nglobalThis.state={verificationDialog,verificationOpen,resumeVerification,token,emailCode,phoneCode,emailOK,phoneOK,password,confirmation,busy,error,done,form,verificationStep,phoneDraft,phoneSent,primaryDisabled,primaryLabel,strength,passwordLength};',c)
 c.state.verificationDialog.value=dialog
 c.state.resumeVerification.value={focus(){focused++}}
 return {c,calls,redirects,dialog,state:c.state,focused:()=>focused}
}
test('successful Google email request opens verification popup',async()=>{
 const h=harness();h.c.start();await settle()
 assert.equal(h.dialog.open,true);assert.equal(h.state.token.value,'test-challenge');assert.equal(h.state.busy.value,false)
})
test('close and reopen preserves verification without sending another code',async()=>{
 const h=harness();h.c.start();await settle();h.state.emailCode.value='123456';h.state.emailOK.value=true
 h.c.closeVerification();await settle();assert.equal(h.dialog.open,false);assert.equal(h.focused(),1)
 await h.c.openVerification();assert.equal(h.state.emailCode.value,'123456');assert.equal(h.state.emailOK.value,true)
 assert.equal(h.calls.length,1)
})
test('pending request prevents dismissal and duplicate submission',async()=>{
 let resolve;const h=harness(()=>new Promise(r=>resolve=r))
 await h.c.openVerification();h.c.start();h.c.start();h.c.closeVerification()
 assert.equal(h.dialog.open,true);assert.equal(h.calls.length,1)
 resolve({challenge:'test'});await settle();assert.equal(h.state.busy.value,false)
})
test('failed verification retains code and proof state for retry',async()=>{
 const h=harness(async()=>{throw Error('Code did not match')});await h.c.openVerification();h.state.emailCode.value='000000'
 h.c.verify('email');await settle()
 assert.equal(h.dialog.open,true);assert.equal(h.state.emailOK.value,false);assert.equal(h.state.emailCode.value,'000000');assert.equal(h.state.error.value,'Code did not match')
})
test('edit details closes popup and resets verification and password values',async()=>{
 const h=harness();await h.c.openVerification();h.state.token.value='test';h.state.emailOK.value=true;h.state.password.value='sensitive-test-value';h.state.error.value='old'
 h.c.reset();await settle();assert.equal(h.dialog.open,false);assert.equal(h.state.token.value,'');assert.equal(h.state.emailOK.value,false);assert.equal(h.state.password.value,'');assert.equal(h.state.error.value,'')
})

test('verification advances through email, number confirmation, SMS and password in order',async()=>{
 const h=harness(async()=>({verified:true,sent:true}));h.state.form.value.phone='+94761234567';h.state.emailCode.value='123456'
 h.c.submitVerification();await settle();assert.equal(h.state.verificationStep.value,'phone');assert.equal(h.state.emailOK.value,true)
 assert.equal(h.calls.length,1);assert.equal(h.calls[0][1],'self_verify')
 h.c.submitVerification();await settle();assert.equal(h.state.verificationStep.value,'code');assert.equal(h.calls[1][1],'self_phone')
 assert.equal(h.state.primaryDisabled.value,true)
 h.state.phoneCode.value='123456';h.c.submitVerification();await settle();assert.equal(h.state.verificationStep.value,'password');assert.equal(h.state.phoneOK.value,true)
 assert.equal(h.state.primaryLabel.value,'Save and verify account')
})
test('phone correction sends the new number and requires its own proof',async()=>{
 const h=harness();h.state.emailOK.value=true;h.state.phoneOK.value=true;h.state.form.value.phone='+94761234567';h.state.phoneDraft.value='+94771234567';h.state.verificationStep.value='phone'
 h.c.phone();await settle();assert.equal(h.calls[0][2].phone,'+94771234567');assert.equal(h.state.form.value.phone,'+94771234567');assert.equal(h.state.phoneOK.value,false);assert.equal(h.state.emailOK.value,true);assert.equal(h.state.verificationStep.value,'code')
})
test('reviewing a verified unchanged phone does not send another SMS',async()=>{
 const h=harness();h.state.emailOK.value=true;h.state.phoneOK.value=true;h.state.form.value.phone='+94761234567';h.state.verificationStep.value='password'
 h.c.previousStep();assert.equal(h.state.verificationStep.value,'phone');assert.equal(h.state.primaryLabel.value,'Continue')
 h.c.submitVerification();await settle();assert.equal(h.state.verificationStep.value,'password');assert.equal(h.calls.length,0)
})
test('only matching passwords of eight or more characters enable final save',async()=>{
 const h=harness();h.state.verificationStep.value='password';h.state.emailOK.value=true;h.state.phoneOK.value=true
 h.state.password.value='Ab3!xyz';h.state.confirmation.value='Ab3!xyz';assert.equal(h.state.primaryDisabled.value,true)
 h.state.password.value='Ab3!xyzw';assert.equal(h.state.primaryDisabled.value,true)
 h.state.confirmation.value='Ab3!xyzw';assert.equal(h.state.primaryDisabled.value,false)
 h.c.submitVerification();await settle();assert.equal(h.calls[0][1],'self_complete');assert.equal(h.state.done.value,true)
})
test('strength feedback distinguishes short and common passwords from a long varied phrase',()=>{
 assert.equal(passwordStrength('abc').label,'Too short');assert.equal(passwordStrength('password123!').label,'Weak')
 assert.equal(passwordStrength('AAAAAAAAAAAAAAAAAAAA1!').label,'Weak')
 assert.ok(passwordStrength('Three gardens bloom 7!').score>passwordStrength('Ab3!xyzw').score)
})

test('Google signup back control signs out and navigates to student login',async()=>{
 const h=harness();let signouts=0
 h.c.fetch=async(url,options)=>{assert.equal(url,'/api/method/logout');assert.equal(options.method,'POST');signouts++;return {ok:true}}
 h.c.backToSignIn();await settle()
 assert.equal(signouts,1);assert.deepEqual(h.redirects,['/login?redirect-to=/campus'])
})
test('failed sign-out keeps signup details available and allows retry',async()=>{
 const h=harness();h.state.form.value.username='keep_my_details';h.c.fetch=async()=>({ok:false})
 h.c.backToSignIn();await settle()
 assert.equal(h.redirects.length,0);assert.match(h.state.error.value,/try again/)
 assert.equal(h.state.form.value.username,'keep_my_details');assert.equal(h.state.busy.value,false)
})
