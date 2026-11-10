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
import GoogleIcon from '../GoogleIcon.vue'
import OnboardingWelcomePanel from './OnboardingWelcomePanel.vue'

import '@fontsource-variable/manrope'

import {ref,onMounted} from 'vue'

import Icon from '../Icon.vue'

import '../brand.css'

import MobileVerification from './MobileVerification.vue'

import {request,csrf} from './client'

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

const emailLogin=ref(location.pathname.startsWith('/login')||new URLSearchParams(location.search).get('login')==='1')
const loginEmail=ref(''),loginPassword=ref(''),loginBusy=ref(false),forgotNotice=ref('')

const roles=[{name:'Student',icon:'GraduationCap',text:'Learn, explore and grow.'},{name:'Teacher',icon:'BookOpen',text:'Your own teaching space.'},{name:'Institute',icon:'Building2',text:'Your teachers and classrooms.'}]

function openSignup(){sessionStorage.setItem('sisu_signup_role',selected.value==='Teacher'?'Individual Teacher':selected.value);signup.value=true}

function openEmailLogin(){
  error.value=''
  forgotNotice.value=''
  emailLogin.value=true
}

function closeEmailLogin(){
  error.value=''
  forgotNotice.value=''
  emailLogin.value=false
  if(location.pathname.startsWith('/login')){
    history.replaceState(null,'','/')
  }
}

async function submitEmailLogin(){
  if(loginBusy.value)return
  loginBusy.value=true
  error.value=''
  forgotNotice.value=''
  try{
    const rawToken=csrf()
    const token=rawToken&&!rawToken.includes('{{')?rawToken:''
    const res=await fetch('/api/method/login',{
      method:'POST',
      credentials:'same-origin',
      headers:{
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept':'application/json',
        ...(token?{'X-Frappe-CSRF-Token':token}:{})
      },
      body:new URLSearchParams({usr:loginEmail.value,pwd:loginPassword.value})
    })
    const contentType=res.headers.get('content-type')||''
    if(!contentType.includes('application/json')){
      throw Error('The Frappe service returned an unexpected response. Check your connection or sign in again.')
    }
    const data=await res.json()
    if(!res.ok||data.exc||data.exc_type){
      let msg=data.message||'Invalid login credentials.'
      try{msg=JSON.parse(JSON.parse(data._server_messages)[0]).message.replace(/<[^>]*>/g,'')}catch{}
      throw Error(msg)
    }
    loginPassword.value=''
    const redirectTo=new URLSearchParams(location.search).get('redirect-to')
    if(redirectTo&&redirectTo.startsWith('/')&&!redirectTo.startsWith('//')&&redirectTo!=='/campus'&&redirectTo!=='/'){
      location.assign(redirectTo)
      return
    }
    emailLogin.value=false
    if(location.pathname.startsWith('/login')){
      history.replaceState(null,'','/campus')
    }
    await connect()
  }catch(e){
    error.value=e.message
  }finally{
    loginBusy.value=false
  }
}

async function requestForgotReset(){
  error.value=''
  forgotNotice.value=''
  if(!loginEmail.value){
    error.value='Enter your account email address above first to request a password reset email.'
    return
  }
  loginBusy.value=true
  try{
    const rawToken=csrf()
    const token=rawToken&&!rawToken.includes('{{')?rawToken:''
    const res=await fetch('/api/method/frappe.core.doctype.user.user.reset_password',{
      method:'POST',
      credentials:'same-origin',
      headers:{
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept':'application/json',
        ...(token?{'X-Frappe-CSRF-Token':token}:{})
      },
      body:new URLSearchParams({user:loginEmail.value})
    })
    if(res.ok){
      forgotNotice.value=`If an account exists for ${loginEmail.value}, a password reset link has been sent.`
    }else{
      forgotNotice.value='Password reset links are sent to verified accounts. Contact support if you need help accessing your workspace.'
    }
  }catch{
    forgotNotice.value='Unable to reach the password reset service right now. Please check your connection.'
  }finally{
    loginBusy.value=false
  }
}

async function google(){try{const r=await request('portal_policy','google_start');const u=new URL(r.url);if(u.protocol!=='https:'||u.hostname!=='accounts.google.com')throw Error('Google sign-in is unavailable');location.assign(u.href)}catch(e){error.value=e.message}}

async function connect(){busy.value=true;error.value='';try{session.value=await request('portal_session','current',{},'GET');if(session.value.csrf_token)window.csrf_token=session.value.csrf_token;if(session.value.member)subscription.value=(await request('account_billing','status')).account}catch(e){error.value=e.message}finally{busy.value=false}}

onMounted(()=>{if(!firebaseTestPage&&!passwordConfirmation){connect();request('portal_policy','public',{},'GET').then(p=>policy.value=p).catch(()=>{})}})

</script>

<template>
<CampusSwitcher provider v-if="session?.shared_campus&&session.authenticated&&!session.member&&session.role!=='Student'&&session.onboarding_kind!=='Student'&&(session.onboarding_kind!=='Institute'||session.workspace_choices_required)"/>

<PasswordConfirmation v-else-if="passwordConfirmation"/><section v-else-if="firebaseTestPage" class="panel" style="max-width:760px;margin:40px auto;padding:24px"><h1>SISU browser notification test</h1><p>This test uses your configured sandbox account.</p><a href="/sandbox_firebase_login">Sign in as sandbox Administrator</a><FirebasePush/></section>

  <ControlPlane v-else-if="session?.control_plane&&session.role==='Super Admin'"/>

  <Subscription v-else-if="session?.control_plane&&session.authenticated" control-plane/>

  <ProviderAccessGate v-else-if="session?.member&&session.role!=='Student'&&(!subscription||(subscription.workspace_available??subscription.available)===false)" :role="session.role" @changed="connect"/><AccountSubscription v-else-if="session?.member&&session.role!=='Student'&&(!subscription||(subscription.workspace_available??subscription.available)===false)" standalone @changed="connect"/>

  <Owner v-else-if="session?.role==='Super Admin'" :session="session"/>

  <Campus v-else-if="session?.shared_campus&&!session.member&&session.onboarding_kind==='Student'&&!newGoogleSignup" shared-campus :general-session="session"/><GeneralCampus v-else-if="session?.shared_campus&&!session.member&&(session.onboarding_kind!=='Institute'||session.workspace_choices_required)&&!(policy.self_signup_enabled&&newGoogleSignup)" :session="session"/>
  <OperatorWorkspace v-else-if="session?.role==='Operator'" standalone/>

  <Campus v-else-if="session?.member" :shared-campus="session.shared_campus"/>

  <VerifiedSignup v-else-if="session?.authenticated && policy.self_signup_enabled && newGoogleSignup" :policy="policy" google-session @back="connect"/>

  <div v-else-if="session?.authenticated" class="sisu-onboarding-shell" :class="{'entry-dark':dark}">
    <div class="sisu-onboarding-split">
      <OnboardingWelcomePanel variant="grow" />
      <div class="entry-onboarding">
        <a class="sisu-back-link" href="/api/method/logout">← Back to sign in</a>
        <h1>Let’s make this space yours.</h1>
        <p class="entry-onboarding-lead">Verify your mobile number and complete your profile before your workspace is activated.</p>
        <p class="entry-onboarding-meta">Account type: <strong>{{session.onboarding_kind}}</strong></p>
        <MobileVerification/>
        <Profile :key="session.onboarding_kind" :member="{user:session.user,full_name:session.user,role:session.onboarding_kind==='Institute'?'Admin':session.onboarding_kind}" @saved="connect"/>
        <div class="entry-onboarding-links">
          <a href="/me">Account settings</a>
          <a href="/api/method/logout">Sign out</a>
        </div>
      </div>
    </div>
  </div>

  <Signup v-else-if="signup" @back="signup=false" @dashboard="connect"/>

  <main v-else class="sisu-entry" :class="{'entry-dark':dark}">
    <div class="entry-layout">
      <OnboardingWelcomePanel :variant="emailLogin ? 'connect' : (selected==='Student'?'discover':'connect')" />

      <div class="entry-card-wrap">
        <section v-if="emailLogin" class="entry-card entry-signin-form-card">
          <div class="entry-card-top">
            <button type="button" class="sisu-back-link entry-back-inline" @click="closeEmailLogin">← Back to sign in</button>
            <button class="entry-icon" type="button" @click="dark=!dark" :aria-label="dark?'Light mode':'Dark mode'">
              <Icon :name="dark?'Sun':'Moon'" :size="18"/>
            </button>
          </div>

          <h2>Welcome back.</h2>
          <p class="entry-signin-lead">Sign in to your teaching or institute workspace.</p>

          <form class="entry-email-form" @submit.prevent="submitEmailLogin">
            <label class="entry-field-label">
              <span>Email</span>
              <input
                v-model.trim="loginEmail"
                type="email"
                autocomplete="username"
                required
                placeholder="teacher@example.invalid"
              />
            </label>

            <label class="entry-field-label">
              <span>Password</span>
              <input
                v-model="loginPassword"
                type="password"
                autocomplete="current-password"
                required
                placeholder="••••••••••••"
              />
            </label>

            <p class="entry-forgot-row">
              <button type="button" class="entry-forgot-btn" :disabled="loginBusy" @click="requestForgotReset">
                Forgot password? Request a secure reset email.
              </button>
            </p>

            <p v-if="forgotNotice" class="entry-forgot-notice" role="status">{{forgotNotice}}</p>

            <button type="submit" class="entry-primary entry-signin-submit" :disabled="loginBusy">
              <span>{{loginBusy ? 'Signing in…' : 'Sign in'}}</span>
              <span class="entry-arrow" aria-hidden="true">→</span>
            </button>
          </form>

          <div v-if="error" class="entry-status" role="alert">
            <span class="status-dot"></span>
            <div>
              <strong>Sign-in or connection issue</strong>
              <p>{{error}}</p>
              <button type="button" @click="connect" :disabled="busy">Check connection again</button>
            </div>
          </div>
        </section>

        <section v-else class="entry-card">
          <div class="entry-card-top">
            <span class="entry-kicker">COME ON IN</span>
            <button class="entry-icon" type="button" @click="dark=!dark" :aria-label="dark?'Light mode':'Dark mode'">
              <Icon :name="dark?'Sun':'Moon'" :size="18"/>
            </button>
          </div>
          <h2>Good to see you.</h2>
          <p>Choose your account type.</p>

          <div class="entry-roles">
            <button
              v-for="r in roles"
              :key="r.name"
              type="button"
              @click="selected=r.name"
              :class="{selected:selected===r.name}"
              :aria-pressed="selected===r.name"
            >
              <span><Icon :name="r.icon" :size="21"/></span>
              <div>
                <strong>{{r.name}}</strong>
                <small>{{r.text}}</small>
              </div>
              <i>{{selected===r.name?'✓':'›'}}</i>
            </button>
          </div>

          <div class="entry-login-actions">
            <a class="entry-primary" href="/login?redirect-to=/campus" @click.prevent="openEmailLogin">
              <span>Sign in with email and password</span>
              <span class="entry-arrow" aria-hidden="true">→</span>
            </a>
            <button class="entry-primary entry-google" type="button" :disabled="!policy.google_available" @click="google">
              <GoogleIcon />
              <span>Continue with Google</span>
            </button>
          </div>

          <div class="entry-divider"><span>NEW TO SISU?</span></div>

          <button class="entry-secondary" type="button" @click="openSignup">
            <span>Create your account</span>
            <Icon name="Plus" :size="16"/>
          </button>

          <p class="entry-subtle">{{policy.self_signup_enabled?'Verify your email and phone, create your password, then sign in.':'Students use Google. Teachers and institutes apply for review, then set a password through a secure email.'}}</p>

          <p class="entry-bottom">{{policy.self_signup_enabled?'Teachers and institutes select and pay for a plan before workspace access.':'One 14-day trial per new account. Then a monthly subscription.'}}</p>

          <div v-if="error" class="entry-status" role="status">
            <span class="status-dot"></span>
            <div>
              <strong>Connection or account issue</strong>
              <p>{{error}}</p>
              <button type="button" @click="connect" :disabled="busy">Check connection again</button>
            </div>
          </div>
          <p v-else-if="busy" class="entry-checking" role="status">Checking your session…</p>
        </section>
      </div>
    </div>
  </main>

</template>

<style>
.sisu-entry,
.sisu-onboarding-shell {
  --entry-bg: #ffffff;
  --entry-card: #ffffff;
  --entry-ink: #19182e;
  --entry-muted: #787788;
  --entry-border: rgba(108, 106, 238, 0.12);
  --entry-brand-purple: #56288d;
  --entry-accent: #6c6aee;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--entry-bg);
  color: var(--entry-ink);
  font-family: 'Manrope', Inter, system-ui, sans-serif;
  box-sizing: border-box;
  padding: clamp(10px, 1.8vh, 20px) clamp(16px, 2.5vw, 28px);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.sisu-entry.entry-dark,
.sisu-onboarding-shell.entry-dark {
  --entry-bg: #121020;
  --entry-card: #1b182e;
  --entry-ink: #f3f1fb;
  --entry-muted: #a69bb8;
  --entry-border: rgba(164, 132, 233, 0.2);
}

.entry-layout,
.sisu-onboarding-split {
  display: grid;
  grid-template-columns: minmax(360px, 500px) minmax(0, 620px);
  gap: clamp(20px, 2.8vw, 40px);
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  align-items: center;
}

.entry-card-wrap {
  min-width: 0;
  width: 100%;
}

.entry-card,
.entry-onboarding {
  box-sizing: border-box;
  width: 100%;
  max-width: 620px;
  padding: clamp(14px, 2.2vh, 28px) clamp(20px, 3vw, 36px);
  border-radius: 24px;
  background: var(--entry-card);
}

.entry-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: clamp(4px, 0.8vh, 8px);
}

.entry-kicker {
  font-size: 10.5px;
  letter-spacing: 0.14em;
  font-weight: 500;
  color: var(--entry-muted);
  text-transform: uppercase;
}

.entry-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  padding: 0;
  background: var(--entry-card);
  border: 1px solid var(--entry-border);
  border-radius: 50%;
  color: var(--entry-ink);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.entry-icon:hover {
  border-color: var(--entry-accent);
}

.entry-card h2,
.entry-onboarding h1 {
  color: var(--entry-ink);
  font-family: 'Manrope', sans-serif;
  font-size: clamp(22px, 3vh, 30px);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin: 0 0 clamp(2px, 0.5vh, 6px);
}

.entry-card > p {
  margin: 0;
  font-size: 12.5px;
  color: var(--entry-muted);
  line-height: 1.4;
}

.entry-signin-lead {
  font-size: 14px !important;
  margin-bottom: clamp(12px, 1.8vh, 18px) !important;
}

.entry-back-inline {
  margin-bottom: 0 !important;
}

.entry-email-form {
  display: grid;
  gap: clamp(10px, 1.6vh, 16px);
  margin-top: clamp(10px, 1.6vh, 16px);
}

.entry-field-label {
  display: grid;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--entry-ink);
}

.entry-field-label input {
  box-sizing: border-box;
  width: 100%;
  min-height: clamp(42px, 5.4vh, 46px);
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #e9e8ef;
  background: #fcfcfe;
  color: #19182e;
  font: 400 13.5px 'Manrope', sans-serif;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.entry-dark .entry-field-label input {
  background: #25203b;
  border-color: rgba(196, 187, 213, 0.25);
  color: #f3f1fb;
}

.entry-field-label input::placeholder {
  color: #787788;
}

.entry-field-label input:focus {
  outline: none;
  border-color: #56288d;
  box-shadow: 0 0 0 3px rgba(86, 40, 141, 0.12);
}

.entry-forgot-row {
  margin: -4px 0 0;
}

.entry-forgot-btn {
  padding: 0;
  border: 0;
  background: none;
  font: 400 12px 'Manrope', sans-serif;
  color: var(--entry-muted);
  cursor: pointer;
  text-align: left;
}

.entry-forgot-btn:hover {
  color: #56288d;
  text-decoration: underline;
}

.entry-forgot-notice {
  margin: 0;
  padding: 10px 14px;
  border-radius: 12px;
  background: #f2f0fc;
  color: #56288d;
  font-size: 12.5px;
  line-height: 1.45;
}

.entry-roles {
  display: grid;
  gap: clamp(6px, 1vh, 9px);
  margin: clamp(8px, 1.4vh, 14px) 0;
}

.entry-roles button {
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  min-height: clamp(48px, 6.4vh, 60px);
  padding: clamp(7px, 1vh, 10px) 14px;
  border: 1px solid var(--entry-border);
  border-radius: 15px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.entry-roles button:hover {
  border-color: rgba(108, 106, 238, 0.36);
}

.entry-roles button.selected {
  background: rgba(108, 106, 238, 0.1);
  border-color: #6c6aee;
}

.entry-dark .entry-roles button:hover:not(.selected) {
  background: #25203b;
  border-color: rgba(164, 132, 233, 0.45);
}

.entry-dark .entry-roles button.selected {
  background: rgba(108, 106, 238, 0.22);
  border-color: #8f85f3;
}

.entry-dark .entry-roles button > span {
  background: rgba(108, 106, 238, 0.25);
  color: #c4b5fd;
}

.entry-dark .entry-roles button i {
  color: #c4b5fd;
}

.entry-roles button > span {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  background: rgba(108, 106, 238, 0.1);
  border-radius: 10px;
  color: #6c6aee;
}

.entry-roles button div {
  display: grid;
  gap: 2px;
  flex: 1;
}

.entry-roles strong {
  font-size: clamp(13.5px, 1.8vh, 15px);
  font-weight: 800;
  color: var(--entry-ink);
  line-height: 1.2;
}

.entry-roles small {
  font-size: 11.5px;
  font-weight: 400;
  color: var(--entry-muted);
  line-height: 1.3;
}

.entry-roles i {
  font-style: normal;
  font-size: 15px;
  font-weight: 700;
  color: #6c6aee;
}

.entry-login-actions {
  display: grid;
  gap: clamp(8px, 1.1vh, 11px);
  margin-top: clamp(8px, 1.4vh, 14px);
}

.entry-primary,
.entry-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-sizing: border-box;
  width: 100%;
  font-family: 'Manrope', sans-serif;
  font-size: 13.5px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: transform 0.12s ease, opacity 0.15s ease, box-shadow 0.15s ease;
}

.entry-primary {
  min-height: clamp(40px, 5.2vh, 46px);
  padding: clamp(8px, 1.1vh, 10px) 18px;
  border-radius: 24px;
  border: 1px solid #56288d;
  background: #56288d;
  color: #ffffff;
  box-shadow: 0 6px 16px rgba(86, 40, 141, 0.18);
}

.entry-primary:hover:not(:disabled) {
  background: #492079;
}

.entry-arrow {
  font-size: 15px;
  line-height: 1;
}

.entry-google,
.entry-primary.entry-google {
  min-height: clamp(40px, 5.2vh, 46px);
  padding: clamp(8px, 1.1vh, 10px) 18px;
  border-radius: 27px;
  background: #ffffff;
  color: #19182e;
  border: 1px solid #c4bbd5;
  box-shadow: 0 1px 3px rgba(25, 24, 46, 0.04);
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease, transform 0.12s ease;
}

.entry-google:hover:not(:disabled),
.entry-primary.entry-google:hover:not(:disabled) {
  background: #f5f2fd !important;
  border-color: #56288d !important;
  color: #56288d !important;
  box-shadow: 0 4px 14px rgba(86, 40, 141, 0.14) !important;
  transform: translateY(-1px);
}

.entry-google:active:not(:disabled),
.entry-primary.entry-google:active:not(:disabled) {
  background: #ede7fa !important;
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(86, 40, 141, 0.12) !important;
}

.entry-dark .entry-google,
.entry-dark .entry-primary.entry-google {
  background: #25203b;
  color: #f3f1fb;
  border-color: rgba(196, 187, 213, 0.28);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.entry-dark .entry-google:hover:not(:disabled),
.entry-dark .entry-primary.entry-google:hover:not(:disabled) {
  background: #312b4d !important;
  color: #ffffff !important;
  border-color: #8f85f3 !important;
  box-shadow: 0 4px 16px rgba(108, 106, 238, 0.25) !important;
  transform: translateY(-1px);
}

.entry-dark .entry-google:active:not(:disabled),
.entry-dark .entry-primary.entry-google:active:not(:disabled) {
  background: #282240 !important;
  transform: translateY(0);
}

.entry-google:disabled,
.entry-primary.entry-google:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.entry-google img {
  flex: none;
}

.entry-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: clamp(8px, 1.4vh, 14px) 0 clamp(6px, 1vh, 10px);
  color: var(--entry-muted);
}

.entry-divider::before,
.entry-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--entry-border);
}

.entry-divider span {
  font-size: 10.5px;
  font-weight: 400;
  letter-spacing: 0.08em;
  color: var(--entry-muted);
  text-transform: uppercase;
}

.entry-secondary {
  min-height: clamp(40px, 5.2vh, 44px);
  padding: clamp(8px, 1.1vh, 10px) 18px;
  border-radius: 12px;
  border: 1px solid var(--entry-border);
  background: transparent;
  color: var(--entry-ink);
  font-size: 12.5px;
  font-weight: 700;
}

.entry-secondary:hover {
  border-color: #6c6aee;
  background: rgba(108, 106, 238, 0.04);
}

.entry-dark .entry-secondary:hover {
  border-color: #8f85f3;
  background: rgba(108, 106, 238, 0.18);
  color: #ffffff;
}

.entry-primary:focus-visible,
.entry-secondary:focus-visible,
.entry-roles button:focus-visible {
  outline: 3px solid #ad99d3;
  outline-offset: 2px;
}

.entry-subtle {
  margin: clamp(6px, 1vh, 10px) 0 0;
  font-size: 11px !important;
  color: var(--entry-muted);
  line-height: 1.35;
}

.entry-bottom {
  margin: clamp(3px, 0.6vh, 6px) 0 0;
  font-size: 10.5px;
  color: var(--entry-muted);
  line-height: 1.35;
}

.entry-status {
  margin-top: 18px;
  padding: 14px 16px;
  display: flex;
  gap: 10px;
  border: 1px solid var(--entry-border);
  border-radius: 14px;
  font-size: 12px;
  color: var(--entry-muted);
  line-height: 1.5;
  background: #fcfcfe;
}

.entry-dark .entry-status {
  background: #231e38;
}

.entry-status p {
  margin: 4px 0;
}

.entry-status button {
  border: 0;
  background: none;
  padding: 0;
  text-decoration: underline;
  color: #56288d;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.status-dot {
  background: #c7a478;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.entry-checking {
  margin-top: 14px;
  font-size: 12px;
  color: var(--entry-muted);
}

.sisu-back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 18px;
  font-family: 'Manrope', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: #56288d;
  text-decoration: none;
  background: none;
  border: 0;
  padding: 0;
  cursor: pointer;
}

.sisu-back-link:hover {
  text-decoration: underline;
}

.entry-onboarding-lead {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--entry-muted);
  line-height: 1.5;
}

.entry-onboarding-meta {
  margin: 0 0 20px;
  padding: 10px 14px;
  border-radius: 12px;
  background: #f2f0fc;
  color: #56288d;
  font-size: 13px;
  display: inline-block;
}

.entry-onboarding-links {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid var(--entry-border);
}

.entry-onboarding-links a {
  font-size: 13px;
  font-weight: 700;
  color: #56288d;
  text-decoration: none;
}

.entry-onboarding-links a:hover {
  text-decoration: underline;
}

@media (max-width: 1040px) {
  .entry-layout,
  .sisu-onboarding-split {
    grid-template-columns: minmax(0, 1fr);
    max-width: 680px;
    gap: 20px;
  }

  .entry-card,
  .entry-onboarding {
    padding: 24px 20px;
  }
}

@media (max-width: 640px) {
  .sisu-entry,
  .sisu-onboarding-shell {
    justify-content: flex-start;
    padding: 12px 12px 24px;
  }

  .entry-layout,
  .sisu-onboarding-split {
    gap: 12px;
  }

  .entry-card,
  .entry-onboarding {
    padding: 20px;
    border-radius: 24px;
  }

  .entry-card h2,
  .entry-onboarding h1 {
    font-size: 28px;
    line-height: 1.18;
    margin: 0 0 8px;
  }

  .entry-signin-lead,
  .entry-onboarding-lead {
    font-size: 15px !important;
    line-height: 1.5;
    margin-bottom: 14px !important;
  }

  .entry-email-form {
    gap: 12px;
    margin-top: 12px;
  }

  .entry-field-label input {
    min-height: 48px;
    padding: 13px 14px;
    border-radius: 13px;
    font-size: 14px;
  }

  .entry-roles {
    gap: 10px;
    margin: 14px 0;
  }

  .entry-roles button {
    min-height: 68px;
    padding: 14px 16px;
    border-radius: 18px;
  }

  .entry-roles strong {
    font-size: 16px;
  }

  .entry-roles small {
    font-size: 13px;
  }

  .entry-login-actions {
    gap: 10px;
    margin-top: 14px;
  }

  .entry-primary,
  .entry-google,
  .entry-secondary {
    min-height: 48px;
    padding: 12px 18px;
  }

  .entry-primary {
    border-radius: 27px;
  }

  .entry-divider {
    margin: 16px 0 8px;
  }

  .sisu-back-link {
    margin-bottom: 12px;
  }
}

@media (max-width: 380px) {
  .entry-card,
  .entry-onboarding {
    padding: 16px;
  }

  .entry-card h2,
  .entry-onboarding h1 {
    font-size: 24px;
  }

  .entry-primary,
  .entry-google,
  .entry-secondary {
    font-size: 13px;
    padding: 10px 14px;
  }
}

@media (min-width: 1000px) {
  main.sisu-entry {
    padding: clamp(10px, 1.8vh, 20px) clamp(16px, 2.5vw, 28px);
  }

  main.sisu-entry > .entry-layout {
    max-width: 1180px;
    grid-template-columns: minmax(360px, 500px) minmax(0, 620px);
    gap: clamp(20px, 2.8vw, 40px);
    margin: 0 auto;
    align-items: center;
  }

  main.sisu-entry .entry-card-wrap .entry-card {
    padding: clamp(14px, 2.2vh, 28px) clamp(20px, 3vw, 36px);
  }

  main.sisu-entry .entry-card-wrap .entry-card h2 {
    font-size: clamp(26px, 3vh, 34px);
    line-height: 1.15;
    letter-spacing: -0.03em;
  }

  main.sisu-entry .entry-card-wrap .entry-card .entry-roles button {
    min-height: 60px;
    border-radius: 16px;
  }

  main.sisu-entry .entry-card-wrap .entry-card .entry-login-actions .entry-primary,
  main.sisu-entry .entry-card-wrap .entry-card .entry-login-actions .entry-google {
    border-radius: 27px;
  }
}
</style>
