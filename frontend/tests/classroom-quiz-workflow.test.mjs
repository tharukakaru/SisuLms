// Executes the real Vue component with a small in-memory renderer and mocked HTTP.
// No browser, live backend or database is contacted.
import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile,writeFile,unlink} from 'node:fs/promises'
import {parse,compileScript,compileTemplate} from '@vue/compiler-sfc'
import {createRenderer,nextTick} from 'vue'

const renderer=createRenderer({
  createElement:tag=>({tag,tagName:tag.toUpperCase(),children:[],get options(){return this.children.filter(n=>n.tag==='option')},props:{},style:{},getRootNode(){return globalThis.document},addEventListener(){},removeEventListener(){},setAttribute(){},removeAttribute(){}}),
  createText:text=>({text}),createComment:text=>({text}),setText:(n,t)=>n.text=t,
  setElementText:(n,t)=>{n.text=t;n.children=[]},
  patchProp:(n,k,old,v)=>{n.props[k]=v;if(k==='value')n.value=v},
  insert:(n,p,anchor)=>{n.parent=p;const i=p.children.indexOf(anchor);if(i<0)p.children.push(n);else p.children.splice(i,0,n)},
  remove:n=>{const i=n.parent?.children.indexOf(n);if(i>=0)n.parent.children.splice(i,1)},
  parentNode:n=>n.parent,nextSibling:n=>n.parent?.children[n.parent.children.indexOf(n)+1],
})
const flush=async()=>{await new Promise(resolve=>setImmediate(resolve));await nextTick()}

test('teacher draft, preview, publish and student review use separate safe payloads',async()=>{
  const file=new URL('../src/native/ClassroomQuizzes.vue',import.meta.url)
  const output=new URL('../src/native/.quiz-workflow-test.mjs',import.meta.url)
  const clientOutput=new URL('../src/native/.quiz-client-test.mjs',import.meta.url)
  await writeFile(clientOutput,(await readFile(new URL('../src/native/client.js',import.meta.url),'utf8')).replace("from './contracts'","from './contracts.js'"))
  const {descriptor}=parse(await readFile(file,'utf8'))
  const script=compileScript(descriptor,{id:'quiz-test'})
  const template=compileTemplate({source:descriptor.template.content,filename:file.pathname,id:'quiz-test',compilerOptions:{bindingMetadata:script.bindings}})
  const code=script.content.replace('export default','const component =').replaceAll("from './client'","from './.quiz-client-test.mjs'").replaceAll("from './classroomQuizRules'","from './classroomQuizRules.js'").replaceAll("from '../i18n'","from '../i18n.js'")
  await writeFile(output,code+'\n'+template.code.replace('export function render','function render')+'\ncomponent.render=render; export default component;')
  const previous={Document:globalThis.Document,ShadowRoot:globalThis.ShadowRoot,fetch:globalThis.fetch,window:globalThis.window,document:globalThis.document}
  globalThis.Document=class {};globalThis.ShadowRoot=class {};globalThis.window={csrf_token:'test'};globalThis.document=Object.assign(new Document(),{activeElement:null})
  let teacher=true,schemaReady=true,metadataFail=false,calls=[],saved=null,submitCount=0
  globalThis.fetch=async(url,options)=>{
    const method=url.split('.').at(-1);const body=JSON.parse(options.body);calls.push({method,body})
    let message
    if(method==='metadata'){
      if(metadataFail)throw Error('Network unavailable')
      message={can_manage:teacher,schema_ready:schemaReady}
    }
    else if(method==='listing')message={items:[],can_manage:teacher}
    else if(method==='save'){saved=body.data;message={name:'quiz-1',status:body.publish?'Published':'Draft',modified:'new'}}
    else if(method==='detail')message={name:'quiz-1',title:'Practice',instructions:'Choose one',questions:[{prompt:'2 + 2?',options:['1','2','3','4']}],can_manage:false,result:null}
    else if(method==='submit'){submitCount++;message={score:1,total:1,percentage:100}}
    else throw Error('Unexpected request '+method)
    return {ok:true,headers:{get:()=> 'application/json'},json:async()=>({message})}
  }
  let app
  try{
    const {default:Component}=await import(output.href)
    const root={children:[]};app=renderer.createApp(Component,{classroom:'room-1'});const vm=app.mount(root);await flush()
    const state=vm.$.setupState
    state.create();await nextTick()
    state.editor.title='Practice'
    await state.save(true);assert.ok(state.errors.questions[0].prompt);assert.equal(state.editor.title,'Practice');assert.equal(calls.filter(c=>c.method==='save').length,0)
    await state.save(false);assert.equal(saved.title,'Practice');assert.equal(saved.questions[0].answer,null)
    state.editor.questions[0]={prompt:'2 + 2?',options:['1','2','3','4'],answer:3}
    const before=calls.length;await state.showPreview();await nextTick();assert.equal(calls.length,before);assert.equal(state.preview,true)
    state.preview=false;assert.equal(state.editor.questions[0].answer,3)
    await state.save(true);assert.equal(calls.findLast(c=>c.method==='save').body.publish,true);assert.equal(state.editor,null)
    app.unmount();teacher=false
    app=renderer.createApp(Component,{classroom:'room-1'});const student=app.mount({children:[]});await flush()
    const take=student.$.setupState;await take.open({name:'quiz-1'});await nextTick()
    assert.equal('answer' in take.selected.questions[0],false)
    take.reviewAnswers();assert.equal(take.review,false);assert.ok(take.error)
    take.answers[0]=3;take.reviewAnswers();assert.equal(take.review,true);assert.equal(submitCount,0)
    await Promise.all([take.submit(),take.submit()]);assert.equal(submitCount,1);assert.equal(take.result.percentage,100)
    assert.deepEqual(calls.find(c=>c.method==='submit').body,{name:'quiz-1',answers:[3]})
    app.unmount();teacher=true;schemaReady=false;calls=[]
    const readiness=[]
    app=renderer.createApp(Component,{classroom:'room-1',onReadiness:value=>readiness.push(value)})
    const setup=app.mount({children:[]});await flush()
    assert.equal(readiness.at(-1).status,'setup');assert.equal(readiness.at(-1).can_manage,true)
    assert.equal(calls.some(c=>c.method==='listing'),false)
    setup.create();assert.equal(setup.$.setupState.editor,null)
    metadataFail=true;await setup.initialize()
    assert.equal(readiness.at(-1).status,'error');assert.match(readiness.at(-1).error,/Network unavailable/)
    metadataFail=false;schemaReady=true;await setup.initialize()
    assert.equal(readiness.at(-1).status,'ready')
    assert.equal(setup.$.setupState.rows.length,0)
    setup.create();assert.ok(setup.$.setupState.editor)
  }finally{app?.unmount();Object.assign(globalThis,previous);await unlink(output);await unlink(clientOutput)}
})
