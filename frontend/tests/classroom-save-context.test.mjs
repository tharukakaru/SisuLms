import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'

// Exercise the actual modal handlers with network/rendering replaced by a small harness.
const source=fs.readFileSync(new URL('../src/App.vue',import.meta.url),'utf8')
const handlers=source.slice(source.indexOf('function edit('),source.indexOf('const imageUploads='))
const close=source.slice(source.indexOf('function closeDialog('),source.indexOf('function trapFocus('))
function harness(){
 const ref=value=>({value}),room={name:'room-a',title:'Assigned class'}
 const context={room,modal:ref('room'),selected:ref({room}),detailTab:ref('Overview'),roomReturn:ref(null),
  internalCreation:ref(false),rooms:ref([room]),form:ref({}),teacherOptions:ref([]),manager:ref(true),admin:ref(false),
  boot:ref({member:{name:'teacher',full_name:'Test Teacher'},institute:{}}),members:ref([]),imageUploads:ref({}),
  uploadingImages:ref(false),classroomBank:ref({}),busy:ref(false),error:ref(''),enrollments:ref([]),
  welcomeSession:ref(null),activeVideo:ref(''),lastFocus:null,dayKey:()=> '2026-11-06',sessionStream:x=>x,
  graphemes:x=>x.length,loadClassroomBank:()=>{},refreshCount:0,notice:'',call:async()=>[],
  openDialog:type=>{context.modal.value=type},refresh:async()=>{context.refreshCount++},notify:msg=>{context.notice=msg}}
 vm.createContext(context);vm.runInContext(close+'\n'+handlers,context)
 return context
}
for(const [action,tab] of [['announcement','Overview'],['session','Sessions'],['material','Materials']]){
 test(`${action} save keeps the classroom open on ${tab}`,async()=>{
  const c=harness();c.edit(action,c.room)
  if(action==='material')c.form.value.file_id='private-file'
  await c.submit()
  assert.equal(c.error.value,'');assert.equal(c.modal.value,'room');assert.equal(c.selected.value.room.name,'room-a')
  assert.equal(c.detailTab.value,tab);assert.equal(c.refreshCount,1)
 })
}
test('cancel nested action returns to the previous classroom tab',()=>{
 const c=harness();c.detailTab.value='Materials';c.edit('announcement',c.room);c.closeDialog()
 assert.equal(c.modal.value,'room');assert.equal(c.detailTab.value,'Materials')
})
test('failed save retains entered form and does not refresh away',async()=>{
 const c=harness();c.edit('announcement',c.room);c.form.value.body='Keep this draft'
 c.call=async()=>{throw Error('Save failed')};await c.submit()
 assert.equal(c.modal.value,'announcement');assert.equal(c.form.value.body,'Keep this draft');assert.equal(c.refreshCount,0)
})
test('scheduling outside a classroom keeps the existing page behavior',async()=>{
 const c=harness();c.modal.value=null;c.edit('session',c.room);await c.submit()
 assert.equal(c.modal.value,null);assert.equal(c.refreshCount,1)
})
