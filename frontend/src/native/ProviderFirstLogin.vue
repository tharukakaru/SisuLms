<script setup>
import {ref,nextTick} from 'vue'
import BrandLogo from '../BrandLogo.vue'
import MobileVerification from './MobileVerification.vue'
import ProviderProfileSetup from './ProviderProfileSetup.vue'
import InstituteJoinPicker from './InstituteJoinPicker.vue'
import {csrf,decode} from './client'
const props=defineProps({session:Object})
const confirmation=ref(null)
async function completed(){saved.value=true;await nextTick();confirmation.value?.showModal()}
const verified=ref(false),saved=ref(false),busy=ref(false),error=ref('')
async function login(){
 if(!verified.value||!saved.value||busy.value)return
 busy.value=true;error.value=''
 try{await decode(await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf()}}));location.assign('/login?redirect-to=/campus')}
 catch(e){error.value=e.message;busy.value=false}
}
</script>
<template><main class="first-login"><BrandLogo/><h1>Let’s make this space yours.</h1><p>Complete these steps once to set up your account.</p>
<MobileVerification v-if="!verified" onboarding hide-heading @verified="verified=$event"/>
<ProviderProfileSetup v-if="verified&&!saved" :member="{user:session.user,full_name:session.user,role:session.onboarding_kind==='Institute'?'Admin':'Teacher'}" @completed="completed"/>
<dialog ref="confirmation" class="saved-dialog" aria-labelledby="saved-title" @cancel.prevent><h2 id="saved-title">Profile details saved successfully</h2><p>Your information is saved securely.</p><button v-if="session.teaching_path==='institute'" class="continue" @click="confirmation.close()">Continue to institute selection</button><button v-else class="continue" :disabled="busy" @click="login">Back to sign in</button><p v-if="error" role="alert">{{error}}</p></dialog>
<section v-if="verified&&saved" class="success" role="status" aria-live="polite"><h2>Profile details saved successfully</h2><p>Your profile and mobile number are saved.{{session.teaching_path==='institute'?' Choose your institutes below.':' You can return to login now.'}}</p></section>
<InstituteJoinPicker v-if="verified&&saved&&session.teaching_path==='institute'" purpose="New application" onboarding/>
<button v-else class="continue" :disabled="!verified||!saved||busy" @click="login">{{busy?'Returning to login…':'Back to login'}}</button>
<p v-if="error" role="alert">{{error}}</p></main></template>
<style scoped>.first-login{max-width:960px;margin:40px auto;padding:24px;font-family:'Manrope Variable',sans-serif;color:#211b31}.first-login>p{color:#787087}.success{background:#ecf8ef;color:#24633d;border:1px solid #c7e6d1;border-radius:16px;padding:22px;margin:24px 0}.continue{background:#56288d;color:white;border:0;border-radius:32px;padding:18px 30px;font-family:inherit;font-size:15px;font-weight:600;margin:24px 0;cursor:pointer}.continue:disabled{opacity:.45;cursor:not-allowed}</style>

<style scoped>.saved-dialog{position:fixed;inset:0;margin:auto;width:min(440px,calc(100vw - 40px));box-sizing:border-box;padding:30px;border:1px solid #c7e6d1;border-radius:20px;background:#effaf3;color:#24633d}.saved-dialog::backdrop{background:#211b3166}.saved-dialog h2{font-size:23px}.saved-dialog p{line-height:1.7}</style>
