<script setup>
import {computed,onMounted,ref} from 'vue'
import BrandLogo from '../BrandLogo.vue'
import ProviderProfileSetup from './ProviderProfileSetup.vue'
import {request} from './client'

const props=defineProps({session:Object})
const emit=defineEmits(['changed'])
const profile=ref(null),busy=ref(false),error=ref(''),editing=ref(false)
const heading=computed(()=>profile.value?.status==='Rejected'?'Your profile needs an update':profile.value?.status==='Verified'?'Your workspace is being set up':'Your profile is awaiting review')
async function load(){
  busy.value=true;error.value=''
  try{profile.value=(await request('profiles','me',{},'GET')).profile}
  catch(e){error.value=e.message}
  finally{busy.value=false}
}
async function refresh(){await load();emit('changed')}
async function saved(){editing.value=false;await refresh()}
onMounted(load)
</script>

<template>
  <main class="onboarding-status">
    <header><BrandLogo/><a href="/api/method/logout">Sign out</a></header>
    <ProviderProfileSetup v-if="editing" :member="{user:session.user,role:session.onboarding_kind==='Institute'?'Admin':'Teacher'}" @completed="saved"/>
    <section v-else aria-labelledby="onboarding-status-title" :aria-busy="busy">
      <p v-if="busy&&!profile" role="status">Checking your saved profile…</p>
      <template v-if="profile">
        <h1 id="onboarding-status-title">{{heading}}</h1>
        <p>Your profile and mobile verification are saved. You don’t need to complete onboarding again.</p>
        <p v-if="profile.status==='Pending'">SISU needs to review your profile before your workspace can be opened. Check here again for an update.</p>
        <p v-else-if="profile.status==='Rejected'">Review the feedback below and update your details.</p>
        <p v-else>Your profile is verified. If your workspace is still unavailable after checking again, contact SISU support.</p>
        <p v-if="profile.review_reason" class="review-feedback">{{profile.review_reason}}</p>
        <dl><dt>Name</dt><dd>{{profile.display_name}}</dd><dt>Username</dt><dd>@{{profile.username}}</dd><dt>Profile status</dt><dd>{{profile.status}}</dd></dl>
      </template>
      <p v-if="error" role="alert">{{error}}</p>
      <div class="status-actions">
        <button type="button" class="primary" :disabled="busy" @click="refresh">{{busy?'Checking…':'Check status'}}</button>
        <button v-if="profile" type="button" :disabled="busy" @click="editing=true">Review profile details</button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.onboarding-status{max-width:960px;margin:auto;padding:32px 24px;font-family:'Manrope Variable',sans-serif;color:#211b31}
header{display:flex;align-items:center;justify-content:space-between;gap:24px}header a{color:#56288d;text-underline-offset:4px}
section{max-width:640px;margin:64px auto}h1{font-size:clamp(26px,4vw,36px);line-height:1.25;margin:0 0 20px;text-wrap:balance}
p{font-size:16px;line-height:1.75;color:#62566e}dl{display:grid;grid-template-columns:110px minmax(0,1fr);gap:16px;margin:28px 0;padding:24px 0;border-block:1px solid #e7e1ee}dt{color:#62566e}dd{margin:0;overflow-wrap:anywhere}
.status-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}button{min-height:48px;padding:12px 20px;border:1px solid #d5c9e3;border-radius:12px;background:#fff;color:#56288d;font:inherit;font-weight:600;cursor:pointer}button.primary{background:#56288d;border-color:#56288d;color:#fff}button:hover{background:#f5f0fa}button.primary:hover{background:#442071}button:disabled{opacity:.6;cursor:wait}button:focus-visible,a:focus-visible{outline:3px solid #aa88ce;outline-offset:4px}[role=alert]{color:#a52642}.review-feedback{padding:16px;background:#f8f5fc;border-radius:12px}
@media(max-width:600px){section{margin-top:40px}.status-actions{flex-direction:column}.status-actions button{width:100%}}
</style>
