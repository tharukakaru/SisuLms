<script setup>
import ExistingAccountDialog from './ExistingAccountDialog.vue'
import {googleSignupEntry} from './existingAccount'
import ProviderFirstLogin from './ProviderFirstLogin.vue'
import PageLoading from '../PageLoading.vue'
import CampusSwitcher from './CampusSwitcher.vue'
import PasswordConfirmation from './PasswordConfirmation.vue'
const passwordConfirmation=location.hash.startsWith('#password-confirm=')
import GeneralCampus from './GeneralCampus.vue'

import {asyncPage as defineAsyncComponent} from '../asyncPage'

import ProviderAccessGate from './ProviderAccessGate.vue'

import VerifiedSignup from './VerifiedSignup.vue'

import FirebasePush from './FirebasePush.vue'

const newGoogleSignup=new URLSearchParams(location.search).get('verified_signup')==='1'

const firebaseTestPage=new URLSearchParams(location.search).get('firebase_test')==='1'

import BrandLogo from '../BrandLogo.vue'

import WebWelcomeStory from '../learning/WebWelcomeStory.vue'
import LearnerSignIn from './LearnerSignIn.vue'
import ProviderAccountChoice from './ProviderAccountChoice.vue'

import '@fontsource-variable/manrope'

import {ref,onMounted,computed,nextTick} from 'vue'
import {rememberTeacherPath,resolveTeacherPath,teacherEntryView} from './teacherEntryPath'

import Icon from '../Icon.vue'
import {ArrowLeft} from 'lucide-vue-next'

import '../brand.css'

import MobileVerification from './MobileVerification.vue'
import VerificationLayout from './VerificationLayout.vue'

import {request} from './client'

const OperatorWorkspace=defineAsyncComponent(()=>import('./AdvancedWorkspace.vue'))

const Campus=defineAsyncComponent(()=>import('../App.vue'))

const ControlPlane=defineAsyncComponent(()=>import('./ControlPlane.vue'))

const Subscription=defineAsyncComponent(()=>import('./Subscription.vue'))

const Owner=defineAsyncComponent(()=>import('./SuperAdmin.vue'))

const Profile=defineAsyncComponent(()=>import('../commerce/ProfileEditor.vue'))

const Signup=defineAsyncComponent(()=>import('./RegistrationFlow.vue'))

const AccountSubscription=defineAsyncComponent(()=>import('./SubscriptionBilling.vue'))

const subscription=ref(null),policy=ref({}),existingGoogleAccount=ref(false),googleSignupError=ref(null)

const session=ref(null),error=ref(''),busy=ref(true),selected=ref('Student'),signup=ref(new URLSearchParams(location.search).get('signup')==='1'),dark=ref(false)

const roles=[{name:'Student',icon:'GraduationCap',text:'Learn, explore and grow.'},{name:'Teacher',icon:'BookOpen',text:'Your own teaching space.'},{name:'Institute',icon:'Building2',text:'Your teachers and classrooms.'}]

const roleChosen=ref(false)
const studentEmailSignup=ref(false)
function openStudentEmailSignup(){sessionStorage.setItem('sisu_signup_role','Student');studentEmailSignup.value=true}
const signupPath=ref(false)
const hasPreviousPage=window.history.length>1
const providerSignupKind=ref('')
const profileOpen=ref(false),profileStarted=ref(false),profileHeading=ref(null),profileContinue=ref(null)
const onboardingPhoneVerified=ref(false)
function showProfile(open){profileOpen.value=open;if(open)profileStarted.value=true;nextTick(()=>(open?profileHeading.value:profileContinue.value)?.focus())}
const teacherPath=ref('individual'),entryPath=ref('')
const teacherView=computed(()=>teacherEntryView(session.value,entryPath.value,newGoogleSignup))
function rememberEntry(){rememberTeacherPath(sessionStorage,'')}
function continueIndividually(){entryPath.value='individual';rememberTeacherPath(sessionStorage,'individual');resolveTeacherPath(sessionStorage,session.value)}
const roleCopy={
  Student:{title:'I’m a learner',description:'Find teachers, join classes and make room to grow.'},
  Teacher:{title:'I’m a teacher',description:'Teach your classes and manage your memberships.'},
  Institute:{title:'We’re an institute',description:'Manage your team, programmes and classrooms.'},
}

function openSignup(){if(selected.value==='Institute'){openProviderSignup('Institute');return}signupPath.value=true}

function openProviderSignup(kind,path){if(kind==='Individual Teacher'){teacherPath.value=path||teacherPath.value;rememberTeacherPath(sessionStorage,teacherPath.value)}else{rememberTeacherPath(sessionStorage,'')}if(kind==='Individual Teacher'&&teacherPath.value==='institute')kind='Institute Teacher';providerSignupKind.value=kind;sessionStorage.setItem('sisu_signup_role',kind);signup.value=true}

function chooseRole(role){roleChosen.value=selected.value===role?!roleChosen.value:true;selected.value=role;signupPath.value=false;providerSignupKind.value=''}

function goBack(){if(signupPath.value){signupPath.value=false}else if(roleChosen.value){roleChosen.value=false}else if(hasPreviousPage){window.history.back()}}

async function google(signup=false){rememberEntry();try{const r=await request('portal_policy','google_start',{signup:signup===true?1:0});const u=new URL(r.url);if(u.protocol!=='https:'||u.hostname!=='accounts.google.com')throw Error('Google sign-in is unavailable');location.assign(u.href)}catch(e){error.value=e.message}}

async function connect(){busy.value=true;error.value='';googleSignupError.value=null;try{session.value=await request('portal_session','current',{},'GET');if(!newGoogleSignup)entryPath.value=resolveTeacherPath(sessionStorage,session.value);if(session.value.csrf_token)window.csrf_token=session.value.csrf_token;const signupEntry=await googleSignupEntry(session.value,newGoogleSignup,request);if(signupEntry){policy.value=signupEntry.policy;existingGoogleAccount.value=signupEntry.accountExists;if(existingGoogleAccount.value)return}if(session.value.member)subscription.value=(await request('account_billing','status')).account}catch(e){error.value=e.message;if(newGoogleSignup)googleSignupError.value=e}finally{busy.value=false}}

onMounted(()=>{if(!firebaseTestPage&&!passwordConfirmation){connect();request('portal_policy','public',{},'GET').then(p=>policy.value=p).catch(()=>{})}})

</script>

<template>

<PageLoading v-if="busy&&(!session||newGoogleSignup||(session.member&&!subscription))&&!passwordConfirmation&&!firebaseTestPage"/><PasswordConfirmation v-else-if="passwordConfirmation"/><section v-else-if="firebaseTestPage" class="panel" style="max-width:760px;margin:40px auto;padding:24px"><h1>SISU browser notification test</h1><p>This test uses your configured sandbox account.</p><a href="/sandbox_firebase_login">Sign in as sandbox Administrator</a><FirebasePush/></section>

  <PageLoading v-else-if="googleSignupError" :error="googleSignupError"/>
  <ExistingAccountDialog v-else-if="existingGoogleAccount" authenticated/>

  <ControlPlane v-else-if="session?.control_plane&&session.role==='Super Admin'"/>

  <Subscription v-else-if="session?.control_plane&&session.authenticated" control-plane/>

  <ProviderFirstLogin v-else-if="session?.provider_onboarding_required" :session="session"/>
  <ProviderAccessGate v-else-if="teacherView==='institute'" key="institute-entry" role="Teacher" selection-only @continue="continueIndividually" @changed="connect">
    <details v-if="session.shared_campus" class="teacher-approved-workspaces"><summary>Open an approved teaching workspace</summary><CampusSwitcher provider @opening="continueIndividually"/></details>
    <button v-else-if="session.member" type="button" class="entry-secondary" @click="continueIndividually">Open my current workspace</button>
  </ProviderAccessGate>

  <ProviderAccessGate v-else-if="session?.member&&session.role!=='Student'&&(!subscription||(subscription.workspace_available??subscription.available)===false)" key="workspace-access" :role="session.role" :initial-individual="session.role==='Teacher'" :checking="busy" :error="error" @changed="connect"/><AccountSubscription v-else-if="session?.member&&session.role!=='Student'&&(!subscription||(subscription.workspace_available??subscription.available)===false)" standalone @changed="connect"/>

  <Owner v-else-if="session?.role==='Super Admin'" :session="session"/>

  <Campus v-else-if="session?.shared_campus&&!session.member&&session.onboarding_kind==='Student'&&!newGoogleSignup" shared-campus :general-session="session"/><GeneralCampus v-else-if="teacherView!=='setup'&&session?.shared_campus&&!session.member&&(session.onboarding_kind!=='Institute'||session.workspace_choices_required)&&!(policy.self_signup_enabled&&newGoogleSignup)" :session="session"/>
  <OperatorWorkspace v-else-if="session?.role==='Operator'" standalone/>

  <Campus v-else-if="session?.member" :shared-campus="session.shared_campus"/>

  <VerifiedSignup v-else-if="session?.authenticated && policy.self_signup_enabled && newGoogleSignup" :policy="policy" google-session @back="connect"/>
  <template v-else-if="session?.authenticated">
    <VerificationLayout v-show="!profileOpen" @back="goBack">
      <MobileVerification onboarding @verified="onboardingPhoneVerified=$event"/>
      <section class="onboarding-profile-next" aria-label="Profile completion">
        <p>Complete your profile and mobile verification before your workspace is activated.</p>
        <button ref="profileContinue" type="button" class="teacher-submit" :disabled="!onboardingPhoneVerified" @click="showProfile(true)">Complete your profile <Icon name="ArrowRight" :size="16"/></button>
        <p><a href="/me">Account settings</a> · <a href="/api/method/logout">Sign out</a></p>
      </section>
    </VerificationLayout>
    <main v-if="profileStarted" v-show="profileOpen" class="onboarding-profile-page" aria-labelledby="onboarding-profile-title">
      <header class="onboarding-profile-header"><a href="/campus" aria-label="SISU home"><BrandLogo/></a><nav aria-label="Account"><a href="/me">Account settings</a><a href="/api/method/logout">Sign out</a></nav></header>
      <button type="button" class="onboarding-profile-back" @click="showProfile(false)"><ArrowLeft :size="16" aria-hidden="true"/>Back to verification</button>
      <h1 id="onboarding-profile-title" ref="profileHeading" tabindex="-1">Complete your profile</h1>
      <p class="onboarding-profile-intro">Complete your profile and mobile verification before your workspace is activated. Account type: {{session.onboarding_kind}}.</p>
      <Profile :key="session.onboarding_kind" :member="{user:session.user,full_name:session.user,role:session.onboarding_kind==='Institute'?'Admin':session.onboarding_kind}" @saved="connect"/>
    </main>
  </template>

  <VerifiedSignup v-else-if="studentEmailSignup" :policy="policy" student-only @back="studentEmailSignup=false;signupPath=false"/>
  <Signup v-else-if="signup" :initial-provider-kind="providerSignupKind" @back="signup=false" @dashboard="connect"/>

  <main v-else class="sisu-entry role-selection" :class="{'entry-dark':dark,'role-selection-expanded':roleChosen&&!signupPath}">

    <header class="role-selection-header"><a href="#" class="entry-brand" aria-label="SISU home"><BrandLogo/></a></header>

    <div class="entry-layout"><WebWelcomeStory :provider="signupPath&&selected==='Teacher'"/>

    <section class="entry-card" :aria-labelledby="signupPath&&selected==='Teacher'?'provider-account-title':signupPath&&selected==='Student'?'learner-signin-title':'role-selection-title'">
      <LearnerSignIn v-if="signupPath&&selected==='Student'" :google-available="!!policy.google_available" :email-available="!!policy.self_signup_enabled" @email="openStudentEmailSignup" @google="google(true)" @choose-path="signupPath=false"/>
      <ProviderAccountChoice v-else-if="signupPath&&selected==='Teacher'" @choose="openProviderSignup" @back="signupPath=false"/>
      <template v-else><button v-if="roleChosen||hasPreviousPage" type="button" class="role-back-link" @click="goBack"><ArrowLeft :size="13" :stroke-width="1.7" aria-hidden="true"/>Back</button><h2 id="role-selection-title">Choose your SISU role</h2><p class="role-selection-subtitle">Your next chapter starts here.</p><div class="entry-roles"><button v-for="r in roles" :key="r.name" type="button" @click="chooseRole(r.name)" :class="{selected:roleChosen&&selected===r.name}" :aria-expanded="roleChosen&&selected===r.name" aria-controls="role-selection-actions"><div><strong>{{roleCopy[r.name].title}}</strong><small>{{roleCopy[r.name].description}}</small></div></button></div>

      <div id="role-selection-actions" v-show="roleChosen"><p class="entry-action-title">{{selected==='Student'?'Learner':selected}} account</p><div class="entry-login-actions"><a class="entry-primary" href="/login?redirect-to=/campus" @click="rememberEntry">Sign in with email and password →</a><button class="entry-primary entry-google" :disabled="!policy.google_available" @click="google"><img :src="'/assets/frappe/icons/social/google.svg'" alt="" width="20" height="20" style="display:inline-block;vertical-align:middle;margin-right:8px;flex-shrink:0" />Continue with Google</button></div><p v-if="!policy.google_available" class="entry-subtle">Google sign-in is being set up for this site. You can sign in with your email and password.</p><p class="entry-secure"><Icon name="ShieldCheck" :size="15"/>Your account determines your permissions.</p><div class="entry-divider"><span>NEW TO SISU?</span></div><button class="entry-secondary" @click="openSignup">Create a new account <Icon name="Plus" :size="16"/></button><p class="entry-subtle">{{policy.self_signup_enabled?'Verify your email and phone, create your password, then sign in.':'Students use Google. Teachers and institutes apply for review, then set a password through a secure email.'}}</p></div>

      </template>

      <div v-if="error" class="entry-status" role="status"><span class="status-dot"></span><div><strong>Connection or account issue</strong><p>{{error}}</p><button @click="connect" :disabled="busy">Check connection again</button></div></div><p v-else-if="busy" role="status">Checking your session…</p>

    </section></div><footer v-if="roleChosen&&selected==='Institute'" class="entry-bottom">{{policy.self_signup_enabled?'Teachers and institutes select and pay for a plan before workspace access.':'One 14-day trial per new account. Then a monthly subscription.'}}<span>Secure access · No sample accounts</span></footer>

  </main>

</template>

<style>

.sisu-entry{--entry-bg:rgb(108 106 238 / 6%);--entry-card:#fffcff;--entry-ink:#3b3050;--entry-muted:#7b708b;--entry-border:rgb(108 106 238 / 12%);min-height:100vh;background:var(--entry-bg);color:var(--entry-ink);padding:34px max(28px,6vw);font-family:Inter,system-ui,sans-serif}.sisu-entry.entry-dark{--entry-bg:#201a2d;--entry-card:#2c243b;--entry-ink:rgb(108 106 238 / 6%);--entry-muted:#b3a5c5;--entry-border:#453854}.sisu-entry header,.sisu-entry header>div,.entry-bottom,.entry-story footer{display:flex;align-items:center;justify-content:space-between;gap:25px}.entry-brand{font-size:39px;font-weight:800;letter-spacing:-3px;color:inherit;text-decoration:none}.entry-brand span{color:#6C6AEE;font-size:22px;margin-left:8px}.entry-note{font-size:12px;color:var(--entry-muted)}.entry-icon{background:var(--entry-card);border:1px solid var(--entry-border);border-radius:50%;padding:12px;color:inherit;cursor:pointer}.entry-layout{display:grid;grid-template-columns:1.1fr 1fr;gap:9%;max-width:1240px;margin:70px auto 50px;align-items:center}.entry-kicker{font-size:10px;letter-spacing:2.7px;font-weight:600;color:var(--entry-muted)}.entry-story h1{font-size:clamp(44px,5vw,74px);line-height:1.12;letter-spacing:-3px;margin:27px 0}.entry-story h1 em{color:#6C6AEE;font-style:normal}.entry-story>p{max-width:365px;color:var(--entry-muted);font-size:15px;line-height:1.9}.entry-garden{position:relative;height:210px;margin:20px 0;display:grid;place-items:center;max-width:370px}.entry-book{width:150px;height:166px;background:linear-gradient(150deg,rgb(108 106 238 / 8%),#6C6AEE);border:5px solid #fff8;border-radius:26px 38px 28px 12px;box-shadow:15px 16px 0 #6C6AEE3a,20px 24px 35px #6C6AEE1c;transform:rotate(-10deg);display:flex;align-items:center;justify-content:center;gap:13px;flex-direction:column;color:#755398}.entry-book span{font-size:12px;font-weight:600}.entry-orbit{position:absolute;width:310px;height:145px;border:1px solid #6C6AEE60;border-radius:50%;transform:rotate(-20deg)}.garden-spark{position:absolute;right:25px;top:15px;color:#6C6AEE;font-size:62px}.garden-leaf{position:absolute;left:0;bottom:0;color:#88a797;font-size:120px;transform:rotate(-30deg)}.garden-dot{width:22px;height:22px;background:#e7c59d;border-radius:50%;position:absolute;bottom:30px;right:38px}.entry-story footer{justify-content:flex-start;font-size:11px;color:var(--entry-muted)}.entry-card{padding:38px;border:1px solid var(--entry-border);border-radius:30px;background:var(--entry-card);box-shadow:0 25px 70px #6a43860b}.entry-card h2{font-size:30px;letter-spacing:-1px;margin:14px 0}.entry-card>p{font-size:13px;color:var(--entry-muted);line-height:1.7}.entry-roles{display:grid;gap:10px;margin:26px 0}.entry-roles button{display:flex;align-items:center;gap:14px;width:100%;padding:15px;border:1px solid var(--entry-border);border-radius:15px;background:transparent;color:inherit;cursor:pointer;text-align:left}.entry-roles button.selected{background:#6C6AEE1a;border-color:#6C6AEE}.entry-roles button>span{background:#6C6AEE19;padding:10px;border-radius:12px;color:#6C6AEE}.entry-roles button div{display:grid;gap:5px;flex:1}.entry-roles strong{font-size:13px}.entry-roles small{font-size:11px;color:var(--entry-muted)}.entry-roles i{font-style:normal;color:#6C6AEE}.entry-primary,.entry-google{margin-top:14px;background:#fff;color:#443153;border:1px solid #c4bbd5;box-shadow:none}.entry-google:disabled{opacity:.55;cursor:not-allowed}.entry-primary,.entry-secondary{display:flex;align-items:center;justify-content:center;gap:15px;box-sizing:border-box;min-height:52px;font-family:inherit;border-radius:13px;padding:16px;font-size:13px;font-weight:600;width:100%;text-decoration:none;cursor:pointer}.entry-primary{background:#6C6AEE;color:#fff;box-shadow:0 7px 16px #6C6AEE20}.entry-google{margin-top:14px;background:#fff;color:#443153;border:1px solid #c4bbd5;box-shadow:none}.entry-google:disabled{opacity:.55;cursor:not-allowed}.entry-secondary{border:1px solid var(--entry-border);color:inherit;background:transparent}.entry-secure{display:flex;align-items:center;justify-content:center;gap:7px;font-size:10px!important;margin:13px 0}.entry-divider{border-top:1px solid var(--entry-border);text-align:center;margin:26px 0 20px;height:0}.entry-divider span{position:relative;top:-8px;padding:0 14px;background:var(--entry-card);font-size:9px;letter-spacing:1px;color:var(--entry-muted)}.entry-subtle{font-size:10px!important;text-align:center;margin:14px 8px}.entry-owner{font-size:11px;margin-top:24px;color:var(--entry-muted);line-height:1.7}.entry-owner summary{cursor:pointer}.entry-owner a{display:block;margin-top:12px;color:#6C6AEE}.entry-status{margin-top:18px;padding:13px;display:flex;gap:10px;border:1px solid var(--entry-border);border-radius:12px;font-size:10px;color:var(--entry-muted);line-height:1.6}.entry-status p{margin:4px 0}.entry-status button{border:0;background:none;padding:0;text-decoration:underline;color:inherit;font-size:10px;cursor:pointer}.status-dot{background:#c7a478;width:6px;height:6px;border-radius:50%;margin-top:5px;flex-shrink:0}.entry-bottom{font-size:11px;color:var(--entry-muted);max-width:1240px;margin:auto}.entry-onboarding{max-width:780px;margin:70px auto;padding:25px}.entry-onboarding>a{margin-right:20px}@media(max-width:850px){.entry-layout{gap:35px;margin-top:40px}.entry-card{padding:25px}.entry-story h1{font-size:46px}.entry-note{display:none}.entry-garden{transform:scale(.85);transform-origin:left}}@media(max-width:640px){.entry-layout{grid-template-columns:1fr;margin-top:35px}.entry-story h1{font-size:44px}.entry-story>p{font-size:13px}.entry-garden,.entry-story footer{display:none}.entry-bottom{flex-direction:column;gap:10px;text-align:center}.entry-card h2{font-size:26px}}

</style>


<style scoped>.entry-card .entry-primary{width:100%;border-radius:13px;padding:16px;font-size:14px;font-weight:600;text-decoration:none;line-height:1.4}.entry-card .entry-google{margin-top:14px;background:#fff;color:#443153;border:1px solid #c4bbd5;box-shadow:none}.entry-primary:focus-visible,.entry-secondary:focus-visible{outline:3px solid #ad99d3;outline-offset:3px}.entry-google img{flex:none}</style>


<style scoped>.entry-login-actions{display:grid;gap:16px;margin-top:18px}.entry-card .entry-login-actions .entry-primary{margin:0;min-height:52px}</style>

<style scoped>
.sisu-entry.role-selection{--entry-bg:#fff;--entry-card:#fff;--entry-ink:#19182e;--entry-muted:#78758b;--entry-border:#e7e3ef;position:relative;min-height:100vh;padding:24px;background:var(--entry-bg);font-family:'Manrope Variable',sans-serif}
.sisu-entry.role-selection.entry-dark{--entry-bg:#201a2d;--entry-card:#2c243b;--entry-ink:#f5f1fb;--entry-muted:#b3a5c5;--entry-border:#584965}
.role-selection .role-selection-header{position:absolute;top:64px;left:max(72px,calc((100% - 1392px)/2 + 48px));right:72px;z-index:1}
.role-selection .entry-brand{display:flex;line-height:1}
.role-selection .entry-layout{max-width:1392px;min-height:calc(100vh - 48px);grid-template-columns:minmax(0,600px) minmax(0,1fr);gap:96px;margin:0 auto;align-items:center}
.role-selection :deep(.web-welcome-story){display:flex;flex-direction:column;align-self:stretch;min-height:1052px;padding:142px 0 0;border-radius:0 0 32px 32px;background:#fff;color:#56288d}
.role-selection :deep(.web-story-copy){padding:0 48px}
.role-selection :deep(.web-story-copy>span){font-size:10px;letter-spacing:1.3px}
.role-selection :deep(.web-story-copy h1){font-size:55px!important;line-height:1.08!important;letter-spacing:-1.8px;margin:22px 0}
.role-selection :deep(.web-story-copy p){font-size:16px;line-height:1.4;font-weight:700}
.role-selection :deep(.web-story-art){width:calc(100% - 140px);height:auto;aspect-ratio:1;object-fit:contain;margin:46px 68px 10px}
.role-selection :deep(.web-welcome-story footer){min-height:166px;padding:44px 48px 72px;gap:10px;margin-top:auto}
.role-selection .entry-card{min-width:0;padding:0 48px 0 0;border:0;border-radius:0;box-shadow:none;background:transparent}
.role-back-link{padding:0;border:0;background:none;font-family:inherit;cursor:pointer;display:flex;width:fit-content;align-items:center;gap:3px;min-height:24px;color:#56288d;font-size:13px;text-decoration:none}
.role-back-link:hover{text-decoration:underline}
.role-selection .entry-card>h2{font-family:'Manrope Variable',sans-serif;font-size:36px;font-weight:800;line-height:1.2;letter-spacing:-1.2px;margin:24px 0 20px;color:var(--entry-ink)}
.role-selection .entry-card>.role-selection-subtitle{font-size:14px;line-height:24px;margin:0;color:var(--entry-muted)}
.role-selection .entry-roles{gap:20px;margin:20px 0 0}
.role-selection .entry-card .entry-roles button{min-height:102px;padding:22px 24px;border:1px solid var(--entry-border);border-radius:20px;background:#fcfbfe;font-family:inherit;color:var(--entry-ink);transition:background .15s,border-color .15s}
.role-selection .entry-roles button div{gap:6px}
.role-selection .entry-roles strong{font-size:20px;font-weight:800;line-height:1.4}
.role-selection .entry-roles small{font-size:14px;line-height:1.5;color:var(--entry-muted)}
.role-selection .entry-card .entry-roles button:hover,.role-selection .entry-card .entry-roles button.selected{background:#f4effb;border-color:#9574bd}
.role-selection :is(.entry-roles button,.role-back-link,.entry-icon):focus-visible{outline:3px solid #8b61bb;outline-offset:4px}
.role-selection.entry-dark .entry-roles button{background:var(--entry-card)}
.role-selection.entry-dark .entry-roles button:is(:hover,.selected){background:#40314f}
.role-selection.entry-dark .role-back-link{color:#ceb4ef}
.role-selection-expanded .entry-card{padding-top:48px;padding-bottom:40px}
.role-selection #role-selection-actions{margin-top:20px;padding:20px 24px;border:1px solid var(--entry-border);border-radius:20px;background:#fcfbfe}
.role-selection.entry-dark #role-selection-actions{background:var(--entry-card)}
.role-selection .entry-action-title{margin:0;color:var(--entry-ink);font-size:16px;font-weight:800}
.role-selection #role-selection-actions .entry-primary{background:#56288d;border-color:#56288d;box-shadow:none}
.role-selection #role-selection-actions .entry-google{background:#fff;color:#56288d;border-color:var(--entry-border)}
.role-selection .entry-bottom{padding:24px 48px 0}
@media(min-width:1000px) and (max-width:1250px){
  .role-selection .entry-layout{grid-template-columns:minmax(0,45%) minmax(0,1fr);gap:48px}
  .role-selection .entry-card{padding-right:24px}
  .role-selection :deep(.web-story-copy){padding-inline:32px}
  .role-selection :deep(.web-story-copy h1){font-size:48px!important}
  .role-selection :deep(.web-story-art){width:calc(100% - 64px);margin-inline:32px}
}
@media(max-width:999px){
  .sisu-entry.role-selection{padding:32px 24px}
  .role-selection .role-selection-header{position:static;max-width:648px;margin:0 auto 60px}
  .role-selection .entry-layout{display:block;min-height:0;max-width:648px;margin:0 auto}
  .role-selection :deep(.web-welcome-story){display:none}
  .role-selection .entry-card{padding:0}
  .role-selection .entry-bottom{padding:32px 0 0}
}
@media(max-width:480px){
  .role-selection .entry-card>h2{font-size:30px;letter-spacing:-1px}
  .role-selection .entry-card .entry-roles button{padding:20px;min-height:112px}
  .role-selection .entry-roles strong{font-size:19px}
  .role-selection .entry-roles small{font-size:13px}
}
</style>

<style scoped>
.teacher-entry-path{display:flex;flex-wrap:wrap;gap:12px 24px;border:0;padding:0;margin:16px 0 0;color:var(--entry-ink)}
.teacher-entry-path legend{font-size:12px;margin-bottom:10px;color:var(--entry-muted)}
.teacher-entry-path label{display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer}
.teacher-entry-path input{accent-color:#56288d}
.teacher-approved-workspaces{margin-top:24px;font-size:13px;color:#56288d}
.teacher-approved-workspaces summary{cursor:pointer;padding:8px 0}
</style>

<style scoped>
.onboarding-profile-next{margin-top:28px;border-top:1px solid #e7e3ef;padding-top:20px}
.onboarding-profile-next p{font:400 13px/1.7 'Manrope Variable',sans-serif;color:#78758b;margin:0 0 16px}
.onboarding-profile-next p:last-child{margin:18px 0 0}
.onboarding-profile-next a{color:#56288d}
.onboarding-profile-page{max-width:1056px;min-height:100vh;margin:0 auto;padding:40px 48px 64px;background:#fff;color:#19182e;font-family:'Manrope Variable',sans-serif}
.onboarding-profile-header{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:40px}
.onboarding-profile-header nav{display:flex;gap:24px;font-size:13px}
.onboarding-profile-header a{color:#56288d}
.onboarding-profile-back{display:inline-flex;align-items:center;gap:6px;border:0;background:none;padding:6px 0;font:400 13px/24px 'Manrope Variable',sans-serif;color:#56288d;cursor:pointer}
.onboarding-profile-page>h1{font-size:32px;line-height:1.25;letter-spacing:-1px;margin:20px 0 12px}
.onboarding-profile-page>h1:focus{outline:none}
.onboarding-profile-intro{font-size:14px;line-height:1.7;color:#78758b;margin:0 0 28px;max-width:720px}
.onboarding-profile-page :is(a,button):focus-visible{outline:3px solid #8b61bb;outline-offset:4px}
@media(max-width:600px){.onboarding-profile-page{padding:28px 20px 40px}.onboarding-profile-header{align-items:flex-start;flex-wrap:wrap;gap:20px;margin-bottom:28px}.onboarding-profile-header nav{gap:20px}.onboarding-profile-page>h1{font-size:28px}}
</style>
