import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('../../institute_lms/public/login-presentation.js',import.meta.url),'utf8')
const helper=source.slice(source.indexOf('  function installPasswordUpdateTransport'),source.indexOf('  function decorate()'))
function setup(path='/update-password'){
 const calls=[],result={};const window={frappe:{call(...args){calls.push(args);return result}}}
 vm.runInNewContext(helper+'\ninstallPasswordUpdateTransport()',{window,location:{pathname:path},Set})
 return {window,calls,result}
}
test('reset submission and strength requests use API with original callbacks and args',()=>{
 const {window,calls,result}=setup()
 for(const method of ['update_password','test_password_strength']){
  const options={method:'frappe.core.doctype.user.user.'+method,args:{key:'synthetic'},statusCode:{200(){}}}
  assert.equal(window.frappe.call(options),result)
  const sent=calls.at(-1)[0];assert.equal(sent.url,'/api/method/'+options.method)
  assert.equal(sent.args,options.args);assert.equal(sent.statusCode,options.statusCode);assert.equal(options.url,undefined)
 }
})
test('unrelated calls, explicit URLs and other pages remain unchanged',()=>{
 for(const [path,options] of [['/login',{method:'frappe.core.doctype.user.user.update_password'}],['/update-password',{method:'other'}],['/update-password',{method:'frappe.core.doctype.user.user.update_password',url:'/custom'}]]){
  const {window,calls}=setup(path);window.frappe.call(options);assert.equal(calls[0][0],options)
 }
})
