// Exercise the real portal and teacher gate with an in-memory Vue renderer.
// Authentication responses are fixtures; no live account or backend is used.
import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile,writeFile,unlink} from 'node:fs/promises'
import {parse,compileScript,compileTemplate} from '@vue/compiler-sfc'
import {createRenderer,nextTick} from 'vue'

const renderer=createRenderer({
  createElement:tag=>({tag,children:[],props:{},style:{},focus(){},addEventListener(){},removeEventListener(){}}),
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

test('workspace dropdown keeps pending membership locked, switches accepted context and reports failures',async()=>{
 const previous={location:globalThis.location,document:globalThis.document,window:globalThis.window,__workspaceRequest:globalThis.__workspaceRequest}
 globalThis.document={body:{style:{overflow:''}},addEventListener(){},removeEventListener(){}}
 globalThis.window={dispatchEvent(){}}
 const calls=[],destinations=[];let fail=false,app
 globalThis.location={assign:path=>destinations.push(path)}
 globalThis.__workspaceRequest=async(...args)=>{calls.push(args);if(fail)throw Error('Membership was removed')}
 try{
  const Switch=await component('TeacherWorkspaceSwitcher')
  const personal={institute:'personal',title:'Personal',kind:'Personal',status:'Active',locked:false}
  const pending={institute:'pending',title:'Pending School',kind:'Institute',status:'Pending',locked:true,request:'request-1'}
  const active={institute:'school',title:'Accepted School',kind:'Institute',status:'Active',locked:false}
  const root={children:[]};app=renderer.createApp(Switch,{data:{selected:'personal',choices:[personal,pending,active]},locked:true})
  const vm=app.mount(root)
  assert.ok(nodes(root).some(n=>n.tag==='summary'&&n.props['aria-label']==='Switch workspace: Personal'))
  assert.equal(button(root,'Pending School').props.disabled,false,'Pending tile can reveal request controls without opening the institute')
  assert.equal(button(root,'Join institute').props.disabled,true)
  assert.equal(button(root,'Accepted School').props.disabled,false,'Approved workspaces remain reachable during personal expiry')
  await vm.$.setupState.open(pending);await vm.$.setupState.open(personal)
  assert.equal(calls.length,0)
  assert.ok(nodes(root).some(n=>n.text==='Current workspace'))
  assert.equal(nodes(root).find(n=>n.props?.['aria-label']==='Cancel request to Pending School'),undefined)
  button(root,'Pending School').props.onClick();await nextTick()
  assert.equal(calls.length,0,'Revealing the bin cannot select a pending workspace')
  const bin=nodes(root).find(n=>n.props?.['aria-label']==='Cancel request to Pending School')
  assert.ok(bin)
  bin.props.onClick();await nextTick()
  assert.ok(button(root,'Cancel request'))
  assert.ok(nodes(root).find(n=>n.tag==='dialog'))
  assert.equal(globalThis.document.body.style.overflow,'hidden')
  button(root,'Keep request').props.onClick();await nextTick()
  assert.equal(calls.length,0,'Keep request does not cancel')
  assert.equal(globalThis.document.body.style.overflow,'')
  fail=true;await vm.$.setupState.cancel(pending);await nextTick()
  assert.equal(nodes(root).find(n=>n.props?.role==='alert').text,'Membership was removed')
  fail=false;await vm.$.setupState.cancel(pending)
  assert.deepEqual(calls.at(-1),['teacher_workspace','cancel_request',{request:'request-1'}])
  await nextTick()
  assert.ok(nodes(root).some(n=>n.tag==='h2'&&n.text==='Request cancelled'))
  assert.ok(nodes(root).some(n=>n.tag==='p'&&n.text==='Request to Pending School cancelled. You can apply again whenever you’re ready.'))
  assert.ok(nodes(root).some(n=>n.tag==='dialog'&&n.props['aria-labelledby']==='request-notice-title'))
  assert.equal(globalThis.document.body.style.overflow,'hidden','The result popup keeps background scrolling locked')
  const callsBeforeDismiss=calls.length
  button(root,'OK').props.onClick();await nextTick()
  assert.equal(vm.$.setupState.notice,'')
  assert.equal(globalThis.document.body.style.overflow,'')
  assert.equal(calls.length,callsBeforeDismiss,'Dismissing the result never submits another cancellation')

  fail=true;await vm.$.setupState.open(active);await nextTick()
  assert.equal(nodes(root).find(n=>n.props?.role==='alert').text,'Membership was removed')
  assert.equal(destinations.length,0)
  fail=false;await vm.$.setupState.open(active)
  assert.deepEqual(calls.at(-1),['campus_context','select',{institute:'school'}])
  assert.deepEqual(destinations,['/campus'])
 }finally{app?.unmount();Object.assign(globalThis,previous)}
})

test('header reflects the selected workspace plan and urgent trial time',async()=>{
 const previous={document:globalThis.document};globalThis.document={addEventListener(){},removeEventListener(){}};let app
 try{
  const Header=await component('TeacherTrialCountdown')
  for(const [context,expected,urgent] of [
   [{kind:'Personal',state:'Trial',available:true,remaining_ms:3600000},'Trial ends soon',true],
   [{kind:'Personal',state:'Active',available:true,plan:'Individual'},'SISU Individual',false],
   [{kind:'Institute',state:'Active',available:true,title:'Test Institute',plan:'Gold'},'SISU Gold',false],
   [{kind:'Institute',state:'Expired',available:false,title:'Test Institute',plan:'Silver'},'SISU Silver',true],
   [{kind:'Institute',state:'Plan required',available:false,title:'Test Institute'},'No plan selected',true],
   [{kind:'Personal',state:'Expired',available:false},'Subscription required',true]
  ]){
   const root={children:[]};app=renderer.createApp(Header,{context});app.mount(root);await nextTick()
   assert.ok(nodes(root).some(n=>n.text===expected))
   assert.equal(String(root.children[0].props.class).includes('teacher-trial--urgent'),urgent)
   app.unmount();app=null
  }
 }finally{app?.unmount();Object.assign(globalThis,previous)}
})

test('selected institute name and logo appear in the compact trigger with broken-image fallback',async()=>{
 const previous={document:globalThis.document};globalThis.document={addEventListener(){},removeEventListener(){}};let app
 try{
  const Switch=await component('TeacherWorkspaceSwitcher')
  const data={selected:'school',choices:[{institute:'school',title:'Accepted Institute',kind:'Institute',image:'/institute-logo.png',status:'Active',locked:false}]}
  const root={children:[]};app=renderer.createApp(Switch,{data});app.mount(root)
  const summary=nodes(root).find(n=>n.tag==='summary')
  assert.equal(summary.props['aria-label'],'Switch workspace: Accepted Institute')
  const image=nodes(summary).find(n=>n.tag==='img')
  assert.equal(image.props.src,'/institute-logo.png')
  image.props.onError();await nextTick()
  assert.equal(nodes(summary).some(n=>n.tag==='img'),false,'Unavailable logos fall back to an institute icon')
  assert.ok(nodes(summary).some(n=>n.tag==='svg'))
 }finally{app?.unmount();Object.assign(globalThis,previous)}
})
