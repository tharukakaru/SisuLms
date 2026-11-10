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
      if(path==='./teacherEntryPath')return line.replace(path,path+'.js')
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

test('teacher sign-in routes preserve access gates, institute actions and signup kinds',async()=>{
  const output=new URL('../src/native/.teacher-portal-flow-test.mjs',import.meta.url)
  const gateOutput=new URL('../src/native/.teacher-gate-flow-test.mjs',import.meta.url)
  const paymentOutput=new URL('../src/native/.payment-required-flow-test.mjs',import.meta.url)
  const previous={window:globalThis.window,location:globalThis.location,sessionStorage:globalThis.sessionStorage,__teacherFlowRequest:globalThis.__teacherFlowRequest}
  const values=new Map(),calls=[]
  globalThis.sessionStorage={getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)}
  globalThis.location={hash:'',search:''}
  globalThis.window={history:{length:1}}
  let session={authenticated:false},available=true,billingError=false,app
  globalThis.__teacherFlowRequest=async(...args)=>{
    calls.push(args)
    if(args[0]==='portal_session')return session
    if(args[0]==='portal_policy')return {self_signup_enabled:true,google_available:true}
    if(args[0]==='account_billing'){if(billingError)throw Error('Unable to check billing. Try again.');return {account:{workspace_available:available}}}
    throw Error('Unexpected API call '+args[0])
  }
  try{
    await compile('PaymentRequired',paymentOutput)
    await compile('ProviderAccessGate',gateOutput)
    await compile('PortalRoot',output,true)
    const {default:Portal}=await import(output.href)
    const teacher={authenticated:true,user:'teacher@example.invalid',role:'Teacher',member:{role:'Teacher'}}
    for(const path of ['individual','institute'])for(const paid of [true,false]){
      values.clear();calls.length=0;session={authenticated:false};available=paid
      const root={children:[]};app=renderer.createApp(Portal);const vm=app.mount(root);await flush()
      const state=vm.$.setupState
      state.chooseRole('Teacher');state.teacherPath=path;await nextTick()
      const signIn=nodes(root).find(n=>n.tag==='a'&&n.props.href==='/login?redirect-to=/campus')
      assert.ok(signIn);signIn.props.onClick()
      session=teacher;await state.connect();await flush()
      if(path==='individual')assert.ok(paid?marker(root,'App'):button(root,'Open billing'))
      else{
        assert.ok(button(root,'Continue as individual teacher'))
        assert.equal(marker(root,'App'),undefined)
        button(root,'Join your registered institute').props.onClick();await nextTick()
        assert.equal(marker(root,'InstituteJoinPicker').props.purpose,'Existing teacher confirmation')
        marker(root,'InstituteJoinPicker').props.onBack();await nextTick()
        button(root,'Apply to an institute').props.onClick();await nextTick()
        assert.equal(marker(root,'InstituteJoinPicker').props.purpose,'New application')
        marker(root,'InstituteJoinPicker').props.onBack();await nextTick()
        button(root,'Continue as individual teacher').props.onClick();await nextTick()
        assert.ok(paid?marker(root,'App'):button(root,'Open billing'))
      }
      assert.deepEqual(calls.filter(c=>c[0]==='account_billing'),[['account_billing','status']])
      assert.deepEqual(calls.filter(c=>c[0]==='portal_session'),[['portal_session','current',{},'GET'],['portal_session','current',{},'GET']])
      if(!paid){
        button(root,'Open billing').props.onClick();await nextTick()
        assert.ok(marker(root,'SubscriptionBilling'))
        button(root,'Back').props.onClick();await nextTick()
        assert.ok(button(root,'Check again'))
        available=true;button(root,'Check again').props.onClick();await flush()
        assert.ok(marker(root,'App'))
        assert.equal(calls.filter(c=>c[0]==='account_billing').length,2)
      }
      app.unmount();app=null
    }
    for(const path of ['individual','institute']){
      values.clear();session={authenticated:false}
      const root={children:[]};app=renderer.createApp(Portal);const vm=app.mount(root);await flush()
      const state=vm.$.setupState;state.openProviderSignup('Individual Teacher',path);await nextTick()
      assert.equal(marker(root,'RegistrationFlow').props['initial-provider-kind'],'Individual Teacher')
      assert.equal(values.get('sisu_signup_role'),'Individual Teacher')
      session={...teacher,member:null,role:'Campus',onboarding_kind:'Teacher',shared_campus:true}
      await state.connect();await flush()
      assert.ok(path==='individual'?marker(root,'MobileVerification'):button(root,'Join your registered institute'))
      session={...teacher,role:'Student',member:{role:'Student'}};await state.connect();await flush()
      assert.ok(marker(root,'App'));assert.equal(button(root,'Join your registered institute'),undefined)
      app.unmount();app=null
    }
    values.clear();session={authenticated:true,user:'institute@example.invalid',role:'Campus',member:null,onboarding_kind:'Institute',shared_campus:true}
    const onboardingRoot={children:[]};app=renderer.createApp(Portal);app.mount(onboardingRoot);await flush()
    assert.ok(marker(onboardingRoot,'MobileVerification'))
    assert.equal(marker(onboardingRoot,'ProfileEditor'),undefined)
    button(onboardingRoot,'Complete your profile').props.onClick();await flush()
    const editor=marker(onboardingRoot,'ProfileEditor')
    assert.deepEqual(editor.props.member,{user:session.user,full_name:session.user,role:'Admin'})
    assert.equal(editor.parent.props.class,'onboarding-profile-page')
    button(onboardingRoot,'Back to verification').props.onClick();await nextTick()
    assert.equal(editor.parent.style.display,'none')
    button(onboardingRoot,'Complete your profile').props.onClick();await nextTick()
    assert.equal(marker(onboardingRoot,'ProfileEditor'),editor,'Returning preserves the mounted editor and unsaved inputs')
    session={...session,role:'Admin',member:{role:'Admin'}};available=true
    await editor.props.onSaved();await flush();assert.ok(marker(onboardingRoot,'App'))
    app.unmount();app=null
    values.clear();session={...teacher,role:'Admin',member:{role:'Admin'}};available=false
    const root={children:[]};app=renderer.createApp(Portal);app.mount(root);await flush()
    assert.ok(button(root,'Open billing'))
    billingError=true;button(root,'Check again').props.onClick();await flush()
    assert.ok(nodes(root).some(n=>n.props?.role==='alert'&&n.text==='Unable to check billing. Try again.'))
    assert.equal(marker(root,'App'),undefined)
    button(root,'Open billing').props.onClick();await nextTick()
    assert.ok(marker(root,'SubscriptionBilling'))
    button(root,'Back').props.onClick();await nextTick()
    billingError=false;available=true;button(root,'Check again').props.onClick();await flush()
    assert.ok(marker(root,'App'))
  }finally{app?.unmount();Object.assign(globalThis,previous);await Promise.all([unlink(output),unlink(gateOutput),unlink(paymentOutput)])}
})
