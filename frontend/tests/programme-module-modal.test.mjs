import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'

const source=readFileSync(new URL('../src/native/Programmes.vue',import.meta.url),'utf8')
function harness(){
  let cleanup
  const listeners=new Map(),events=[]
  const document={body:{style:{overflow:'auto'}},documentElement:{style:{overflow:''}},
    addEventListener:(key,fn)=>listeners.set(key,fn),removeEventListener:key=>listeners.delete(key)}
  const control=()=>({isConnected:true,disabled:false,tabIndex:0,getClientRects:()=>[{}],focus(){document.activeElement=this}})
  const trigger=control(),close=control(),last=control();document.activeElement=trigger
  const context=vm.createContext({document,ref:value=>({value}),nextTick:async()=>{},onMounted(){},
    onBeforeUnmount(fn){cleanup=fn},defineProps:()=>({member:{role:'Student'},rooms:[{name:'room-a'}]}),
    defineEmits:()=>((...args)=>events.push(args)),request:async()=>[]})
  const script=source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')
  // Run the component's actual event handlers against a minimal DOM double.
  vm.runInContext(script+'\nglobalThis.modal={openModules,closeModules,openModule,dialogKeys,selected,moduleDialog,closeButton};',context)
  const modal=context.modal
  modal.closeButton.value=close
  modal.moduleDialog.value={contains:el=>[close,last].includes(el),querySelectorAll:()=>[close,last],focus(){}}
  return {modal,document,trigger,close,last,listeners,events,unmount:()=>cleanup()}
}
test('opening different programmes selects the correct modules and restores scrolling/focus',async()=>{
  const h=harness(),a={name:'a',modules:[{classroom:'room-a'}]},b={name:'b',modules:[]}
  await h.modal.openModules(a,{currentTarget:h.trigger})
  assert.equal(h.modal.selected.value,a)
  assert.equal(h.document.activeElement,h.close)
  assert.equal(h.document.body.style.overflow,'hidden')
  await h.modal.openModules(b)
  assert.equal(h.modal.selected.value,b)
  h.modal.closeModules()
  assert.equal(h.document.body.style.overflow,'auto')
  assert.equal(h.document.documentElement.style.overflow,'')
  assert.equal(h.document.activeElement,h.trigger)
  assert.equal(h.listeners.size,0)
})
test('keyboard cycles focus and Escape closes the dialog',async()=>{
  const h=harness();await h.modal.openModules({name:'a'})
  let prevented=0
  const event={key:'Tab',shiftKey:true,preventDefault(){prevented++}}
  h.modal.dialogKeys(event);assert.equal(h.document.activeElement,h.last)
  h.modal.dialogKeys({...event,shiftKey:false});assert.equal(h.document.activeElement,h.close)
  h.modal.dialogKeys({key:'Escape',preventDefault(){prevented++},stopPropagation(){}})
  assert.equal(h.modal.selected.value,null);assert.equal(prevented,3)
})
test('classroom navigation closes the popup and retains the existing room event',async()=>{
  const h=harness();await h.modal.openModules({name:'a'})
  h.modal.openModule({classroom:'room-a'})
  assert.equal(h.modal.selected.value,null)
  assert.equal(h.events[0][0],'room');assert.equal(h.events[0][1].name,'room-a')
  assert.equal(h.document.body.style.overflow,'auto')
})
test('module markup lives in the shared modal shell and card label never toggles',()=>{
  assert.doesNotMatch(source,/Hide modules/)
  assert.match(source,/<Teleport to="body"><div v-if="selected" class="modal-backdrop/)
  assert.match(source,/role="dialog" aria-modal="true" aria-labelledby="programme-module-title"/)
  assert.match(source,/v-for="\(m,i\) in selected.modules"/)
  assert.match(source,/max-height:calc\(100dvh - 20px\)/)
})
test('unmount releases scroll lock and event listeners',async()=>{
  const h=harness();await h.modal.openModules({name:'a'})
  h.unmount()
  assert.equal(h.document.body.style.overflow,'auto')
  assert.equal(h.listeners.size,0)
})
