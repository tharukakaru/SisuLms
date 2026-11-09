import test from 'node:test'
import assert from 'node:assert/strict'
import {paymentMessage,libraryMetadata,loadCheckoutLibrary} from '../src/native/cybersourceCheckout.js'
test('only server success is presented as verified',()=>{
 assert.match(paymentMessage({status:'pending',browser_event:'completed'}),/pending/)
 assert.match(paymentMessage({status:'succeeded'}),/verified/)
 assert.match(paymentMessage({status:'pending',browser_event:'cancelled'}),/verify/)
 assert.match(paymentMessage({status:'review'}),/review/)
})
const libraryURL='https://testup.cybersource.com/uc/v1/assets/test-version/UnifiedCheckout.js'
const token=(url=libraryURL, integrity='sha384-YWJjZA==')=>'header.'+Buffer.from(JSON.stringify({ctx:[{data:{clientLibrary:url,clientLibraryIntegrity:integrity}}]})).toString('base64url')+'.signature'
test('rejects untrusted executable URLs and missing integrity',()=>{
 for(const url of ['https://evil.test/UnifiedCheckout.js','https://testup.cybersource.com.evil.test/uc/v1/assets/a/UnifiedCheckout.js',libraryURL+'?evil=1'])assert.throws(()=>libraryMetadata(token(url)))
 assert.throws(()=>libraryMetadata(token(libraryURL,'')))
})
test('checkout uses session library with SRI and retries a failed load',async()=>{
 let added
 globalThis.window={}
 globalThis.document={createElement:()=>({remove(){}}),head:{appendChild(s){added=s}}}
 const failed=loadCheckoutLibrary(token())
 assert.equal(added.src,libraryURL);assert.match(libraryURL,/testup\.cybersource\.com/)
 assert.equal(added.integrity,'sha384-YWJjZA==');assert.equal(added.crossOrigin,'anonymous');added.onerror();await assert.rejects(failed,/Unable to load/)
 const retry=loadCheckoutLibrary(token());window.VAS={UnifiedCheckout:()=>{}}
 added.onload();assert.equal(await retry,window.VAS)
 delete globalThis.window;delete globalThis.document
})
