import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'

const source=readFileSync(new URL('../src/materials/MaterialViewer.vue',import.meta.url),'utf8')
function viewer(material,blob=new Blob(['lesson'])){
  const revoked=[]
  const context=vm.createContext({
    defineProps:()=>({material,member:{role:'Student'}}),
    ref:value=>({value}),computed:fn=>({get value(){return fn()}}),
    onBeforeUnmount(){},nextTick:async()=>{},materialBlob:async()=>blob,
    URL:{createObjectURL:()=> 'blob:preview',revokeObjectURL:url=>revoked.push(url)},
  })
  const script=source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')
  vm.runInContext(script+'\nglobalThis.viewer={view,close,isImage,isText,hasPreview,canDownload,imageUrl,textPreview,error};',context)
  return {...context.viewer,revoked}
}

test('ordinary main image previews retain view-only policy and release blob URLs',async()=>{
  for(const file_type of ['png','jpg','jpeg']){
    const v=viewer({name:'material',file_type,download_policy:'View only'})
    assert.equal(v.hasPreview.value,true)
    assert.equal(v.canDownload.value,false)
    await v.view()
    assert.equal(v.imageUrl.value,'blob:preview')
    assert.equal(v.error.value,'')
    v.close()
    assert.deepEqual(v.revoked,['blob:preview'])
  }
})

test('paper text and WebP preview additions do not broaden ordinary document previews',async()=>{
  for(const file_type of ['txt','webp']){
    assert.equal(viewer({name:'ordinary',file_type}).hasPreview.value,false)
    const v=viewer({name:'paper-upload-1',file_type,download_policy:'Downloadable'})
    assert.equal(v.hasPreview.value,true)
    assert.equal(v.canDownload.value,true)
    await v.view()
    assert.equal(file_type==='txt'?v.textPreview.value:v.imageUrl.value,file_type==='txt'?'lesson':'blob:preview')
    v.close()
    assert.equal(v.textPreview.value,'')
  }
  assert.equal(viewer({name:'ordinary',file_type:'xlsx',preview_file_id:'pdf'}).hasPreview.value,true)
})

test('closing a text preview during decoding cannot restore stale text',async()=>{
  let finish
  let started
  const decoding=new Promise(resolve=>{started=resolve})
  const v=viewer({name:'paper-upload-1',file_type:'txt'},{text:()=>new Promise(resolve=>{finish=resolve;started()})})
  const pending=v.view()
  await decoding
  v.close()
  finish('stale')
  await pending
  assert.equal(v.textPreview.value,'')
})
