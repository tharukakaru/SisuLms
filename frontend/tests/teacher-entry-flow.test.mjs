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
    .replace("const ProviderAccessGate=defineAsyncComponent(()=>import('./ProviderAccessGate.vue'))",realGate?"const ProviderAccessGate=RealProviderAccessGate":"const ProviderAccessGate=stub('ProviderAccessGate')")
    .replace(/^import (.+?) from ['"](.+?)['"];?$/gm,(line,binding,path)=>{
      if(path==='vue'||path==='./.teacher-gate-flow-test.mjs')return line
      if(['./teacherEntryPath','./existingAccount'].includes(path))return line.replace(path,path+'.js')
      if(path==='./ProviderAccessGate.vue'&&realGate)return `import ProviderAccessGate from './.teacher-gate-flow-test.mjs'`
      if(path==='./PaymentRequired.vue')return `import PaymentRequired from './.payment-required-flow-test.mjs'`
      if(path==='./client')return 'const request=(...args)=>globalThis.__teacherFlowRequest(...args); const csrf=()=>"test-csrf"; const decode=async response=>{if(!response.ok)throw Error("Request failed");return response.json()}'
      if(path==='../asyncPage')return `const defineAsyncComponent=loader=>stub(loader.toString().match(/import\\(['"](.+?)['"]\\)/)[1].split('/').pop().replace('.vue',''))`
      if(binding.startsWith('{'))return binding.slice(1,-1).split(',').map(n=>`const ${n.trim()}=stub('${n.trim()}')`).join('\n')
      return `const ${binding}=stub('${binding}')`
    }).replace(/^import ['"].+?['"];?$/gm,'')
  code=(realGate?"import RealProviderAccessGate from './.teacher-gate-flow-test.mjs';\n":'')+`import {h} from 'vue'; const stub=name=>({inheritAttrs:false,setup:(_,ctx)=>()=>h(name,ctx.attrs,ctx.slots.default?.())});\n`+code
  await writeFile(output,code+'\n'+template.code.replace('export function render','function render')+'\ncomponent.render=render;export default component;')
}

test('teacher sign-in routes preserve access gates, institute actions and signup kinds',async()=>{
  const output=new URL('../src/native/.teacher-portal-flow-test.mjs',import.meta.url)
  const gateOutput=new URL('../src/native/.teacher-gate-flow-test.mjs',import.meta.url)
  const paymentOutput=new URL('../src/native/.payment-required-flow-test.mjs',import.meta.url)
  const previous={window:globalThis.window,location:globalThis.location,sessionStorage:globalThis.sessionStorage,__teacherFlowRequest:globalThis.__teacherFlowRequest}
  const values=new Map(),calls=[]
  globalThis.sessionStorage={getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)}
  globalThis.location={hash:'',search:'',assign:()=>{}}
  globalThis.window={history:{length:1}}
  let unified=false,session={authenticated:false},available=true,billingError=false,existingGoogle=true,holdGoogle=false,finishGoogle,holdBilling=false,finishBilling,app
  globalThis.__teacherFlowRequest=async(...args)=>{
    calls.push(args)
    if(args[0]==='portal_session')return session
    if(args[0]==='portal_policy'&&args[1]==='google_start')return {url:'https://accounts.google.com/o/oauth2/auth?state=fixture'}
    if(args[0]==='portal_policy')return {self_signup_enabled:true,google_available:true,unified_teacher_signup:unified}
    if(args[0]==='teacher_workspace'){session={...session,role:'Teacher',member:{role:'Teacher'}};return {selected:'personal'}}
    if(args[0]==='registration'&&args[1]==='self_google_details'){if(holdGoogle)return new Promise(resolve=>finishGoogle=resolve);return {account_exists:existingGoogle}}
    if(args[0]==='account_billing'){if(holdBilling)return new Promise(resolve=>finishBilling=resolve);if(billingError)throw Error('Unable to check billing. Try again.');return {account:{workspace_available:available}}}
    throw Error('Unexpected API call '+args[0])
  }
  try{
    await compile('PaymentRequired',paymentOutput)
    await compile('ProviderAccessGate',gateOutput)
    await compile('PortalRoot',output,true)
    const {default:Portal}=await import(output.href)
    const teacher={authenticated:true,user:'teacher@example.invalid',role:'Teacher',member:{role:'Teacher'}}
    for(const [choice,kind] of [['Student','Student'],['Teacher','Individual Teacher'],['Institute','Institute']]){
      session={authenticated:false};calls.length=0
      const entryRoot={children:[]};app=renderer.createApp(Portal);const entryVm=app.mount(entryRoot);await flush()
      entryVm.$.setupState.chooseRole(choice);await nextTick()
      await button(entryRoot,'Continue with Google').props.onClick();await flush()
      assert.deepEqual(calls.find(c=>c[1]==='google_start'),['portal_policy','google_start',{signup:1,kind}])
      app.unmount();app=null
    }

    for(const role of ['Teacher','Admin'])for(const paid of [true,false]){
      values.clear();session={...teacher,role,member:{role}};holdBilling=true
      const pendingRoot={children:[]};app=renderer.createApp(Portal);app.mount(pendingRoot);await flush()
      assert.ok(marker(pendingRoot,'PageLoading'),'Wait for billing before choosing a dashboard or payment gate')
      assert.equal(button(pendingRoot,'Open billing'),undefined,'Do not flash a false payment warning')
      assert.equal(marker(pendingRoot,'App'),undefined)
      finishBilling({account:{workspace_available:paid}});holdBilling=false;await flush()
      assert.ok(paid?marker(pendingRoot,'App'):role==='Admin'?marker(pendingRoot,'InstituteSetupLayout'):marker(pendingRoot,'SubscriptionBilling'))
      if(role==='Admin'&&!paid){
        const billing=marker(pendingRoot,'SubscriptionBilling')
        assert.ok(billing,'Institute plan selection opens directly in the setup page')
        assert.equal(marker(pendingRoot,'App'),undefined,'Unpaid institute remains outside the dashboard')
        assert.ok(Object.hasOwn(billing.props,'onboarding'))
        available=true;await billing.props.onChanged();await flush()
        assert.ok(marker(pendingRoot,'App'),'Verified billing refresh unlocks the institute workspace')
      }
      app.unmount();app=null
    }
    for(const path of ['individual','institute'])for(const paid of [true,false]){
      values.clear();calls.length=0;session={authenticated:false};available=paid
      const root={children:[]};app=renderer.createApp(Portal);const vm=app.mount(root);await flush()
      const state=vm.$.setupState
      state.chooseRole('Teacher');state.teacherPath=path;await nextTick()
      const signIn=nodes(root).find(n=>n.tag==='a'&&n.props.href==='/login?redirect-to=/campus')
      assert.ok(signIn);signIn.props.onClick()
      session=teacher;await state.connect();await flush()
      // Existing membership wins over any old sign-in path preference.
      assert.ok(paid?marker(root,'App'):marker(root,'SubscriptionBilling'))
      assert.equal(button(root,'Continue as individual teacher'),undefined)
      assert.deepEqual(calls.filter(c=>c[0]==='account_billing'),[['account_billing','status']])
      assert.deepEqual(calls.filter(c=>c[0]==='portal_session'),[['portal_session','current',{},'GET'],['portal_session','current',{},'GET']])
      if(!paid){
            assert.ok(marker(root,'SubscriptionBilling'))
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
      assert.equal(marker(root,'RegistrationFlow').props['initial-provider-kind'],path==='institute'?'Institute Teacher':'Individual Teacher')
      assert.equal(values.get('sisu_signup_role'),path==='institute'?'Institute Teacher':'Individual Teacher')
      session={...teacher,member:null,role:'Campus',onboarding_kind:'Teacher',shared_campus:true}
      await state.connect();await flush()
      assert.ok(marker(root,'MobileVerification'),'Both teacher signup paths require phone verification first')
      session={...teacher,role:'Student',member:{role:'Student'}};await state.connect();await flush()
      assert.ok(marker(root,'App'));assert.equal(button(root,'Join your registered institute'),undefined)
      app.unmount();app=null
    }
    for(const kind of ['Teacher','Institute']){
      values.clear();session={authenticated:true,user:'provider@example.invalid',role:'Campus',member:null,onboarding_kind:kind,shared_campus:true,teaching_path:'individual',provider_onboarding_required:true}
      const root={children:[]};app=renderer.createApp(Portal);const vm=app.mount(root);await flush()
      assert.ok(marker(root,'ProviderFirstLogin'))
      session={...session,provider_onboarding_required:false};await vm.$.setupState.connect();await flush()
      assert.ok(marker(root,'ProviderOnboardingStatus'),'A saved provider profile must not loop back to profile completion')
      assert.equal(marker(root,'MobileVerification'),undefined)
      assert.equal(marker(root,'ProfileEditor'),undefined)
      assert.equal(marker(root,'App'),undefined,'Saving a profile must not grant workspace access')
      if(kind==='Teacher'){
        session={...session,teaching_path:'institute'};await vm.$.setupState.connect();await flush()
        assert.equal(marker(root,'ProviderOnboardingStatus'),undefined,'Institute teachers retain their membership request flow')
        assert.ok(marker(root,'MobileVerification'))
      }
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
    assert.ok(marker(root,'InstituteSetupLayout'))
    billingError=true;await marker(root,'SubscriptionBilling').props.onChanged();await flush()
    assert.ok(nodes(root).some(n=>n.props?.role==='alert'&&nodes(n).some(child=>child.text==='Unable to check billing. Try again.')))
    assert.equal(marker(root,'App'),undefined)
    assert.ok(marker(root,'SubscriptionBilling'),'Billing remains accessible after an access-check failure')
    billingError=false;available=true;button(root,'Try again').props.onClick();await flush()
    assert.ok(marker(root,'App'))
    app.unmount();app=null
    unified=true;values.clear();session={authenticated:false}
    const unifiedRoot={children:[]};app=renderer.createApp(Portal);let unifiedVm=app.mount(unifiedRoot);await flush()
    unifiedVm.$.setupState.chooseRole('Teacher');unifiedVm.$.setupState.openSignup();await nextTick()
    assert.ok(marker(unifiedRoot,'RegistrationFlow'),'One Teacher choice opens signup directly')
    assert.equal(marker(unifiedRoot,'ProviderAccountChoice'),undefined)
    assert.equal(marker(unifiedRoot,'RegistrationFlow').props['initial-provider-kind'],'Individual Teacher')
    app.unmount();app=null
    for(const oldPath of ['individual','institute']){
      calls.length=0;values.clear();session={authenticated:true,user:'teacher@example.invalid',role:'Campus',shared_campus:true,onboarding_kind:'Teacher',member:null,teaching_path:oldPath,provider_onboarding_required:true}
      const target={children:[]};app=renderer.createApp(Portal);const vm=app.mount(target);await flush()
      assert.ok(marker(target,'ProviderFirstLogin'))
      assert.equal(calls.filter(c=>c[0]==='teacher_workspace').length,0,'Incomplete identity cannot provision')
      session={...session,provider_onboarding_required:false};await vm.$.setupState.connect();await flush()
      assert.ok(marker(target,'App'),'Both legacy teacher paths open the shared dashboard after verification')
      assert.equal(calls.filter(c=>c[0]==='teacher_workspace').length,1)
      assert.equal(button(target,'Apply to an institute'),undefined)
      available=false;await vm.$.setupState.connect();await flush()
      assert.ok(marker(target,'App'),'Expired unified teachers retain the shell for billing and workspace switching')
      assert.equal(button(target,'Continue as individual teacher'),undefined)
      available=true;app.unmount();app=null
    }
    unified=false
    globalThis.location.search='?checkout_invoice=institute-draft'
    session=teacher;available=true
    const checkoutRoot={children:[]};app=renderer.createApp(Portal);app.mount(checkoutRoot);await flush()
    assert.ok(marker(checkoutRoot,'CheckoutEntry'),'A checkout link must check invoice ownership before opening any dashboard')
    assert.equal(marker(checkoutRoot,'CheckoutEntry').props.invoice,'institute-draft')
    assert.equal(marker(checkoutRoot,'App'),undefined,'An existing teacher session cannot flash the teacher dashboard for an institute checkout')
    app.unmount();app=null
    for(const kind of ['Student','Individual Teacher','Institute'])for(const existing of [true,false]){
      globalThis.location.search='?verified_signup=1&signup_role='+encodeURIComponent(kind)
      values.set('sisu_signup_role',kind==='Student'?'Institute':'Student')
      holdGoogle=true;existingGoogle=existing;calls.length=0
      const role=kind==='Institute'?'Admin':kind==='Student'?'Student':'Teacher'
      session={authenticated:true,user:'google@example.invalid',role:existing?role:'Campus',shared_campus:true,onboarding_kind:existing?kind:'Student',member:existing?{role}:null}
      const signupRoot={children:[]};app=renderer.createApp(Portal);app.mount(signupRoot);await flush()
      assert.ok(marker(signupRoot,'PageLoading'),'Wait for the server to classify this Google account')
      assert.equal(marker(signupRoot,'App'),undefined)
      assert.equal(marker(signupRoot,'VerifiedSignup'),undefined)
      finishGoogle({account_exists:existing});holdGoogle=false;await flush()
      assert.equal(marker(signupRoot,'ExistingAccountDialog'),undefined)
      if(existing){
        assert.ok(marker(signupRoot,'App'),kind+' existing account opens its dashboard')
        assert.equal(marker(signupRoot,'VerifiedSignup'),undefined)
      }else{
        const form=marker(signupRoot,'VerifiedSignup')
        assert.ok(form,kind+' new account opens the original full signup page')
        assert.equal(form.props['initial-kind'],kind)
        assert.equal(form.props['student-only'],kind==='Student')
        assert.equal(marker(signupRoot,'App'),undefined,'No dashboard or inline signup popup for new accounts')
        assert.equal(calls.filter(c=>c[0]==='teacher_workspace'||c[0]==='account_billing').length,0)
      }
      app.unmount();app=null
    }
    // A selected signup tile cannot change an existing account's permissions.
    globalThis.location.search='?verified_signup=1&signup_role=Institute'
    existingGoogle=true;session={...teacher};available=true
    const existingRoot={children:[]};app=renderer.createApp(Portal);app.mount(existingRoot);await flush()
    assert.ok(marker(existingRoot,'App'));assert.equal(marker(existingRoot,'VerifiedSignup'),undefined)
    assert.equal(session.role,'Teacher')
    app.unmount();app=null
    // A failed classification must never reveal the dashboard or a guessed form.
    holdGoogle=true
    const failedRoot={children:[]};app=renderer.createApp(Portal);app.mount(failedRoot);await flush()
    finishGoogle(Promise.reject(Error('Could not check Google account')));holdGoogle=false;await flush()
    assert.ok(marker(failedRoot,'PageLoading').props.error)
    assert.equal(marker(failedRoot,'App'),undefined);assert.equal(marker(failedRoot,'VerifiedSignup'),undefined)
    app.unmount();app=null
  }finally{app?.unmount();Object.assign(globalThis,previous);await Promise.all([unlink(output),unlink(gateOutput),unlink(paymentOutput)])}
})



test('checkout entry blocks another account, preserves the invoice through login and never starts a charge',async()=>{
  const output=new URL('../src/native/.checkout-entry-flow-test.mjs',import.meta.url)
  const previous={location:globalThis.location,fetch:globalThis.fetch,__teacherFlowRequest:globalThis.__teacherFlowRequest}
  let app,own=false,fail=false,logoutOK=false,redirect=''
  const calls=[]
  globalThis.location={assign:url=>redirect=url}
  globalThis.fetch=async(url,options)=>{calls.push([url,options]);return {ok:logoutOK,json:async()=>({})}}
  globalThis.__teacherFlowRequest=async(module,method)=>{
    assert.equal(module,'account_billing');assert.equal(method,'status')
    if(fail)throw Error('offline')
    return {invoices:own?[{name:'institute-draft',status:'Draft'}]:[{name:'teacher-draft',status:'Draft'}]}
  }
  try{
    await compile('CheckoutEntry',output)
    const {default:Entry}=await import(output.href)
    const root={children:[]};app=renderer.createApp(Entry,{invoice:'institute-draft',user:'teacher@example.invalid'});app.mount(root);await flush()
    assert.equal(marker(root,'SubscriptionBilling'),undefined)
    assert.ok(button(root,'Sign in with another account'))
    await button(root,'Sign in with another account').props.onClick();await flush()
    assert.equal(redirect,'','Failed logout must not open login in the old session')
    logoutOK=true;await button(root,'Sign in with another account').props.onClick();await flush()
    assert.equal(new URL('https://checkout.localhost'+redirect).searchParams.get('redirect-to'),'/campus?checkout_invoice=institute-draft#subscription')
    assert.equal(calls[0][0],'/api/method/logout');assert.equal(calls[0][1].method,'POST')
    app.unmount();app=null
    fail=true;const retryRoot={children:[]};app=renderer.createApp(Entry,{invoice:'institute-draft',user:'institute@example.invalid'});app.mount(retryRoot);await flush()
    assert.equal(marker(retryRoot,'SubscriptionBilling'),undefined,'API failure stays closed')
    fail=false;own=true;await button(retryRoot,'Check again').props.onClick();await flush()
    assert.ok(marker(retryRoot,'SubscriptionBilling'),'Matching account opens its subscription checkout')
  }finally{app?.unmount();Object.assign(globalThis,previous);await unlink(output)}
})

test('invitation entry preserves destination and offers same-email teacher signup',async()=>{
  const output=new URL('../src/native/.invitation-entry-ui-test.mjs',import.meta.url)
  let app
  try{
    await compile('InvitationEntry',output)
    const {default:Entry}=await import(output.href)
    let signups=0
    const root={children:[]};app=renderer.createApp(Entry,{signupAvailable:true,onSignup:()=>signups++});app.mount(root);await flush()
    const link=nodes(root).find(n=>n.tag==='a')
    assert.equal(link.props.href,'/login?redirect-to=%2Fcampus%23invitations')
    await button(root,'Create your teacher account').props.onClick();assert.equal(signups,1)
    assert.ok(nodes(root).some(n=>n.text?.includes('invited email')))
    app.unmount();app=null
    const closed={children:[]};app=renderer.createApp(Entry,{signupAvailable:false});app.mount(closed);await flush()
    assert.equal(button(closed,'Create your teacher account'),undefined)
  }finally{app?.unmount();await unlink(output).catch(()=>{})}
})

test('revoked workspace recovery uses server-authorized personal selection and handles failures',async()=>{
  const output=new URL('../src/native/.workspace-recovery-ui-test.mjs',import.meta.url)
  const previous={location:globalThis.location,request:globalThis.__teacherFlowRequest}
  let app,fail=true,reloads=0;const calls=[],destinations=[]
  globalThis.location={assign:path=>destinations.push(path),reload:()=>reloads++}
  globalThis.__teacherFlowRequest=async(...args)=>{calls.push(args);if(fail)throw Error('No access');return {selected:'personal'}}
  try{
    await compile('WorkspaceAccessChanged',output)
    const {default:Recovery}=await import(output.href)
    const root={children:[]};app=renderer.createApp(Recovery,{teacher:true});app.mount(root);await flush()
    await button(root,'Switch to Personal').props.onClick();await flush()
    assert.equal(destinations.length,0)
    assert.equal(reloads,0)
    assert.ok(nodes(root).some(n=>n.props?.role==='alert'))
    assert.equal(button(root,'Switch to Personal').props.disabled,false)
    fail=false;await button(root,'Switch to Personal').props.onClick();await flush()
    assert.deepEqual(calls.at(-1),['teacher_workspace','open_workspace'])
    assert.equal(destinations.at(-1),'/campus#dashboard')
    assert.equal(reloads,1)
    app.unmount();app=null
    const student={children:[]};app=renderer.createApp(Recovery,{teacher:false});app.mount(student);await flush()
    await button(student,'Choose another workspace').props.onClick()
    assert.deepEqual(calls.at(-1),['campus_context','clear'])
  }finally{app?.unmount();globalThis.location=previous.location;globalThis.__teacherFlowRequest=previous.request;await unlink(output).catch(()=>{})}
})

test('only explicit membership revocation produces the workspace recovery signal',async()=>{
  const {errorDetails}=await import('../src/native/contracts.js')
  assert.equal(errorDetails({workspace_access_changed:true},403).code,'workspace_access_changed')
  assert.equal(errorDetails({},403).code,'forbidden')
  assert.notEqual(errorDetails({workspace_access_changed:true},500).code,'workspace_access_changed')
  assert.notEqual(errorDetails({workspace_access_changed:'true'},403).code,'workspace_access_changed')
})
