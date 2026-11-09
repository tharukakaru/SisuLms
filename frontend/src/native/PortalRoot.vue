<script setup>
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

import mascot from '../assets/mascot.png'


import '@fontsource-variable/manrope'

import {ref,onMounted} from 'vue'

import Icon from '../Icon.vue'

import '../brand.css'

import MobileVerification from './MobileVerification.vue'

import {request} from './client'

const OperatorWorkspace=defineAsyncComponent(()=>import('./AdvancedWorkspace.vue'))

const Campus=defineAsyncComponent(()=>import('../App.vue'))

const ControlPlane=defineAsyncComponent(()=>import('./ControlPlane.vue'))

const Subscription=defineAsyncComponent(()=>import('./Subscription.vue'))

const Owner=defineAsyncComponent(()=>import('./SuperAdmin.vue'))

const Profile=defineAsyncComponent(()=>import('../commerce/ProfileEditor.vue'))

const Signup=defineAsyncComponent(()=>import('./RegistrationFlow.vue'))

const AccountSubscription=defineAsyncComponent(()=>import('./SubscriptionBilling.vue'))

const subscription=ref(null),policy=ref({})

const session=ref(null),error=ref(''),busy=ref(true),selected=ref('Student'),signup=ref(new URLSearchParams(location.search).get('signup')==='1'),dark=ref(false)

const roles=[{name:'Student',icon:'GraduationCap',text:'Learn, explore and grow.'},{name:'Teacher',icon:'BookOpen',text:'Your own teaching space.'},{name:'Institute',icon:'Building2',text:'Your teachers and classrooms.'}]

function openSignup(){sessionStorage.setItem('sisu_signup_role',selected.value==='Teacher'?'Individual Teacher':selected.value);signup.value=true}

async function google(){try{const r=await request('portal_policy','google_start');const u=new URL(r.url);if(u.protocol!=='https:'||u.hostname!=='accounts.google.com')throw Error('Google sign-in is unavailable');location.assign(u.href)}catch(e){error.value=e.message}}

async function connect(){busy.value=true;error.value='';try{session.value=await request('portal_session','current',{},'GET');if(session.value.csrf_token)window.csrf_token=session.value.csrf_token;if(session.value.member)subscription.value=(await request('account_billing','status')).account}catch(e){error.value=e.message}finally{busy.value=false}}

onMounted(()=>{if(!firebaseTestPage&&!passwordConfirmation){connect();request('portal_policy','public',{},'GET').then(p=>policy.value=p).catch(()=>{})}})

</script>

<template>
<CampusSwitcher provider v-if="session?.shared_campus&&session.authenticated&&!session.member&&session.role!=='Student'&&session.onboarding_kind!=='Student'&&(session.onboarding_kind!=='Institute'||session.workspace_choices_required)"/>

<PasswordConfirmation v-if="passwordConfirmation"/><section v-else-if="firebaseTestPage" class="panel" style="max-width:760px;margin:40px auto;padding:24px"><h1>SISU browser notification test</h1><p>This test uses your configured sandbox account.</p><a href="/sandbox_firebase_login">Sign in as sandbox Administrator</a><FirebasePush/></section>

  <ControlPlane v-else-if="session?.control_plane&&session.role==='Super Admin'"/>

  <Subscription v-else-if="session?.control_plane&&session.authenticated" control-plane/>

  <ProviderAccessGate v-else-if="session?.member&&session.role!=='Student'&&(!subscription||(subscription.workspace_available??subscription.available)===false)" :role="session.role" @changed="connect"/><AccountSubscription v-else-if="session?.member&&session.role!=='Student'&&(!subscription||(subscription.workspace_available??subscription.available)===false)" standalone @changed="connect"/>

  <Owner v-else-if="session?.role==='Super Admin'" :session="session"/>

  <Campus v-else-if="session?.shared_campus&&!session.member&&session.onboarding_kind==='Student'&&!newGoogleSignup" shared-campus :general-session="session"/><GeneralCampus v-else-if="session?.shared_campus&&!session.member&&(session.onboarding_kind!=='Institute'||session.workspace_choices_required)&&!(policy.self_signup_enabled&&newGoogleSignup)" :session="session"/>
  <OperatorWorkspace v-else-if="session?.role==='Operator'" standalone/>

  <Campus v-else-if="session?.member" :shared-campus="session.shared_campus"/>

  <VerifiedSignup v-else-if="session?.authenticated && policy.self_signup_enabled && newGoogleSignup" :policy="policy" google-session @back="connect"/><div v-else-if="session?.authenticated" class="entry-onboarding"><h1>Let’s make this space yours.</h1><p>Complete your profile and mobile verification before your workspace is activated.</p><p>Account type: {{session.onboarding_kind}}</p><MobileVerification/><Profile :key="session.onboarding_kind" :member="{user:session.user,full_name:session.user,role:session.onboarding_kind==='Institute'?'Admin':session.onboarding_kind}" @saved="connect"/><a href="/me">Account settings</a><a href="/api/method/logout">Sign out</a></div>

  <Signup v-else-if="signup" @back="signup=false" @dashboard="connect"/>

  <main v-else class="sisu-entry" :class="{'entry-dark':dark}">

    <header><a href="#" class="entry-brand"><BrandLogo/></a><div><button class="entry-icon" @click="dark=!dark" :aria-label="dark?'Light mode':'Dark mode'"><Icon :name="dark?'Sun':'Moon'"/></button></div></header>

    <div class="entry-layout"><section class="entry-story"><img class="entry-spheres" src="../assets/spheres.png" alt="" aria-hidden="true" loading="lazy" decoding="async" width="420" height="595"/><span class="entry-kicker">YOUR NEXT CHAPTER STARTS HERE</span><h1>Big dreams. <br>Little steps. <br><em>Your space.</em></h1><p>A calm home for learning, teaching and all the wonderful things you’ll become.</p><footer><span>✦ A place to belong</span><span>Made for curious minds</span></footer></section>

    <div class="entry-mascot" aria-hidden="true"><img class="mascot-body" :src="mascot" alt="" width="500" height="500" decoding="async"/><img class="mascot-hand" :src="mascot" alt="" width="500" height="500" decoding="async"/></div>

    <div class="entry-card-wrap"><section class="entry-card"><span class="entry-kicker">COME ON IN</span><h2>It’s good to see you.</h2><p>Choose your account type.</p><div class="entry-roles"><button v-for="r in roles" :key="r.name" @click="selected=r.name" :class="{selected:selected===r.name}" :aria-pressed="selected===r.name"><span><Icon :name="r.icon" :size="21"/></span><div><strong>{{r.name}}</strong><small>{{r.text}}</small></div><i>{{selected===r.name?'✓':'›'}}</i></button></div>

      <div class="entry-login-actions"><a class="entry-primary" href="/login?redirect-to=/campus">Sign in with email and password →</a><button class="entry-primary entry-google" :disabled="!policy.google_available" @click="google"><img :src="'/assets/frappe/icons/social/google.svg'" alt="" width="20" height="20"/>Continue with Google</button></div><div class="entry-divider"><span>NEW TO SISU?</span></div><button class="entry-secondary" @click="openSignup">Create your account <Icon name="Plus" :size="16"/></button><p class="entry-subtle">{{policy.self_signup_enabled?'Verify your email and phone, create your password, then sign in.':'Students use Google. Teachers and institutes apply for review, then set a password through a secure email.'}}</p>

      <div v-if="error" class="entry-status" role="status"><span class="status-dot"></span><div><strong>Connection or account issue</strong><p>{{error}}</p><button @click="connect" :disabled="busy">Check connection again</button></div></div><p v-else-if="busy" role="status">Checking your session…</p>

    </section></div></div><footer class="entry-bottom">{{policy.self_signup_enabled?'Teachers and institutes select and pay for a plan before workspace access.':'One 14-day trial per new account. Then a monthly subscription.'}}</footer>

  </main>

</template>

<style>

.sisu-entry{--entry-bg:rgb(108 106 238 / 6%);--entry-card:#fffcff;--entry-ink:#3b3050;--entry-muted:#7b708b;--entry-border:rgb(108 106 238 / 12%);min-height:100vh;background:var(--entry-bg);color:var(--entry-ink);padding:34px max(28px,6vw);font-family:Inter,system-ui,sans-serif}.sisu-entry.entry-dark{--entry-bg:#201a2d;--entry-card:#2c243b;--entry-ink:#f3f1fb;--entry-muted:#b3a5c5;--entry-border:#453854}.sisu-entry header,.sisu-entry header>div,.entry-bottom,.entry-story footer{display:flex;align-items:center;justify-content:space-between;gap:25px}.entry-brand{font-size:39px;font-weight:800;letter-spacing:-3px;color:inherit;text-decoration:none}.entry-brand span{color:#6C6AEE;font-size:22px;margin-left:8px}.entry-note{font-size:12px;color:var(--entry-muted)}.entry-icon{background:var(--entry-card);border:1px solid var(--entry-border);border-radius:50%;padding:12px;color:inherit;cursor:pointer}.entry-layout{display:grid;grid-template-columns:1fr clamp(200px,18vw,340px) 1.1fr;gap:clamp(20px,3.5vw,56px);max-width:1560px;margin:70px auto 50px;align-items:center}.entry-kicker{font-size:10px;letter-spacing:2.7px;font-weight:600;color:var(--entry-muted)}.entry-story h1{color:var(--entry-ink);font-size:clamp(44px,5vw,74px);line-height:1.12;letter-spacing:-3px;margin:27px 0}.entry-story h1 em{color:#6C6AEE;font-style:normal}.entry-story>p{max-width:365px;color:var(--entry-muted);font-size:15px;line-height:1.9}.entry-story footer{margin-top:28px;justify-content:flex-start;font-size:11px;color:var(--entry-muted)}
.entry-story{position:relative}
.entry-spheres{position:absolute;top:58%;left:46%;width:min(430px,135%);height:auto;max-width:none;transform:translate(-50%,-50%);mix-blend-mode:multiply;opacity:.8;pointer-events:none;user-select:none}
.entry-dark .entry-spheres{mix-blend-mode:screen;opacity:.4;filter:blur(60px)}.entry-card{padding:38px;border:1px solid var(--entry-border);border-radius:30px;background:var(--entry-card);box-shadow:0 25px 70px #6a43860b}.entry-card h2{color:var(--entry-ink);font-size:30px;letter-spacing:-1px;margin:14px 0}.entry-card>p{font-size:13px;color:var(--entry-muted);line-height:1.7}.entry-roles{display:grid;gap:10px;margin:26px 0}.entry-roles button{display:flex;align-items:center;gap:14px;width:100%;padding:15px;border:1px solid var(--entry-border);border-radius:15px;background:transparent;color:inherit;cursor:pointer;text-align:left}.entry-roles button.selected{background:#6C6AEE1a;border-color:#6C6AEE}.entry-roles button>span{background:#6C6AEE19;padding:10px;border-radius:12px;color:#6C6AEE}.entry-roles button div{display:grid;gap:5px;flex:1}.entry-roles strong{font-size:13px}.entry-roles small{font-size:11px;color:var(--entry-muted)}.entry-roles i{font-style:normal;color:#6C6AEE}.entry-primary,.entry-google{margin-top:14px;background:#fff;color:#443153;border:1px solid #c4bbd5;box-shadow:none}.entry-google:disabled{opacity:.55;cursor:not-allowed}.entry-primary,.entry-secondary{display:flex;align-items:center;justify-content:center;gap:15px;box-sizing:border-box;min-height:52px;font-family:inherit;border-radius:13px;padding:16px;font-size:13px;font-weight:600;width:100%;text-decoration:none;cursor:pointer}.entry-primary{background:#6C6AEE;color:#fff;box-shadow:0 7px 16px #6C6AEE20}.entry-google{margin-top:14px;background:#fff;color:#443153;border:1px solid #c4bbd5;box-shadow:none}.entry-google:disabled{opacity:.55;cursor:not-allowed}.entry-secondary{border:1px solid var(--entry-border);color:inherit;background:transparent}.entry-secure{display:flex;align-items:center;justify-content:center;gap:7px;font-size:10px!important;margin:13px 0}.entry-divider{border-top:1px solid var(--entry-border);text-align:center;margin:26px 0 20px;height:0}.entry-divider span{position:relative;top:-8px;padding:0 14px;background:var(--entry-card);font-size:9px;letter-spacing:1px;color:var(--entry-muted)}.entry-subtle{font-size:10px!important;text-align:center;margin:14px 8px}.entry-owner{font-size:11px;margin-top:24px;color:var(--entry-muted);line-height:1.7}.entry-owner summary{cursor:pointer}.entry-owner a{display:block;margin-top:12px;color:#6C6AEE}.entry-status{margin-top:18px;padding:13px;display:flex;gap:10px;border:1px solid var(--entry-border);border-radius:12px;font-size:10px;color:var(--entry-muted);line-height:1.6}.entry-status p{margin:4px 0}.entry-status button{border:0;background:none;padding:0;text-decoration:underline;color:inherit;font-size:10px;cursor:pointer}.status-dot{background:#c7a478;width:6px;height:6px;border-radius:50%;margin-top:5px;flex-shrink:0}.entry-bottom{font-size:11px;color:var(--entry-muted);max-width:1240px;margin:auto}.entry-onboarding{max-width:780px;margin:70px auto;padding:25px}.entry-onboarding>a{margin-right:20px}@media(max-width:850px){.entry-layout{gap:35px;margin-top:40px}.entry-card{padding:25px}.entry-story h1{font-size:46px}.entry-note{display:none}}@media(max-width:640px){.entry-layout{grid-template-columns:1fr;margin-top:35px}.entry-story h1{font-size:44px}.entry-story>p{font-size:13px}.entry-story footer{display:none}.entry-spheres{display:none}.entry-bottom{flex-direction:column;gap:10px;text-align:center}.entry-card h2{font-size:26px}}

</style>


<style scoped>.entry-card .entry-primary{width:100%;border-radius:13px;padding:8px 16px;font-size:14px;font-weight:600;text-decoration:none;line-height:1.4}.entry-card .entry-google{margin-top:14px;background:#fff;color:#443153;border:1px solid #c4bbd5;box-shadow:none}.entry-primary:focus-visible,.entry-secondary:focus-visible{outline:3px solid #ad99d3;outline-offset:3px}.entry-google img{flex:none}</style>


<style scoped>.entry-login-actions{display:grid;gap:clamp(8px,1.4vh,16px);margin-top:clamp(8px,1.6vh,18px)}.entry-card .entry-login-actions .entry-primary{margin:0;min-height:clamp(44px,5.8vh,52px)}</style>

<style>/* entry-fit */
/* Sizes follow viewport height so the whole page fits on landing; min-height (not height) keeps scrolling available for browser zoom or a long error. */
.sisu-entry{display:flex;flex-direction:column;box-sizing:border-box;min-height:100vh;min-height:100dvh;padding:clamp(10px,2.6vh,34px) clamp(16px,6vw,96px)}
.sisu-entry header{flex:none}
.sisu-entry .entry-icon{display:grid;place-items:center;box-sizing:border-box;width:44px;height:44px;padding:0}
.sisu-entry .entry-layout{flex:1;width:100%;gap:clamp(24px,6vw,96px);margin:clamp(6px,1.6vh,32px) auto;overflow:clip}
.sisu-entry .entry-bottom{flex:none;width:100%;margin:0 auto;font-size:12px;line-height:1.4}
.sisu-entry .entry-story h1{margin:clamp(8px,2.2vh,27px) 0;font-size:clamp(32px,min(5vw,8.6vh),74px);line-height:1.08;letter-spacing:-.04em}
.sisu-entry .entry-story>p{margin:0;line-height:1.6}
.sisu-entry .entry-story footer{margin-top:clamp(10px,2.6vh,28px);flex-wrap:wrap;font-size:12px}
.sisu-entry .entry-card{box-sizing:border-box;width:100%;min-width:0;padding:clamp(14px,3vh,38px) clamp(18px,2.6vw,38px)}
.sisu-entry .entry-kicker{font-size:11px}
.sisu-entry .entry-card h2{margin:clamp(3px,1vh,14px) 0;font-size:clamp(21px,3.4vh,30px)}
.sisu-entry .entry-card>p{margin:0;line-height:1.4}
.sisu-entry .entry-roles{gap:clamp(6px,1vh,10px);margin:clamp(8px,1.8vh,26px) 0}
.sisu-entry .entry-roles button{gap:12px;min-height:44px;padding:clamp(5px,1.1vh,15px) 14px}
.sisu-entry .entry-roles button>span{display:grid;place-items:center;padding:clamp(4px,.8vh,10px)}
.sisu-entry .entry-roles small{font-size:12px}
.sisu-entry .entry-secondary{min-height:clamp(44px,5.8vh,52px);padding:8px 16px}
.sisu-entry .entry-divider{margin:clamp(14px,2.6vh,26px) 0 clamp(6px,1.4vh,20px)}
.sisu-entry .entry-divider span{font-size:11px}
.sisu-entry .entry-subtle{margin:clamp(6px,1.2vh,14px) 8px 0;font-size:12px!important;line-height:1.35}
/* Short screens: account types become one row of tiles. */
@media(max-height:680px),(max-width:480px),(max-width:820px) and (orientation:portrait) and (max-height:1100px){.sisu-entry .entry-roles{grid-template-columns:repeat(3,minmax(0,1fr))}.sisu-entry .entry-roles button{flex-direction:column;justify-content:center;gap:4px;padding:6px 4px;text-align:center}.sisu-entry .entry-roles button div{justify-items:center}.sisu-entry .entry-roles small,.sisu-entry .entry-roles i{display:none}}
/* Landscape phones: paired buttons, and only the essentials beside the card. */
@media(max-height:480px){.sisu-entry .entry-login-actions{grid-template-columns:repeat(2,minmax(0,1fr))}.sisu-entry .entry-subtle,.sisu-entry .entry-bottom,.sisu-entry .entry-story footer,.sisu-entry .entry-story>p,.sisu-entry .entry-story .entry-kicker{display:none}.sisu-entry .entry-card{border-radius:20px}.sisu-entry .entry-card h2{font-size:20px}.sisu-entry .entry-card>p{display:none}.sisu-entry header{position:absolute;inset:8px auto auto clamp(16px,6vw,96px);right:50%;z-index:1}.sisu-entry .entry-story{padding-top:48px}.sisu-entry .entry-layout{margin:0}.sisu-entry .entry-card .entry-primary,.sisu-entry .entry-secondary{font-size:13px;padding:6px 8px}}
/* Narrow or portrait: one column, card under a compact headline. */
@media(max-width:560px),(max-width:820px) and (orientation:portrait){.sisu-entry .entry-layout{grid-template-columns:minmax(0,1fr);justify-items:center;align-content:center;gap:clamp(8px,2vh,28px)}.sisu-entry .entry-story,.sisu-entry .entry-card-wrap,.sisu-entry .entry-card{width:100%;max-width:560px}.sisu-entry .entry-story h1{font-size:clamp(26px,min(8.6vw,5.4vh),56px)}.sisu-entry .entry-story footer{display:none}.sisu-entry .entry-spheres{display:none}.sisu-entry .entry-bottom{text-align:center}}
@media(max-width:560px) and (max-height:860px),(max-width:820px) and (orientation:portrait) and (max-height:860px){.sisu-entry .entry-story .entry-kicker,.sisu-entry .entry-story>p{display:none}.sisu-entry .entry-story h1{margin:0;font-size:clamp(24px,7.4vw,32px)}.sisu-entry .entry-story h1 br{display:none}}
@media(max-width:340px){.sisu-entry .entry-card .entry-primary{font-size:13px;padding:8px}}
@media(max-width:560px) and (max-height:600px){.sisu-entry .entry-subtle,.sisu-entry .entry-card>p{display:none}}
/* Mascot peeks out from behind the card: mirrored so the raised hand stays visible; the hand is a second clipped copy of the art so it can wave alone. */
.entry-card-wrap{min-width:0;width:100%}
.sisu-entry .entry-card{min-width:0}
.entry-mascot{width:100%;aspect-ratio:1;justify-self:center;transform:scaleX(-1);pointer-events:none;user-select:none}
.entry-mascot img{position:absolute;inset:0;width:100%;height:100%}
.mascot-body{clip-path:polygon(0 0,100% 0,100% 37.2%,80% 37.2%,76.6% 41.4%,75.6% 44.4%,74.2% 47.2%,75.2% 60%,100% 60%,100% 100%,0 100%)}
.mascot-hand{clip-path:polygon(80% 37.2%,100% 37.2%,100% 60%,74.4% 60%,73.6% 49%,74.2% 47.2%,75.6% 44.4%,76.6% 41.4%);transform-origin:73.2% 54.4%;animation:mascot-wave 3.6s ease-in-out infinite}
@keyframes mascot-wave{0%,45%,100%{transform:rotate(0)}10%,30%{transform:rotate(-11deg)}20%,38%{transform:rotate(4deg)}}
@media(prefers-reduced-motion:reduce){.mascot-hand{animation:none}}
@media(max-width:1150px),(max-height:480px),(max-width:820px) and (orientation:portrait){.entry-mascot{display:none}}
@media(min-width:561px) and (max-width:1150px) and (orientation:landscape),(min-width:561px) and (max-height:480px) and (orientation:landscape){.sisu-entry .entry-layout{grid-template-columns:1fr 1.15fr}}
</style>
