import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('../../institute_lms/public/login-presentation.js',import.meta.url),'utf8')
function setup(){
 const calls=[],state={};const pending={fail(fn){state.fail=fn;return this},always(fn){state.always=fn;return this}}
 const window={login:{call(...args){calls.push(args);return pending},hide_loading(){state.hidden=true},show_error_banner(message){state.error=message}}}
 vm.runInNewContext(source.slice(source.indexOf('  function installPasswordRecoveryTransport'),source.indexOf('  function decorate()'))+'\ninstallPasswordRecoveryTransport()', {window})
 return {window,calls,state,pending}
}
test('password recovery uses API and preserves arguments and request handle',()=>{
 const {window,calls,pending}=setup(),args={cmd:'frappe.core.doctype.user.user.reset_password',user:'example@example.test'},callback=()=>{}
 assert.equal(window.login.call(args,callback,'/','notice'),pending)
 assert.deepEqual(calls[0],[args,callback,'/api/method/frappe.core.doctype.user.user.reset_password','notice'])
})
test('reset transport failure reports error and always clears loading',()=>{
 const {window,state}=setup();window.login.call({cmd:'frappe.core.doctype.user.user.reset_password'})
 state.fail();state.always();assert.match(state.error,/try again/);assert.equal(state.hidden,true)
})
test('login and other authentication calls retain their original route',()=>{
 const {window,calls,state}=setup(),args={cmd:'login'};window.login.call(args,null,'/','error')
 assert.deepEqual(calls[0],[args,null,'/','error']);assert.equal(state.fail,undefined)
})
