// Exercise the real portal and teacher gate with an in-memory Vue renderer.
// Authentication responses are fixtures; no live account or backend is used.
import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile,writeFile,unlink} from 'node:fs/promises'
import {parse,compileScript,compileTemplate} from '@vue/compiler-sfc'
import {createRenderer,nextTick} from 'vue'

const renderer=createRenderer({
  createElement:tag=>({tag,children:[],props:{},style:{},getRootNode(){return {}},focus(){},addEventListener(){},removeEventListener(){}}),
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
 const code=script.content.replace('export default','const component =').replace("import {request} from './client'",'const request=(...args)=>globalThis.__workspaceRequest(...args)').replace("import SocialLinks from '../commerce/SocialLinks.vue'","const SocialLinks={render(){return null}}")
 const output=new URL(`../src/native/.${name}-test.mjs`,import.meta.url)
 await writeFile(output,code+'\n'+template.code.replace('export function render','function render')+'\ncomponent.render=render;export default component;')
 try{return (await import(output.href)).default}finally{await unlink(output)}
}

test('institute profiles preserve search, reject stale responses and keep pending requests locked',async()=>{
 const previous={window:globalThis.window,Document:globalThis.Document,ShadowRoot:globalThis.ShadowRoot,document:globalThis.document,__workspaceRequest:globalThis.__workspaceRequest}
 globalThis.Document=class {};globalThis.ShadowRoot=class {}
 globalThis.window={addEventListener(){},removeEventListener(){}}
 globalThis.document={getElementById(){return {focus(){}}}}
 const schools=[{name:'a',display_name:'Alpha',username:'alpha',country:'LK'},{name:'b',display_name:'Beta',username:'beta',country:'LK',tagline:'None'}]
 const calls=[];let resolveProfile,fail=false,app
 globalThis.__workspaceRequest=async(module,method,args)=>{
  calls.push({module,method,args})
  if(method==='institute_join_options')return {institutes:schools,requests:[{profile:'b',status:'Pending'}]}
  if(method==='institute_profile'){
   if(fail)throw Error('Profile unavailable')
   return new Promise(resolve=>{resolveProfile=resolve})
  }
  throw Error('Unexpected mutation')
 }
 try{
  const Component=await component('TeacherInstitutes'),root={children:[]}
  app=renderer.createApp(Component);const vm=app.mount(root);await flush()
  const state=vm.$.setupState
  state.query='beta';await nextTick()
  assert.equal(state.rows.length,1);assert.equal(state.rows[0].tagline,'');assert.equal(state.rows[0].country,'Sri Lanka')
  const pending=state.view(schools[1]);await flush()
  assert.ok(nodes(root).some(n=>n.text==='Pending approval'))
  assert.equal(button(root,'Request to join institute'),undefined)
  assert.equal(button(root,'Open workspace'),undefined)
  await state.back()
  resolveProfile({profile:schools[1],classes:[],teachers:[],class_count:0,teacher_count:0});await pending
  assert.equal(state.selected,null);assert.equal(state.catalogue,null,'A late response must not reopen a closed preview')
  assert.equal(state.query,'beta')
  fail=true;await state.view(schools[0]);await flush()
  assert.ok(nodes(root).some(n=>n.text==='Profile unavailable'))
  assert.equal(button(root,'Request to join institute').props.disabled,true,'Cannot request a profile that failed to load')
  fail=false;const retry=state.readProfile();await flush()
  resolveProfile({profile:{...schools[0],bio:'Public introduction'},classes:[{name:'c',title:'Public class',fee_mode:'Free'}],teachers:[],class_count:1,teacher_count:0,has_more:false});await retry;await flush()
  assert.ok(nodes(root).some(n=>n.text==='Public introduction'))
  assert.ok(nodes(root).some(n=>n.text==='Public class'))
  assert.equal(button(root,'Request to join institute').props.disabled,false)
  assert.equal(calls.filter(c=>['select','request_institutes'].includes(c.method)).length,0,'Viewing profiles must not join or switch workspace')
 }finally{app?.unmount();Object.assign(globalThis,previous)}
})
