// Exercise the real portal and teacher gate with an in-memory Vue renderer.
// Authentication responses are fixtures; no live account or backend is used.
import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile,writeFile,unlink} from 'node:fs/promises'
import {parse,compileScript,compileTemplate} from '@vue/compiler-sfc'
import {createRenderer,nextTick} from 'vue'

const renderer=createRenderer({
  querySelector:()=>globalThis.__inviteBody,
  createElement:tag=>({tag,children:[],props:{},style:{},focus(){},showModal(){this.open=true},close(){this.open=false},addEventListener(){},removeEventListener(){}}),
  createText:text=>({text}),createComment:text=>({text}),setText:(n,t)=>n.text=t,
  setElementText:(n,t)=>{n.text=t;n.children=[]},patchProp:(n,k,old,v)=>n.props[k]=v,
  insert:(n,p,anchor)=>{n.parent=p;const i=p.children.indexOf(anchor);if(i<0)p.children.push(n);else p.children.splice(i,0,n)},
  remove:n=>{const i=n.parent?.children.indexOf(n);if(i>=0)n.parent.children.splice(i,1)},
  parentNode:n=>n.parent,nextSibling:n=>n.parent?.children[n.parent.children.indexOf(n)+1],
})
const flush=async()=>{await new Promise(resolve=>setImmediate(resolve));await nextTick()}
const nodes=root=>[root,...(root.children||[]).flatMap(nodes)]
const marker=(root,name)=>nodes(root).find(n=>n.tag===name)
const button=(root,label)=>nodes(root).find(n=>n.tag==='button'&&nodes(n).some(child=>child.text?.trim()===label))


async function component(name){
 const file=new URL(`../src/native/${name}.vue`,import.meta.url)
 const {descriptor}=parse(await readFile(file,'utf8'))
 const script=compileScript(descriptor,{id:name})
 const template=compileTemplate({source:descriptor.template.content,filename:file.pathname,id:name,compilerOptions:{bindingMetadata:script.bindings}})
 const code=script.content.replace('export default','const component =').replace("import {request} from './client'",'const request=(...args)=>globalThis.__workspaceRequest(...args)')
 const output=new URL(`../src/native/.${name}-test.mjs`,import.meta.url)
 await writeFile(output,code+'\n'+template.code.replace('export function render','function render')+'\ncomponent.render=render;export default component;')
 try{return (await import(output.href)).default}finally{await unlink(output)}
}

test('invitations prompt once, keep errors open, accept/reject explicitly and switch connected workspace',async()=>{
 globalThis.__inviteBody={children:[]}
 globalThis.document={body:{style:{overflow:''}},visibilityState:'visible',addEventListener(){},removeEventListener(){},activeElement:{focus(){}}}
 globalThis.window={dispatchEvent(){}}
 const calls=[],destinations=[];let fail=false
 const row={name:'inv-1',institute:'I',institute_title:'Test Institute',status:'Pending',expired:false,creation:'2026-11-16 10:00:00',expires_at:'2026-11-23 10:00:00'}
 globalThis.location={assign:path=>destinations.push(path)}
 globalThis.__workspaceRequest=async(...args)=>{calls.push(args);if(args[1]==='list_invitations')return [{...row}];if(fail)throw Error('This invitation expired');if(args[1]==='respond'){row.status=args[2].decision;row.connected=row.status==='Accepted';row.responded_at='2026-11-16 11:00:00'};return {}}
 const Component=await component('TeacherInvitations')
 const app=renderer.createApp(Component,{active:true,member:{role:'Teacher'}})
 try{
  const vm=app.mount({children:[]});await new Promise(resolve=>setImmediate(resolve));await nextTick()
  assert.equal(vm.$.setupState.selected.name,'inv-1','Normal entry prompts pending invitation')
  assert.equal(document.body.style.overflow,'hidden')
  vm.$.setupState.close();await vm.$.setupState.load(true)
  assert.equal(vm.$.setupState.selected,null,'Dismissal does not repeatedly prompt')
  assert.equal(calls.filter(c=>c[1]==='respond').length,0,'Dismiss is not a rejection')
  await vm.$.setupState.review(row);fail=true;await vm.$.setupState.respond('Accepted')
  assert.equal(vm.$.setupState.error,'This invitation expired');assert.ok(vm.$.setupState.selected,'Failure stays in dialog')
  fail=false;await vm.$.setupState.respond('Accepted')
  assert.equal(vm.$.setupState.selected,null);assert.equal(vm.$.setupState.rows[0].connected,true)
  assert.equal(document.body.style.overflow,'')
  await vm.$.setupState.open(row);assert.deepEqual(destinations,['/campus'])
  assert.deepEqual(calls.at(-1),['campus_context','select',{institute:'I'}])
  vm.$.setupState.busy='';row.name='inv-2';row.status='Pending';row.connected=false
  await vm.$.setupState.review(row);await vm.$.setupState.respond('Declined')
  assert.equal(row.status,'Declined');assert.equal(vm.$.setupState.label(row),'Rejected')
  row.status='Accepted';row.expired=false;row.connected=true
  assert.equal(vm.$.setupState.label(row),'Connected','Accepted invitations do not expire out of history')
 }finally{app.unmount()}
})
