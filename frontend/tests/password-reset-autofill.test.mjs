import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('../../institute_lms/public/login-presentation.js',import.meta.url),'utf8')
const helper=source.slice(source.indexOf('  function protectResetLinkFromAutofill'),source.indexOf('  function decorate()'))
function setup(pathname,search){
 const events={},windowEvents={};const old={value:'autofilled',disabled:false,form:{addEventListener(name,fn,capture){assert.equal(capture,true);events[name]=fn}}}
 vm.runInNewContext(helper+'\nprotectResetLinkFromAutofill()',{
  location:{pathname,search},URLSearchParams,document:{getElementById(id){assert.equal(id,'old_password');return old}},window:{addEventListener(name,fn){windowEvents[name]=fn}}
 })
 return {old,events,windowEvents}
}
test('reset link excludes hidden autofilled old password before native validation',()=>{
 const {old,events,windowEvents}=setup('/update-password','?key=synthetic-test-key')
 assert.equal(old.value,'');assert.equal(old.disabled,true)
 for(const event of ['input','change','keyup','paste','submit']){old.value='autofilled-again';events[event]();assert.equal(old.value,'')}
 old.value='restored';windowEvents.pageshow();assert.equal(old.value,'')
})
test('ordinary password changes retain their old password field',()=>{
 for(const [path,search] of [['/update-password',''],['/update-password','?key='],['/login','?key=test']]){
  const {old,events}=setup(path,search);assert.equal(old.value,'autofilled');assert.equal(old.disabled,false);assert.deepEqual(events,{})
 }
})
