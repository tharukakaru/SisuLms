<script setup>
import {ref} from 'vue'
import OnboardingWelcomePanel from './OnboardingWelcomePanel.vue'
import {request} from './client'
const parts=location.hash.replace('#password-confirm=','').split('.'),done=ref(false),busy=ref(false),error=ref('')
history.replaceState(null,'',location.pathname)
async function confirm(){busy.value=true;error.value='';try{await request('password_reset','confirm',{token:parts[0],proof:parts[1]});done.value=true}catch(e){error.value=e.message}finally{busy.value=false}}
</script>
<template>
  <main class="confirmation-shell">
    <div class="confirmation-split">
      <OnboardingWelcomePanel variant="grow" />
      <section class="confirmation-page">
        <a class="sisu-back-link" href="/campus">← Back to sign in</a>
        <h1>{{done?'Email confirmed':'Confirm your password reset'}}</h1>
        <p v-if="done">You can close this tab and return to the SISU Settings tab where you requested the reset. Choose and save your new password there.</p>
        <template v-else>
          <p>Only confirm if you requested a password reset from your SISU account.</p>
          <button type="button" :disabled="busy" @click="confirm">
            <span>{{busy?'Confirming…':'Confirm password reset'}}</span>
            <span aria-hidden="true">→</span>
          </button>
        </template>
        <p v-if="error" class="confirmation-error" role="alert">{{error}}</p>
      </section>
    </div>
  </main>
</template>
<style scoped>
.confirmation-shell {
  min-height: 100vh;
  min-height: 100dvh;
  padding: clamp(16px, 2vw, 24px);
  background: #ffffff;
  color: #19182e;
  font-family: 'Manrope', Inter, system-ui, sans-serif;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.confirmation-split {
  display: grid;
  grid-template-columns: minmax(360px, 500px) minmax(0, 620px);
  gap: clamp(20px, 2.8vw, 40px);
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  align-items: center;
}

.confirmation-page {
  max-width: 620px;
  padding: clamp(14px, 2.2vh, 28px) clamp(20px, 3vw, 36px);
  border-radius: 24px;
  background: #ffffff;
  color: #19182e;
  box-sizing: border-box;
}

.sisu-back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: clamp(8px, 1.2vh, 14px);
  font-size: 12.5px;
  font-weight: 500;
  color: #56288d;
  text-decoration: none;
}

.sisu-back-link:hover {
  text-decoration: underline;
}

.confirmation-page h1 {
  margin: 0 0 clamp(6px, 0.9vh, 10px);
  font: 800 clamp(22px, 3vh, 30px)/1.15 'Manrope', sans-serif;
  letter-spacing: -0.03em;
  color: #19182e;
}

.confirmation-page p {
  margin: 0 0 clamp(12px, 1.8vh, 18px);
  font-size: 13.5px;
  color: #787788;
  line-height: 1.45;
}

.confirmation-page button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  min-height: clamp(42px, 5.4vh, 48px);
  padding: 10px 20px;
  border: 1px solid #56288d;
  border-radius: 24px;
  color: #ffffff;
  background: #56288d;
  font: 700 13.5px 'Manrope', sans-serif;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(86, 40, 141, 0.16);
}

.confirmation-page button:hover:not(:disabled) {
  background: #472074;
}

.confirmation-page button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.confirmation-error {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 13px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b !important;
  font-size: 13px !important;
}

@media (max-width: 1040px) {
  .confirmation-split {
    grid-template-columns: minmax(0, 1fr);
    max-width: 680px;
    gap: 20px;
  }

  .confirmation-page {
    padding: 24px 20px;
  }
}

@media (max-width: 640px) {
  .confirmation-shell {
    justify-content: flex-start;
    padding: 12px 12px 24px;
  }

  .confirmation-split {
    gap: 12px;
  }

  .confirmation-page {
    padding: 20px;
    border-radius: 24px;
  }

  .sisu-back-link {
    margin-bottom: 12px;
  }

  .confirmation-page h1 {
    font-size: 28px;
    line-height: 1.18;
    margin: 0 0 8px;
  }

  .confirmation-page p {
    font-size: 15px;
    margin: 0 0 16px;
  }

  .confirmation-page button {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }
}
</style>
