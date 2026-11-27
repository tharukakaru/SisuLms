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


test('sign-out navigation waits for session verification and opens SISU login',async()=>{
  const {readFileSync}=await import('node:fs')
  const {runInNewContext}=await import('node:vm')
  const source=readFileSync(new URL('../src/logout.js',import.meta.url),'utf8')
  let click
  const redirects=[],broadcasts=[]
  const ctx={window:{addEventListener(){},location:{replace:url=>redirects.push(url)}},document:{addEventListener:(_,fn)=>click=fn},BroadcastChannel:class {postMessage(message){broadcasts.push(message)}}}
  runInNewContext(source.replace(/export /g,'')+'; endSession=()=>{requests++;return new Promise(r=>complete=r)}; installSignOut();',Object.assign(ctx,{requests:0,complete:null}))
  const link={setAttribute(){}}
  const event={target:{closest:()=>link},preventDefault(){}}
  const pending=click(event);await click(event)
  assert.equal(ctx.requests,1);assert.deepEqual(redirects,[])
  ctx.complete();await pending
  assert.deepEqual(redirects,['/login?redirect-to=/campus'])
  assert.deepEqual(broadcasts,['signed-out'])
})

test('a sign-out from another tab returns to SISU login',async()=>{
  const {readFileSync}=await import('node:fs')
  const {runInNewContext}=await import('node:vm')
  const source=readFileSync(new URL('../src/logout.js',import.meta.url),'utf8')
  const redirects=[];let channel
  runInNewContext(source.replace(/export /g,'')+'; installSignOut();',{
    window:{addEventListener(){},location:{replace:url=>redirects.push(url)}},document:{addEventListener(){}},
    BroadcastChannel:class {constructor(){channel=this}}
  })
  channel.onmessage({data:'signed-out'})
  assert.deepEqual(redirects,['/login?redirect-to=/campus'])
})
