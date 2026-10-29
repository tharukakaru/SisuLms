import test from 'node:test'
import assert from 'node:assert/strict'
import {endSession} from '../src/logout.js'
const reply = message => ({ok:true,json:async()=>({message})})
test('logout POST uses current CSRF and verifies guest session',async()=>{
  const calls=[]
  const responses=[reply({authenticated:true,csrf_token:'fresh'}),{ok:true},reply({authenticated:false})]
  await endSession(async(url,options)=>{calls.push({url,...options});return responses.shift()})
  assert.equal(calls[1].method,'POST')
  assert.equal(calls[1].headers['X-Frappe-CSRF-Token'],'fresh')
  assert.ok(calls.every(call=>call.cache==='no-store'&&call.credentials==='same-origin'))
})
test('logout failure is not reported as success',async()=>{
  const responses=[reply({authenticated:true,csrf_token:'fresh'}),{ok:false}]
  await assert.rejects(endSession(async()=>responses.shift()),/Sign out failed/)
})
test('remaining authenticated session is rejected',async()=>{
  const responses=[reply({authenticated:true,csrf_token:'fresh'}),{ok:true},reply({authenticated:true})]
  await assert.rejects(endSession(async()=>responses.shift()),/still active/)
})
test('already signed-out session needs no POST',async()=>{
  const calls=[]
  await endSession(async(url,options)=>{calls.push(options);return reply({authenticated:false})})
  assert.ok(calls.every(call=>!call.method))
})
