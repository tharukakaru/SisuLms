import test from 'node:test'
import assert from 'node:assert/strict'
import {paymentMessage,libraryURL,loadCheckoutLibrary} from '../src/native/cybersourceCheckout.js'
test('only server success is presented as verified',()=>{
 assert.match(paymentMessage({status:'pending',browser_event:'completed'}),/pending/)
 assert.match(paymentMessage({status:'succeeded'}),/verified/)
 assert.match(paymentMessage({status:'pending',browser_event:'cancelled'}),/verify/)
 assert.match(paymentMessage({status:'review'}),/review/)
})
test('checkout loads only the fixed sandbox library and retries a failed load',async()=>{
 let added
 globalThis.window={}
 globalThis.document={createElement:()=>({remove(){}}),head:{appendChild(s){added=s}}}
 const failed=loadCheckoutLibrary()
 assert.equal(added.src,libraryURL);assert.match(libraryURL,/apitest\.cybersource\.com/)
 added.onerror();await assert.rejects(failed,/Unable to load/)
 const retry=loadCheckoutLibrary();window.VAS={UnifiedCheckout:()=>{}}
 added.onload();assert.equal(await retry,window.VAS)
 delete globalThis.window;delete globalThis.document
})
