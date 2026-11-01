import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
const code=readFileSync(new URL('../../institute_lms/public/firebase-messaging-sw.js',import.meta.url),'utf8')
function setup(project='sisu-lms'){
  const events={},imports=[],opened=[];let initialized,messaging=0
  const origin='https://sandbox.example'
  const context={URL,JSON,Error,self:{location:{href:origin+'/assets/institute_lms/firebase-messaging-sw.js?config='+encodeURIComponent(JSON.stringify({projectId:project})),origin},addEventListener:(name,fn)=>events[name]=fn},clients:{openWindow:url=>{opened.push(url);return Promise.resolve()}},importScripts:(...urls)=>imports.push(...urls),firebase:{initializeApp:value=>initialized=value,messaging:()=>messaging++}}
  vm.runInNewContext(code,context)
  return {events,imports,opened,initialized,messaging}
}
test('worker initializes intended project using pinned official SDK only',()=>{
  const state=setup();assert.equal(state.initialized.projectId,'sisu-lms');assert.equal(state.messaging,1)
  assert.deepEqual(state.imports,['https://www.gstatic.com/firebasejs/13.0.0/firebase-app-compat.js','https://www.gstatic.com/firebasejs/13.0.0/firebase-messaging-compat.js'])
})
test('worker rejects another Firebase project',()=>assert.throws(()=>setup('other'),/Unexpected/))
test('notification clicks always navigate to own campus, never payload links',async()=>{
  const state=setup();let stopped=false,closed=false,wait
  state.events.notificationclick({notification:{data:{url:'https://evil.example'},close:()=>closed=true},stopImmediatePropagation:()=>stopped=true,waitUntil:p=>wait=p})
  await wait;assert.equal(stopped,true);assert.equal(closed,true);assert.deepEqual(state.opened,['https://sandbox.example/campus'])
})
