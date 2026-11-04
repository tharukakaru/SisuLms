import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('../src/App.vue',import.meta.url),'utf8')
function harness(){
 const pending=[]
 const context={form:{value:{}},imageUploads:{value:{}},error:{value:''},uploadImage:file=>new Promise((resolve,reject)=>pending.push({file,resolve,reject}))}
 vm.createContext(context)
 const start=source.indexOf('async function upload(event,field)')
 const end=source.indexOf('async function sendComment',start)
 vm.runInContext(source.slice(start,end),context)
 return {context,pending}
}
const input=name=>({target:{files:[{name}],value:name}})
test('both classroom images upload even while first is pending',async()=>{
 const {context:c,pending}=harness()
 const first=c.upload(input('profile.png'),'profile_image')
 const second=c.upload(input('cover.png'),'cover_image')
 assert.equal(pending.length,2)
 pending[1].resolve('/files/cover.webp');await second
 assert.equal(c.imageUploads.value.profile_image.pending,true)
 pending[0].resolve('/files/profile.webp');await first
 assert.equal(c.form.value.profile_image,'/files/profile.webp')
 assert.equal(c.form.value.cover_image,'/files/cover.webp')
 assert.equal(c.imageUploads.value.cover_image.name,'cover.png')
})
test('failed upload retains filename and error without replacing saved image',async()=>{
 const {context:c,pending}=harness();c.form.value.cover_image='/files/old.webp'
 const job=c.upload(input('new.png'),'cover_image')
 pending[0].reject(Error('Storage unavailable'));await job
 assert.equal(c.imageUploads.value.cover_image.error,'Storage unavailable')
 assert.equal(c.imageUploads.value.cover_image.name,'new.png')
 assert.equal(c.form.value.cover_image,'/files/old.webp')
 assert.ok(source.includes('Object.values(imageUploads.value).some(x=>x.error)'))
})
test('upload finishing after switching editor does not change the new classroom',async()=>{
 const {context:c,pending}=harness()
 const job=c.upload(input('old.png'),'cover_image');c.form.value={title:'Other class'}
 pending[0].resolve('/files/old.webp');await job
 assert.equal(c.form.value.cover_image,undefined)
})
