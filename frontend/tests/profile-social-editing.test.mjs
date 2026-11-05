import test from 'node:test'
import assert from 'node:assert/strict'
import {editableSocials,socialNetworks} from '../src/commerce/socials.js'
test('empty and legacy social values always produce editable fields',()=>{
 for(const value of [null,undefined,'null','{}','invalid',[],42]) {
  const fields=editableSocials(value)
  assert.deepEqual(Object.keys(fields),Object.keys(socialNetworks))
  assert.ok(Object.values(fields).every(x=>x===''))
  fields.linkedin='https://linkedin.com/in/test'
  assert.equal(fields.linkedin,'https://linkedin.com/in/test')
 }
})
test('existing social text survives editing without accepting non-text fields',()=>{
 assert.equal(editableSocials('{"linkedin":"https://linkedin.com/in/test"}').linkedin,'https://linkedin.com/in/test')
 assert.equal(editableSocials({facebook:null}).facebook,'')
})
