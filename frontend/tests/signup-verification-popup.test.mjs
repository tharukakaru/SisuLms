import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import {passwordStrength} from '../src/native/passwordStrength.js'

const source=fs.readFileSync(new URL('../src/native/VerifiedSignup.vue',import.meta.url),'utf8')
const setup=source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')
const settle=()=>new Promise(resolve=>setImmediate(resolve))
function harness(request=async()=>({challenge:'test-challenge'}),props={},storedRole=null){
 const redirects=[],calls=[],dialog={open:false,showModal(){this.open=true},close(){this.open=false}}
 let focused=0
 const c={location:{assign:url=>redirects.push(url)},passwordStrength,ref:value=>({value}),computed:fn=>({get value(){return fn()}}),nextTick:async fn=>fn?.(),onMounted:()=>{},onUnmounted:()=>{},setInterval:()=>0,clearInterval:()=>{},sessionStorage:{getItem:()=>storedRole,setItem:()=>{}},defineProps:()=>({googleSession:true,policy:{privacy_policy_version:'test'},...props}),defineEmits:()=>()=>{},request:async(...args)=>{calls.push(args);return request(...args)},csrf:()=>'',fetch:async()=>({ok:true}),Intl,Date}
 vm.createContext(c)
 vm.runInContext(setup+'\nglobalThis.state={accountExists,verificationDialog,verificationOpen,resumeVerification,token,emailCode,phoneCode,emailOK,phoneOK,password,confirmation,busy,error,done,form,verificationStep,phoneDraft,phoneSent,primaryDisabled,primaryLabel,strength,passwordLength,successDialog,leavingSuccess,successError};',c)
 c.state.verificationDialog.value=dialog
 c.state.successDialog.value={open:false,showModal(){this.open=true},close(){this.open=false}}
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

test('saving closes password popup and shows success without navigating or signing out',async()=>{
 const h=harness();let signouts=0;h.c.fetch=async()=>{signouts++;return {ok:true}}
 await h.c.openVerification();h.state.password.value='test-only-password';h.state.confirmation.value='test-only-password'
 h.c.save();await settle()
 assert.equal(h.dialog.open,false);assert.equal(h.state.verificationOpen.value,false)
 assert.equal(h.state.successDialog.value.open,true);assert.equal(h.state.done.value,true)
 assert.equal(h.state.password.value,'');assert.equal(h.state.confirmation.value,'')
 assert.equal(signouts,0);assert.deepEqual(h.redirects,[])
})

test('success exit waits for Google sign-out and ignores duplicate clicks',async()=>{
 const h=harness();let finish,signouts=0
 h.c.fetch=()=>{signouts++;return new Promise(resolve=>finish=resolve)}
 const first=h.c.closeSuccess();await h.c.closeSuccess()
 assert.equal(signouts,1);assert.equal(h.state.leavingSuccess.value,true);assert.deepEqual(h.redirects,[])
 finish({ok:true});await first
 assert.deepEqual(h.redirects,['/login?redirect-to=/campus'])
})

test('failed success exit retains confirmation and retries sign-out without recreating the account',async()=>{
 const h=harness();h.c.save();await settle();h.c.fetch=async()=>({ok:false})
 await h.c.closeSuccess()
 assert.equal(h.state.done.value,true);assert.equal(h.state.successDialog.value.open,true)
 assert.equal(h.state.leavingSuccess.value,false);assert.match(h.state.successError.value,/account is saved/)
 assert.deepEqual(h.redirects,[]);assert.equal(h.calls.filter(c=>c[1]==='self_complete').length,1)
 h.c.fetch=async()=>({ok:true});await h.c.closeSuccess()
 assert.deepEqual(h.redirects,['/login?redirect-to=/campus'])
 assert.equal(h.calls.filter(c=>c[1]==='self_complete').length,1)
})

test('failed save keeps the password popup open and does not show success',async()=>{
 const h=harness(async()=>{throw Error('Could not save')});await h.c.openVerification()
 h.c.save();await settle()
 assert.equal(h.dialog.open,true);assert.equal(h.state.done.value,false)
 assert.equal(h.state.successDialog.value.open,false);assert.deepEqual(h.redirects,[])
})

test('email signup success goes directly to student login on explicit exit',async()=>{
 const h=harness();vm.runInContext('props.googleSession=false',h.c)
 h.c.fetch=async()=>{throw Error('Email signup must not need Google sign-out')}
 await h.c.closeSuccess()
 assert.deepEqual(h.redirects,['/login?redirect-to=/campus'])
})


test('existing student email opens account dialog without starting verification',async()=>{
 const h=harness(async()=>({account_exists:true}));h.c.start();await settle()
 assert.equal(h.state.accountExists.value,true);assert.equal(h.state.token.value,'');assert.equal(h.dialog.open,false)
})
test('a username collision does not claim the email already has an account',async()=>{
 const h=harness(async()=>{throw Error('Account details are unavailable. Sign in if you already registered.')});h.c.start();await settle()
 assert.equal(h.state.accountExists.value,false);assert.equal(h.dialog.open,false)
})


test('selected provider form overrides a stale stored student role and submits the correct account type',async()=>{
 for(const [kind,serverKind,path] of [['Individual Teacher','Individual Teacher','individual'],['Institute Teacher','Individual Teacher','institute'],['Institute','Institute','individual']]){
  const h=harness(undefined,{googleSession:false,initialKind:kind},'Student')
  assert.equal(h.state.form.value.kind,kind)
  h.state.password.value='Test-password-only';h.state.confirmation.value='Test-password-only'
  h.c.start();await settle()
  const data=h.calls[0][2].data
  assert.equal(data.kind,serverKind);assert.equal(data.teaching_path,path)
 }
})
test('student entry cannot inherit a previous teacher or institute selection',()=>{
 for(const stored of ['Individual Teacher','Institute Teacher','Institute']){
  const h=harness(undefined,{googleSession:false,studentOnly:true},stored)
  assert.equal(h.state.form.value.kind,'Student')
 }
})
