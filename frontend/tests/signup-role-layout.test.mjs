import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile,writeFile,unlink} from 'node:fs/promises'
import {parse,compileScript,compileTemplate} from '@vue/compiler-sfc'
import {createRenderer,nextTick} from 'vue'

const renderer=createRenderer({
 createElement:tag=>({tag,children:[],props:{},style:{},focus(){},scrollIntoView(){},getRootNode(){return globalThis.document},addEventListener(){},removeEventListener(){},setAttribute(){},removeAttribute(){}}),
 createText:text=>({text}),createComment:text=>({text}),setText:(n,t)=>n.text=t,
 setElementText:(n,t)=>{n.text=t;n.children=[]},patchProp:(n,k,old,v)=>{n.props[k]=v;n[k]=v},
 insert:(n,p,anchor)=>{n.parent=p;const i=p.children.indexOf(anchor);if(i<0)p.children.push(n);else p.children.splice(i,0,n)},
 remove:n=>{const i=n.parent?.children.indexOf(n);if(i>=0)n.parent.children.splice(i,1)},
 parentNode:n=>n.parent,nextSibling:n=>n.parent?.children[n.parent.children.indexOf(n)+1],
})
const nodes=n=>[n,...(n.children||[]).flatMap(nodes)]
const flush=async()=>{await new Promise(r=>setImmediate(r));await nextTick()}

test('Google and email render the same original form and provider verification for all three roles',async()=>{
 const output=new URL('../src/native/.signup-layout-test.mjs',import.meta.url)
 const file=new URL('../src/native/VerifiedSignup.vue',import.meta.url)
 const {descriptor}=parse(await readFile(file,'utf8'))
 const script=compileScript(descriptor,{id:'SignupLayoutTest'})
 const template=compileTemplate({source:descriptor.template.content,filename:file.pathname,id:'SignupLayoutTest',compilerOptions:{bindingMetadata:script.bindings}})
 assert.deepEqual(template.errors,[])
 let code=script.content.replace('export default','const component =').replace(/^import (.+?) from ['"](.+?)['"];?$/gm,(line,binding,path)=>{
  if(path==='vue')return line
  if(['./passwordStrength','./ageToday'].includes(path))return line.replace(path,path+'.js')
  if(path==='./client')return 'const request=(...args)=>globalThis.__signupRequest(...args);const csrf=()=>"test"'
  if(binding.startsWith('{'))return binding.slice(1,-1).split(',').map(n=>`const ${n.trim()}=stub('${n.trim()}')`).join('\n')
  return `const ${binding}=stub('${binding}')`
 }).replace(/^import ['"].+?['"];?$/gm,'')
 await writeFile(output,"import {h} from 'vue';const stub=name=>({inheritAttrs:false,setup:(_,ctx)=>()=>h(name,ctx.attrs,ctx.slots.default?.())});\n"+code+'\n'+template.code.replace('export function render','function render')+'\ncomponent.render=render;export default component;')
 const prior={Document:globalThis.Document,sessionStorage:globalThis.sessionStorage,document:globalThis.document,__signupRequest:globalThis.__signupRequest}
 globalThis.sessionStorage={getItem:()=>null,setItem:()=>{}}
 globalThis.Document=class Document {}
 globalThis.document=Object.assign(new Document(),{activeElement:null})
 const identity={first_name:'Sadisna',last_name:'Dhanupa',email:'qa@example.invalid',kind:'Institute',organization:'Must not overwrite role fields'}
 let app
 try{
  const {default:Signup}=await import(output.href)
  for(const kind of ['Student','Individual Teacher','Institute']){
   let emailFields
   for(const googleSession of [false,true]){
    const calls=[]
    globalThis.__signupRequest=async(...args)=>{calls.push(args);return args[1]==='self_google_details'?identity:{challenge:'test-challenge'}}
    const root={children:[]}
    app=renderer.createApp(Signup,{initialKind:kind,studentOnly:kind==='Student',googleSession,policy:{privacy_policy_url:'/privacy',google_available:true,unified_teacher_signup:true}})
    const instance=app.mount(root);await flush()
    const all=nodes(root), state=instance.$.setupState
    const inputs=all.filter(n=>n.tag==='input'&&n.props['aria-label'])
    const fields=inputs.map(n=>n.props['aria-label'])
    const layout=all.find(n=>n.tag==='TeacherSignupLayout')
    assert.equal(layout.props.active,kind!=='Student')
    assert.equal(layout.props.institute,kind==='Institute')
    assert.equal(state.form.kind,kind)
    assert.equal(state.form.organization,'')
    assert.equal(all.some(n=>n.props?.class==='signup-grid'),kind==='Student','Providers must never render the generic student grid')
    assert.equal(fields.includes('Date of birth'),kind==='Student')
    assert.equal(fields.includes('Subject / expertise'),kind==='Individual Teacher')
    assert.equal(fields.includes('Recovery contact email'),kind==='Institute')
    if(!googleSession)emailFields=fields
    else assert.deepEqual(fields,emailFields,`${kind} must use identical original fields for Google and email`)
    const name=inputs.find(n=>n.props['aria-label']===(kind==='Institute'?'Administrator first name':'First name'))
    const last=inputs.find(n=>n.props['aria-label']===(kind==='Institute'?'Administrator last name':'Last name'))
    const email=inputs.find(n=>n.props['aria-label']==='Email')
    assert.equal(name.value,googleSession?identity.first_name:'')
    assert.equal(last.value,googleSession?identity.last_name:'')
    assert.equal(email.value,googleSession?identity.email:'')
    assert.equal(email.props.readonly,googleSession)
    if(kind!=='Student'){
     state.password='Test-only-password';state.confirmation='Test-only-password'
     state.start();await flush()
     assert.ok(nodes(root).some(n=>n.tag==='VerificationLayout'),'Both provider methods use the original verification page')
     assert.equal(nodes(root).some(n=>n.tag==='TeacherSignupLayout'),false)
     state.emailCode='123456';state.verify('email');await flush()
     assert.ok(nodes(root).some(n=>n.tag==='button'&&nodes(n).some(c=>c.text?.includes('Save and create account'))))
     assert.equal(calls.filter(c=>c[1]==='self_start').length,1)
    }
    app.unmount();app=null
   }
  }
 }finally{app?.unmount();Object.assign(globalThis,prior);await unlink(output)}
})
