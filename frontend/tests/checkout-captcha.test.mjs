import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
import {ref} from 'vue'
const source=readFileSync(new URL('../src/native/CheckoutCaptcha.vue',import.meta.url),'utf8')
function harness(width=400){
 const events=[];let options,resets=0
 const context=vm.createContext({ref,defineProps:()=>({siteKey:'public-test-key'}),defineEmits:()=>((...args)=>events.push(args)),defineExpose(){},onMounted(){},onBeforeUnmount(){},setTimeout,clearTimeout,
  window:{grecaptcha:{render(target,opts){options=opts;return 1},reset(){resets++}}}})
 vm.runInContext(source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')+'\nglobalThis.ui={mount,reset,retry,target,error,loading}',context)
 context.ui.target.value={clientWidth:width}
 return {ui:context.ui,events,get options(){return options},get resets(){return resets}}
}
test('Google verification completion, expiration and errors propagate token state',async()=>{
 const h=harness();await h.ui.mount()
 assert.equal(h.options.sitekey,'public-test-key');assert.equal(h.options.size,'normal')
 h.options.callback('test-token');assert.deepEqual(h.events.at(-1),['token','test-token'])
 h.options['expired-callback']();assert.deepEqual(h.events.at(-1),['token',''])
 h.options.callback('replacement');h.options['error-callback']()
 assert.deepEqual(h.events.at(-1),['token','']);assert.match(h.ui.error.value,/interrupted/)
 h.options.callback('recovered-token');assert.equal(h.ui.error.value,'')
 assert.deepEqual(h.events.at(-1),['token','recovered-token'])
 h.ui.retry();assert.equal(h.resets,1);assert.equal(h.ui.error.value,'')
})
test('narrow checkout renders compact verification and reset clears its token',async()=>{
 const h=harness(280);await h.ui.mount();assert.equal(h.options.size,'compact')
 h.options.callback('token');h.ui.reset();assert.equal(h.resets,1)
 assert.deepEqual(h.events.at(-1),['token','']);assert.equal(h.ui.loading.value,false)
})
