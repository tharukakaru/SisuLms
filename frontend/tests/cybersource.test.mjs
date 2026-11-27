import test from 'node:test'
import assert from 'node:assert/strict'
import {paymentMessage,libraryMetadata,loadCheckoutLibrary,reusableCheckout} from '../src/native/cybersourceCheckout.js'
test('only server success is presented as verified',()=>{
 assert.match(paymentMessage({status:'pending',browser_event:'completed'}),/pending/)
 assert.match(paymentMessage({status:'succeeded'}),/verified/)
 assert.match(paymentMessage({status:'pending',browser_event:'cancelled'}),/not been confirmed/)
 assert.match(paymentMessage({status:'review'}),/review/)
 assert.match(paymentMessage({status:'failed',session_rejected:true}),/No payment session was created/)
 assert.doesNotMatch(paymentMessage({status:'failed',session_rejected:true}),/declined/)
})

test('verified acquirer rejection shows the server explanation instead of pending',()=>{
 const message='Payment was rejected by the acquiring bank or processor (code 491). Your paid plan was not activated.'
 assert.equal(paymentMessage({status:'failed',message}),message)
 assert.doesNotMatch(paymentMessage({status:'failed'}),/pending|invoice remains unpaid/)
})

test('lost checkout copy distinguishes unfinished checkout from payment processing',()=>{
 const waiting=paymentMessage({status:'pending',retry_after:Date.now()/1000+600})
 assert.match(waiting,/original window/)
 assert.doesNotMatch(waiting,/verification pending|five minutes/)
 assert.match(paymentMessage({status:'pending',retry_after:1}),/Check and reopen/)
 assert.match(paymentMessage({status:'pending',retry_after:100},undefined,99999),/reserved/)
 assert.match(paymentMessage({status:'pending',retry_after:100},undefined,100000),/Check and reopen/)
 assert.match(paymentMessage({status:'cancelled',retry_allowed:true}),/without a recorded payment/)
})

test('closing and reopening reuses the checkout and ignores a detached result',async()=>{
 let resolve, mounts=0, unmounts=0, destroyed=0
 const sdk={mount:()=>{mounts++;return new Promise(r=>resolve=r)},unmount:()=>unmounts++,destroy:()=>destroyed++}
 const checkout=reusableCheckout({destroy:()=>destroyed++},sdk,100,()=>0)
 const first=checkout.mount('#target');checkout.pause();resolve('late-result')
 assert.deepEqual(await first,{detached:true})
 assert.equal(checkout.canResume(),true)
 const second=checkout.mount('#target');resolve('completed')
 assert.deepEqual(await second,{result:'completed'})
 assert.equal(checkout.canResume(),false)
 await assert.rejects(checkout.mount('#target'))
 assert.equal(mounts,2);assert.equal(unmounts,1);assert.equal(destroyed,0)
 checkout.destroy();assert.equal(destroyed,2)
})

test('an expired retained checkout must go through server recovery',async()=>{
 let now=0, mounted=0
 const checkout=reusableCheckout({destroy(){}},{mount(){mounted++},unmount(){},destroy(){}},100,()=>now)
 assert.equal(checkout.canResume(),true);now=100000
 assert.equal(checkout.canResume(),false)
 await assert.rejects(checkout.mount('#target'),/expired/)
 assert.equal(mounted,0)
})

test('collecting details does not process a payment and submission cannot resume',async()=>{
 let payments=0
 const checkout=reusableCheckout({destroy(){}},{
   mount:async()=> 'transient-token', unmount(){},destroy(){},
   complete:async token=>{assert.equal(token,'transient-token');payments++;return 'result'}
 },100,()=>0)
 const collected=await checkout.mount('#target')
 assert.equal(payments,0)
 assert.equal(checkout.canResume(),false)
 assert.equal(await checkout.complete(collected.result),'result')
 assert.equal(payments,1)
})
const libraryURL='https://testup.cybersource.com/uc/v1/assets/test-version/UnifiedCheckout.js'
const token=(url=libraryURL, integrity='sha384-YWJjZA==')=>'header.'+Buffer.from(JSON.stringify({ctx:[{data:{clientLibrary:url,clientLibraryIntegrity:integrity}}]})).toString('base64url')+'.signature'
test('rejects untrusted executable URLs and missing integrity',()=>{
 for(const url of ['https://evil.test/UnifiedCheckout.js','https://testup.cybersource.com.evil.test/uc/v1/assets/a/UnifiedCheckout.js',libraryURL+'?evil=1'])assert.throws(()=>libraryMetadata(token(url)))
 assert.throws(()=>libraryMetadata(token(libraryURL,'')))
})

test('accepts the signed live checkout asset host without accepting lookalikes or sandbox crossover',()=>{
 const live='https://up.cybersource.com/uc/v1/assets/test-version/UnifiedCheckout.js'
 assert.equal(libraryMetadata(token(live),'live').url,live)
 assert.throws(()=>libraryMetadata(token(live),'sandbox'))
 assert.throws(()=>libraryMetadata(token(libraryURL),'live'))
 for(const url of [live.replace('up.cybersource.com','up.cybersource.com.evil.test'),live+'?x=1',live.replace('https:','http:')])assert.throws(()=>libraryMetadata(token(url),'live'))
})
test('checkout uses session library with SRI and retries a failed load',async()=>{
 let added
 globalThis.window={}
 globalThis.document={createElement:()=>({remove(){}}),head:{appendChild(s){added=s}}}
 const failed=loadCheckoutLibrary(token())
 assert.equal(added.src,libraryURL);assert.match(libraryURL,/testup\.cybersource\.com/)
 assert.equal(added.integrity,'sha384-YWJjZA==');assert.equal(added.crossOrigin,'anonymous');added.onerror();await assert.rejects(failed,/Unable to load/)
 const stalled=loadCheckoutLibrary(token(),'sandbox',5)
 await assert.rejects(stalled,/taking longer/)
 assert.equal(added.onload,null);assert.equal(added.onerror,null)
 const retry=loadCheckoutLibrary(token());window.VAS={UnifiedCheckout:()=>{}}
 assert.equal(loadCheckoutLibrary(token()),retry)
 added.onload();assert.equal(await retry,window.VAS)
 // A fresh signed context uses another URL for the identical SDK bytes.
 const previous=added
 const renewed=token(libraryURL.replace('/assets/', '/assets/new-'))
 assert.equal(await loadCheckoutLibrary(renewed),window.VAS)
 assert.equal(added,previous)
 const changed=JSON.parse(atob(token().split('.')[1]))
 changed.ctx[0].data.clientLibraryIntegrity='sha384-ZGlmZmVyZW50'
 const changedToken='header.'+btoa(JSON.stringify(changed))+'.signature'
 assert.throws(()=>loadCheckoutLibrary(changedToken),{code:'CHECKOUT_RELOAD_REQUIRED'})
 assert.equal(added,previous)
 // Even with identical integrity, an untrusted URL is never accepted.
 assert.throws(()=>loadCheckoutLibrary(token('https://evil.test/uc/v1/assets/new/UnifiedCheckout.js')))

 delete globalThis.window;delete globalThis.document
})
