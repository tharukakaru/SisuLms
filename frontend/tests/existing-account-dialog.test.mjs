import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('../src/native/ExistingAccountDialog.vue',import.meta.url),'utf8').match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')
function harness(authenticated,endSession=async()=>{}){
 const redirects=[];let ended=0
 const c={ref:value=>({value}),defineProps:()=>({authenticated}),onMounted:()=>{},onUnmounted:()=>{},endSession:()=>{ended++;return endSession()},window:{location:{assign:url=>redirects.push(url)}}}
 vm.createContext(c);vm.runInContext(source+';globalThis.state={busy,error}',c)
 return {c,redirects,ended:()=>ended}
}
test('email popup opens student login without logging into the account',async()=>{
 const h=harness(false);await h.c.login();assert.equal(h.ended(),0);assert.deepEqual(h.redirects,['/login?redirect-to=/campus'])
})
test('Google popup ends the authenticated session before navigating',async()=>{
 let complete;const h=harness(true,()=>new Promise(resolve=>complete=resolve));const pending=h.c.login();await h.c.login()
 assert.equal(h.ended(),1);assert.equal(h.redirects.length,0);complete();await pending
 assert.deepEqual(h.redirects,['/login?redirect-to=/campus'])
})
test('failed sign out remains in the dialog and permits retry',async()=>{
 const h=harness(true,async()=>{throw Error('offline')});await h.c.login()
 assert.equal(h.redirects.length,0);assert.equal(h.c.state.busy.value,false);assert.match(h.c.state.error.value,/try again/)
})


const {googleSignupEntry}=await import('../src/native/existingAccount.js')
test('ordinary Google login and guests do not trigger duplicate signup checks',async()=>{
 const request=()=>{throw Error('must not request')}
 assert.equal(await googleSignupEntry({authenticated:true},false,request),null)
 assert.equal(await googleSignupEntry({authenticated:false},true,request),null)
})
test('registered Google signup selects the popup instead of dashboard routing',async()=>{
 const calls=[]
 const result=await googleSignupEntry({authenticated:true,member:{role:'Student'}},true,async(module,method)=>{
  calls.push(method);return module==='portal_policy'?{self_signup_enabled:true}:{account_exists:true}
 })
 assert.equal(result.accountExists,true);assert.equal(result.policy.self_signup_enabled,true)
 assert.deepEqual(calls,['public','self_google_details'])
})
test('a new Google identity continues signup after policy is loaded',async()=>{
 const result=await googleSignupEntry({authenticated:true},true,async(module)=>module==='portal_policy'?{self_signup_enabled:true}:{email:'new@example.invalid'})
 assert.equal(result.accountExists,false);assert.equal(result.policy.self_signup_enabled,true)
})
