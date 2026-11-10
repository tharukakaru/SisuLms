<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue'
import {request} from './client'
import './release.css'
import {ArrowRight} from 'lucide-vue-next'
defineProps({onboarding:Boolean})
const phone=ref(''),code=ref(''),channel=ref('SMS'),challenge=ref(null),verified=ref(false),error=ref(''),busy=ref(false),config=ref(null),cooldown=ref(0),expiry=ref(0)
const timer=setInterval(()=>{cooldown.value=Math.max(0,cooldown.value-1);expiry.value=Math.max(0,expiry.value-1)},1000)
onBeforeUnmount(()=>clearInterval(timer))
async function issue(){error.value='';busy.value=true;cooldown.value=60;try{const r=await request(channel.value==='SMS'?'mobile_verification':'private_contact',channel.value==='SMS'?'request_code':'request_whatsapp_code',{phone:phone.value});challenge.value=r.challenge;expiry.value=r.expires_in_seconds;code.value=''}catch(e){if(e.retryAfterSeconds){cooldown.value=e.retryAfterSeconds;error.value=''}else error.value=e.message}finally{busy.value=false}}
async function verify(){error.value='';busy.value=true;try{await request('mobile_verification','verify',{code:code.value,channel:channel.value,challenge:challenge.value});verified.value=true;code.value='';challenge.value=null}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(async()=>{try{config.value=await request('release','otp_status',{},'GET');verified.value=config.value.verified;if(!config.value.SMS&&config.value.WHATSAPP)channel.value='WHATSAPP'}catch(e){error.value=e.message}})
</script>
<template><section v-if="onboarding" class="onboarding-mobile">
  <h1>Let’s make this space yours.</h1><p class="verification-intro">Verify your mobile number to continue.</p>
  <p v-if="error" class="verification-feedback error" role="alert">{{error}}</p>
  <template v-if="verified"><p class="verification-feedback" role="status">Mobile verified.</p><button class="teacher-submit verification-secondary" @click="verified=false">Verify another number<ArrowRight :size="16" aria-hidden="true"/></button></template>
  <template v-else>
    <p v-if="config&&!config.SMS&&!config.WHATSAPP" class="verification-feedback">SMS and WhatsApp verification are not configured. Contact the administrator.</p>
    <form @submit.prevent="issue">
      <label>Mobile number<input v-model="phone" type="tel" required pattern="\+[1-9][0-9]{7,14}" placeholder="+94" :disabled="busy||cooldown>0"></label>
      <button class="teacher-submit" :disabled="busy||cooldown>0||!config?.[channel]">{{cooldown?'Try again in '+String(Math.floor(cooldown/60)).padStart(2,'0')+':'+String(cooldown%60).padStart(2,'0'):busy?'Sending…':'Send verification code'}}<ArrowRight :size="16" aria-hidden="true"/></button>
    </form>
    <form class="verification-phone-form" @submit.prevent="verify">
      <label>Verification code<input v-model="code" :disabled="!challenge||busy" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="Six-digit code" required></label>
      <button class="teacher-submit verification-secondary" :disabled="busy||!challenge||!expiry">Verify number<ArrowRight :size="16" aria-hidden="true"/></button>
      <p v-if="challenge" class="verification-feedback" role="status">Code expires in {{expiry}} seconds. Failed attempts are limited by the server.</p>
    </form>
    <details class="verification-channel"><summary>Verification method · {{channel}}</summary><label>Channel<select v-model="channel" :disabled="busy||cooldown>0" @change="challenge=null;code='' "><option :disabled="!config?.SMS">SMS</option><option :disabled="!config?.WHATSAPP">WHATSAPP</option></select></label></details>
  </template>
</section><section v-else class="release panel"><h2>Verify your mobile</h2><p v-if="error" class="error" role="alert">{{error}}</p><p v-if="verified" role="status">Mobile verified.</p><button v-if="verified" class="button subtle" @click="verified=false">Verify another number</button><template v-else><p v-if="config&&!config.SMS&&!config.WHATSAPP">SMS and WhatsApp verification are not configured. Contact the administrator.</p><form @submit.prevent="issue"><label>Channel<select v-model="channel" :disabled="busy||cooldown>0" @change="challenge=null;code='' "><option :disabled="!config?.SMS">SMS</option><option :disabled="!config?.WHATSAPP">WHATSAPP</option></select></label><label>Mobile number<input v-model="phone" type="tel" required pattern="\+[1-9][0-9]{7,14}" placeholder="+94…" :disabled="busy||cooldown>0"></label><button class="button subtle" :disabled="busy||cooldown>0||!config?.[channel]">{{cooldown?'Try again in '+String(Math.floor(cooldown/60)).padStart(2,'0')+':'+String(cooldown%60).padStart(2,'0'):'Send verification code'}}</button></form><form v-if="challenge" @submit.prevent="verify"><p>Code expires in {{expiry}} seconds. Failed attempts are limited by the server.</p><label>Six-digit code<input v-model="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" required></label><button class="button primary" :disabled="busy||!expiry">Verify</button></form></template></section></template>
