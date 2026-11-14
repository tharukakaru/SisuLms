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

async function compile(name,output,realGate=false){
  const file=new URL(`../src/native/${name}.vue`,import.meta.url)
  const {descriptor}=parse(await readFile(file,'utf8'))
  const script=compileScript(descriptor,{id:name})
  const template=compileTemplate({source:descriptor.template.content,filename:file.pathname,id:name,compilerOptions:{bindingMetadata:script.bindings}})
  let code=script.content.replace('export default','const component =')
    .replace(/^import (.+?) from ['"](.+?)['"];?$/gm,(line,binding,path)=>{
      if(path==='vue')return line
      if(['./teacherEntryPath','./existingAccount'].includes(path))return line.replace(path,path+'.js')
      if(path==='./ProviderAccessGate.vue'&&realGate)return `import ProviderAccessGate from './.teacher-gate-flow-test.mjs'`
      if(path==='./PaymentRequired.vue')return `import PaymentRequired from './.payment-required-flow-test.mjs'`
      if(path==='./client')return 'const request=(...args)=>globalThis.__teacherFlowRequest(...args)'
      if(path==='../asyncPage')return `const defineAsyncComponent=loader=>stub(loader.toString().match(/import\\(['"](.+?)['"]\\)/)[1].split('/').pop().replace('.vue',''))`
      if(binding.startsWith('{'))return binding.slice(1,-1).split(',').map(n=>`const ${n.trim()}=stub('${n.trim()}')`).join('\n')
      return `const ${binding}=stub('${binding}')`
    }).replace(/^import ['"].+?['"];?$/gm,'')
  code=`import {h} from 'vue'; const stub=name=>({inheritAttrs:false,setup:(_,ctx)=>()=>h(name,ctx.attrs,ctx.slots.default?.())});\n`+code
  await writeFile(output,code+'\n'+template.code.replace('export function render','function render')+'\ncomponent.render=render;export default component;')
}

test('provider registration preserves every role after loading public signup policy',async()=>{
 const output=new URL('../src/native/.registration-role-flow-test.mjs',import.meta.url)
 const previous=globalThis.__teacherFlowRequest
 let studentOnly=false
 const calls=[]
 globalThis.__teacherFlowRequest=async(...args)=>{calls.push(args);return args[0]==='portal_policy'?{self_signup_enabled:true,student_signup_only:studentOnly,provider_applications_enabled:true,privacy_policy_url:'/privacy',privacy_policy_version:'v1'}:{challenge:'test'}}
 let app
 try{
  await compile('RegistrationFlow',output)
  const {default:Registration}=await import(output.href)
  for(const role of ['Individual Teacher','Institute Teacher','Institute']){
   const root={children:[]};app=renderer.createApp(Registration,{initialProviderKind:role});app.mount(root)
   assert.ok(marker(root,'PageLoading'));assert.equal(marker(root,'VerifiedSignup'),undefined)
   await flush()
   const signup=marker(root,'VerifiedSignup')
   assert.ok(signup);assert.equal(signup.props['initial-kind'],role);assert.equal(signup.props['student-only'],false)
   app.unmount();app=null
  }
  const chooser={children:[]};app=renderer.createApp(Registration);app.mount(chooser);await flush()
  assert.equal(marker(chooser,'VerifiedSignup'),undefined,'No role must not default to a student form')
  app.unmount();app=null
  studentOnly=true
  for(const role of ['Individual Teacher','Institute Teacher','Institute']){
   const root={children:[]};app=renderer.createApp(Registration,{initialProviderKind:role});const vm=app.mount(root);await flush()
   assert.equal(marker(root,'VerifiedSignup'),undefined,'Student-only settings must not replace provider forms')
   await vm.$.setupState.submit()
   const data=calls.filter(c=>c[0]==='registration').at(-1)[2].data
   assert.equal(data.kind,role==='Institute Teacher'?'Individual Teacher':role)
   assert.equal(data.teaching_path,role==='Institute Teacher'?'institute':'individual')
   app.unmount();app=null
  }
 }finally{app?.unmount();globalThis.__teacherFlowRequest=previous;await unlink(output)}
})
