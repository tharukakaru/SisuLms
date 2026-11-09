<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue'
import {request} from './client'
const emit=defineEmits(['close']),dialog=ref(null),token=ref(''),email=ref(''),verified=ref(false),busy=ref(false),error=ref(''),password=ref(''),confirmation=ref(''),done=ref(false),seconds=ref(0)
let poll
async function start(){busy.value=true;error.value='';try{const r=await request('password_reset','start');token.value=r.token;email.value=r.email;seconds.value=r.expires_in;poll=setInterval(check,4000)}catch(e){error.value=e.message}finally{busy.value=false}}
async function check(){if(!token.value||busy.value||done.value||verified.value)return;try{const r=await request('password_reset','status',{token:token.value},'GET');verified.value=r.verified;seconds.value=r.expires_in;if(r.verified)clearInterval(poll)}catch(e){clearInterval(poll);error.value=e.message}}
async function save(){busy.value=true;error.value='';try{await request('password_reset','finish',{token:token.value,password:password.value,confirmation:confirmation.value});password.value='';confirmation.value='';done.value=true;clearInterval(poll)}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(()=>dialog.value.showModal());onBeforeUnmount(()=>{clearInterval(poll);dialog.value?.close()})
</script>
<template>
  <dialog ref="dialog" class="password-dialog" aria-labelledby="password-reset-title" @cancel.prevent="!busy&&emit('close')">
    <button type="button" class="close-reset" aria-label="Close password reset" :disabled="busy" @click="emit('close')">×</button>
    <h2 id="password-reset-title">{{done?'Password updated':'Reset your password'}}</h2>
    <p v-if="error" class="reset-error" role="alert">{{error}}</p>
    <section v-if="done">
      <p>Your new password is saved. A security confirmation is queued for your email and verified mobile. Please sign in again.</p>
      <a class="button primary reset-pill-primary" href="/campus">Return to sign in →</a>
    </section>
    <section v-else-if="!token">
      <p>First, let’s confirm it’s you. We’ll send a secure link to the email address on your signed-in account.</p>
      <button type="button" class="button primary reset-pill-primary" :disabled="busy" @click="start">{{busy?'Sending…':'Send confirmation email →'}}</button>
    </section>
    <section v-else-if="!verified">
      <p class="reset-notice">Open the confirmation email sent to <strong>{{email}}</strong> and select Confirm password reset.</p>
      <p>Keep this tab open. Your new-password form will appear here after confirmation. The link lasts 10 minutes.</p>
      <button type="button" class="button subtle reset-pill-secondary" @click="check">I’ve confirmed — check now →</button>
    </section>
    <form v-else @submit.prevent="save">
      <p class="reset-notice">Email confirmed. Choose your new password.</p>
      <label>New password
        <input v-model="password" type="password" autocomplete="new-password" minlength="12" maxlength="128" required placeholder="At least 12 characters">
      </label>
      <label>Confirm new password
        <input v-model="confirmation" type="password" autocomplete="new-password" minlength="12" maxlength="128" required placeholder="Repeat password">
      </label>
      <p class="reset-hint">Use 12–128 characters. Both passwords must match.</p>
      <button type="submit" class="button primary reset-pill-primary" :disabled="busy||password.length<12||password!==confirmation">{{busy?'Saving…':'Save new password →'}}</button>
    </form>
  </dialog>
</template>
<style scoped>
.password-dialog {
  position: fixed;
  inset: 0;
  margin: auto;
  width: min(540px, calc(100vw - 32px));
  padding: 36px 32px;
  border: 1px solid #e9e8ef;
  border-radius: 28px;
  color: #19182e;
  background: #ffffff;
  max-height: 90vh;
  overflow: auto;
  font-family: 'Manrope', Inter, system-ui, sans-serif;
  box-shadow: 0 24px 64px rgba(25, 24, 46, 0.18);
}

.password-dialog::backdrop {
  background: rgba(25, 24, 46, 0.48);
  backdrop-filter: blur(4px);
}

.password-dialog h2 {
  margin: 0 0 12px;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #19182e;
}

.password-dialog p {
  font-size: 14px;
  color: #787788;
  line-height: 1.6;
  margin: 14px 0;
}

.password-dialog label {
  display: grid;
  gap: 8px;
  margin: 14px 0;
  font-size: 13px;
  font-weight: 600;
  color: #19182e;
}

.password-dialog input {
  min-height: 50px;
  padding: 13px 14px;
  border: 1px solid #e9e8ef;
  border-radius: 13px;
  background: #fcfcfe;
  color: #19182e;
  font: 400 14px 'Manrope', sans-serif;
  box-sizing: border-box;
  width: 100%;
}

.password-dialog input:focus {
  outline: none;
  border-color: #56288d;
  box-shadow: 0 0 0 3px rgba(86, 40, 141, 0.12);
}

.close-reset {
  position: absolute;
  right: 18px;
  top: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f2f0fc;
  color: #56288d;
  border: 0;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.reset-notice {
  padding: 16px;
  background: #eff8f2;
  border: 1px solid #cddfd4;
  border-radius: 16px;
  color: #24543b !important;
}

.reset-error {
  padding: 12px 16px;
  border-radius: 13px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b !important;
}

.reset-pill-primary,
.reset-pill-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 54px;
  padding: 12px 22px;
  border-radius: 27px;
  font: 700 14px 'Manrope', sans-serif;
  text-decoration: none;
  cursor: pointer;
  box-sizing: border-box;
}

.reset-pill-primary {
  background: #56288d;
  border: 1px solid #56288d;
  color: #ffffff;
}

.reset-pill-secondary {
  background: #f2f0fc;
  border: 1px solid #f2f0fc;
  color: #19182e;
}

@media (max-width: 640px) {
  .password-dialog {
    width: calc(100vw - 24px);
    max-height: calc(100dvh - 24px);
    padding: 24px 20px;
    border-radius: 24px;
  }

  .password-dialog h2 {
    font-size: 24px;
    margin: 0 32px 10px 0;
  }

  .password-dialog input {
    min-height: 48px;
    padding: 13px 14px;
    border-radius: 13px;
  }

  .reset-pill-primary,
  .reset-pill-secondary {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }
}
</style>
