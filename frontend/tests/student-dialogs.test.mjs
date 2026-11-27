import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'

const dialog=fs.readFileSync(new URL('../src/shared/StudentDialog.vue',import.meta.url),'utf8')
function dialogHarness(){
 const events=[],calls=[],props={busy:false},previous={isConnected:true,focus:()=>calls.push('restore')}
 const ctx={ref:value=>({value}),defineProps:()=>props,defineEmits:()=>event=>events.push(event),document:{activeElement:previous},nextTick:async()=>{},onMounted:fn=>ctx.mount=fn,onBeforeUnmount:fn=>ctx.unmount=fn}
 vm.createContext(ctx)
 vm.runInContext(dialog.split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm,'')+'\nglobalThis.dialogRef=dialog',ctx)
 ctx.dialogRef.value={showModal:()=>calls.push('open'),close:()=>calls.push('close')}
 return {ctx,events,calls,props,previous}
}
test('student popup opens in the native modal layer and restores focus on dismissal',async()=>{
 const h=dialogHarness();await h.ctx.mount();h.ctx.close();h.ctx.unmount()
 assert.deepEqual(h.calls,['open','close','restore']);assert.deepEqual(h.events,['close'])
})
test('busy student popup blocks dismissal and does not focus a removed trigger',async()=>{
 const h=dialogHarness();await h.ctx.mount();h.props.busy=true;h.ctx.close();assert.equal(h.events.length,0)
 h.previous.isConnected=false;h.ctx.unmount();assert.deepEqual(h.calls,['open','close'])
})

const classrooms=fs.readFileSync(new URL('../src/native/StudentClassrooms.vue',import.meta.url),'utf8')
function enrollmentHarness(){
 const pending=[],ctx={ref:value=>({value}),keyRoom:{value:null},enrollmentKey:{value:''},error:{value:''},request:()=>new Promise((resolve,reject)=>pending.push({resolve,reject}))}
 vm.createContext(ctx)
 vm.runInContext(classrooms.slice(classrooms.indexOf('const approved='),classrooms.indexOf('\nasync function resendKey'))+'\nglobalThis.state={approved,checkingKey}',ctx)
 return {ctx,pending}
}
test('enrollment popup ignores approval from an older classroom request',async()=>{
 const {ctx,pending}=enrollmentHarness();const first=ctx.openEnrollment({name:'a'}),second=ctx.openEnrollment({name:'b'})
 pending[1].resolve({payment_approved:false});await second;pending[0].resolve({payment_approved:true});await first
 assert.equal(ctx.state.approved.value,false);assert.equal(ctx.keyRoom.value.name,'b');assert.equal(ctx.state.checkingKey.value,false)
})
test('closing enrollment while checking ignores late errors and clears the key',async()=>{
 const {ctx,pending}=enrollmentHarness();const work=ctx.openEnrollment({name:'a'});ctx.enrollmentKey.value='private-key';ctx.closeEnrollment();pending[0].reject(new Error('Old request'));await work
 assert.equal(ctx.error.value,'');assert.equal(ctx.keyRoom.value,null);assert.equal(ctx.enrollmentKey.value,'');assert.equal(ctx.state.checkingKey.value,false)
})
test('current enrollment errors are shown and a fresh check can recover',async()=>{
 const {ctx,pending}=enrollmentHarness();let work=ctx.openEnrollment({name:'a'});pending[0].reject(new Error('Connection lost'));await work
 assert.equal(ctx.error.value,'Connection lost');assert.equal(ctx.state.checkingKey.value,false)
 work=ctx.openEnrollment({name:'a'});pending[1].resolve({payment_approved:true});await work
 assert.equal(ctx.error.value,'');assert.equal(ctx.state.approved.value,true)
})
