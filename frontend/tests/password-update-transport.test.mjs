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
  assert.equal(sent.args,options.args);assert.equal(typeof sent.statusCode[200],'function');assert.equal(options.url,undefined)
 }
})
test('unrelated calls, explicit URLs and other pages remain unchanged',()=>{
 for(const [path,options] of [['/login',{method:'frappe.core.doctype.user.user.update_password'}],['/update-password',{method:'other'}],['/update-password',{method:'frappe.core.doctype.user.user.update_password',url:'/custom'}]]){
  const {window,calls}=setup(path);window.frappe.call(options);assert.equal(calls[0][0],options)
 }
})


test('successful desk redirect becomes campus without changing auth redirects or errors',()=>{
 const {window,calls}=setup(); const received=[]; const context={};
 const handler=function(...args){received.push([this,...args]);return 'handled'};
 const denied=()=>{};
 const options={method:'frappe.core.doctype.user.user.update_password',statusCode:{200:handler,401:denied}};
 window.frappe.call(options);
 const statuses=calls[0][0].statusCode;
 assert.equal(statuses[401],denied);assert.equal(options.statusCode[200],handler);
 for(const response of [{message:'/desk'},{message:'/login'},{message:'/campus'},{message:'/custom'},{message:'/desk',exc:'error'},{message:'/desk',exc_type:'PermissionError'},{}]){
  assert.equal(statuses[200].call(context,response,'ok'),'handled');
  const [receiver,actual,extra]=received.at(-1);
  assert.equal(receiver,context);assert.equal(extra,'ok');
  if(response.message==='/desk'&&!response.exc&&!response.exc_type){
   assert.equal(actual.message,'/campus');assert.equal(response.message,'/desk');
  }else assert.equal(actual,response);
 }
})
