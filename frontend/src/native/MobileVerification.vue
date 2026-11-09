<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue'
import {request} from './client'
import './release.css'
const phone=ref(''),code=ref(''),channel=ref('SMS'),challenge=ref(null),verified=ref(false),error=ref(''),busy=ref(false),config=ref(null),cooldown=ref(0),expiry=ref(0)
const timer=setInterval(()=>{cooldown.value=Math.max(0,cooldown.value-1);expiry.value=Math.max(0,expiry.value-1)},1000)
onBeforeUnmount(()=>clearInterval(timer))
async function issue(){error.value='';busy.value=true;cooldown.value=60;try{const r=await request(channel.value==='SMS'?'mobile_verification':'private_contact',channel.value==='SMS'?'request_code':'request_whatsapp_code',{phone:phone.value});challenge.value=r.challenge;expiry.value=r.expires_in_seconds;code.value=''}catch(e){if(e.retryAfterSeconds){cooldown.value=e.retryAfterSeconds;error.value=''}else error.value=e.message}finally{busy.value=false}}
async function verify(){error.value='';busy.value=true;try{await request('mobile_verification','verify',{code:code.value,channel:channel.value,challenge:challenge.value});verified.value=true;code.value='';challenge.value=null}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(async()=>{try{config.value=await request('release','otp_status',{},'GET');verified.value=config.value.verified;if(!config.value.SMS&&config.value.WHATSAPP)channel.value='WHATSAPP'}catch(e){error.value=e.message}})
</script>
<template>
  <section class="release panel sisu-mobile-verify">
    <div class="sisu-mobile-verify-head">
      <h2>Verify your mobile</h2>
      <p>Verify your mobile number to continue.</p>
    </div>

    <p v-if="error" class="error sisu-mobile-error" role="alert">{{error}}</p>
    <p v-if="verified" class="sisu-mobile-verified" role="status">Mobile verified.</p>
    <button v-if="verified" type="button" class="button subtle sisu-pill-secondary-btn" @click="verified=false">
      <span>Verify another number</span>
      <span class="sisu-purple-arrow" aria-hidden="true">→</span>
    </button>

    <template v-else>
      <p v-if="config&&!config.SMS&&!config.WHATSAPP" class="sisu-mobile-unconfigured">SMS and WhatsApp verification are not configured. Contact the administrator.</p>

      <form class="sisu-mobile-form" @submit.prevent="issue">
        <label>Channel
          <select v-model="channel" :disabled="busy||cooldown>0" @change="challenge=null;code=''">
            <option :disabled="!config?.SMS">SMS</option>
            <option :disabled="!config?.WHATSAPP">WHATSAPP</option>
          </select>
        </label>
        <label>Mobile number
          <input v-model="phone" type="tel" required pattern="\+[1-9][0-9]{7,14}" placeholder="+94" :disabled="busy||cooldown>0">
        </label>
        <button type="submit" class="button subtle sisu-pill-primary-btn" :disabled="busy||cooldown>0||!config?.[channel]">
          <span>{{cooldown?'Try again in '+String(Math.floor(cooldown/60)).padStart(2,'0')+':'+String(cooldown%60).padStart(2,'0'):'Send verification code'}}</span>
          <span aria-hidden="true">→</span>
        </button>
      </form>

      <form v-if="challenge" class="sisu-mobile-form sisu-mobile-code-form" @submit.prevent="verify">
        <p class="sisu-mobile-expiry">Code expires in {{expiry}} seconds. Failed attempts are limited by the server.</p>
        <label>Verification code
          <input v-model="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" required placeholder="Six-digit code">
        </label>
        <button type="submit" class="button primary sisu-pill-secondary-btn" :disabled="busy||!expiry">
          <span>Verify number</span>
          <span class="sisu-purple-arrow" aria-hidden="true">→</span>
        </button>
      </form>
    </template>
  </section>
</template>
<style scoped>
.sisu-mobile-verify {
  margin: 18px 0;
  padding: 24px;
  border-radius: 22px;
  background: #fcfcfe;
  border: 1px solid #e9e8ef;
  font-family: 'Manrope', Inter, system-ui, sans-serif;
}

.sisu-mobile-verify-head h2 {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 800;
  color: #19182e;
}

.sisu-mobile-verify-head p {
  margin: 0 0 16px;
  font-size: 14px;
  color: #787788;
}

.sisu-mobile-form {
  display: grid;
  gap: 14px;
}

.sisu-mobile-code-form {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid #e9e8ef;
}

.sisu-mobile-form label {
  display: grid;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #19182e;
  margin: 0;
}

.sisu-mobile-form input,
.sisu-mobile-form select {
  box-sizing: border-box;
  width: 100%;
  min-height: 50px;
  padding: 13px 14px;
  border: 1px solid #e9e8ef;
  border-radius: 13px;
  background: #ffffff;
  color: #19182e;
  font: 400 14px 'Manrope', sans-serif;
}

.sisu-mobile-form input:focus,
.sisu-mobile-form select:focus {
  outline: none;
  border-color: #56288d;
  box-shadow: 0 0 0 3px rgba(86, 40, 141, 0.12);
}

.sisu-pill-primary-btn,
.sisu-pill-secondary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  min-height: 54px;
  padding: 12px 22px;
  border-radius: 27px;
  font: 700 14px 'Manrope', sans-serif;
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.sisu-pill-primary-btn {
  background: #56288d;
  border: 1px solid #56288d;
  color: #ffffff;
}

.sisu-pill-primary-btn:hover:not(:disabled) {
  background: #472074;
}

.sisu-pill-secondary-btn {
  background: #f2f0fc;
  border: 1px solid #f2f0fc;
  color: #19182e;
}

.sisu-pill-secondary-btn:hover:not(:disabled) {
  background: #e6e1f9;
}

.sisu-pill-primary-btn:disabled,
.sisu-pill-secondary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.sisu-purple-arrow {
  color: #56288d;
}

.sisu-mobile-expiry {
  margin: 0;
  font-size: 12px;
  color: #787788;
}

.sisu-mobile-verified {
  margin: 0 0 12px;
  padding: 12px 16px;
  border-radius: 13px;
  background: #eff8f2;
  border: 1px solid #cddfd4;
  color: #24543b;
  font-size: 13px;
  font-weight: 600;
}

.sisu-mobile-error {
  margin: 0 0 12px;
  padding: 12px 16px;
  border-radius: 13px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 13px;
}

@media (max-width: 640px) {
  .sisu-mobile-verify {
    margin: 14px 0;
    padding: 18px 16px;
    border-radius: 20px;
  }

  .sisu-mobile-verify-head h2 {
    font-size: 20px;
  }

  .sisu-mobile-form {
    gap: 10px;
  }

  .sisu-mobile-form input,
  .sisu-mobile-form select {
    min-height: 48px;
    padding: 13px 14px;
    border-radius: 13px;
  }

  .sisu-pill-primary-btn,
  .sisu-pill-secondary-btn {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }
}
</style>
