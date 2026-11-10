<script setup>
import {computed,ref,nextTick,onMounted,onUnmounted} from 'vue'
import GoogleIcon from '../GoogleIcon.vue'
import OnboardingWelcomePanel from './OnboardingWelcomePanel.vue'
import {request,csrf} from './client'
const props=defineProps({policy:Object,googleSession:Boolean});const emit=defineEmits(['back','verified','dashboard'])
const form=ref({kind:'Student',first_name:'',last_name:'',email:'',phone:'',username:'',country:'',timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,grade:'',subject:'',organization:'',job:'',backup_name:'',backup_email:'',website:'',qualifications:'',bio:'',privacy_accepted:false})
const extra=computed(()=>form.value.kind==='Student'?['grade']:form.value.kind==='Individual Teacher'?['subject']:['organization','job','backup_name','backup_email'])
const required=computed(()=>['first_name','last_name','email','phone','username','country','timezone',...extra.value])
const label=f=>({first_name:'First name',last_name:'Last name',backup_email:'Recovery contact email',backup_name:'Recovery contact name',job:'Your position',grade:'Grade / study level',subject:'Subject / expertise',organization:'Institute name'}[f]||f.replaceAll('_',' ').replace(/^./,s=>s.toUpperCase()))
const feedback=ref(null),status=ref('')
const cooldownKey='sisu-verification-5m-retry-until'
const now=ref(Date.now()),retryUntil=ref(0)
try{const saved=Number(sessionStorage.getItem(cooldownKey));if(saved>now.value&&saved<now.value+7200000)retryUntil.value=saved}catch{}
const remaining=computed(()=>Math.max(0,Math.ceil((retryUntil.value-now.value)/1000)))
const countdown=computed(()=>`${String(Math.floor(remaining.value/60)).padStart(2,'0')}:${String(remaining.value%60).padStart(2,'0')}`)
const timer=setInterval(()=>{now.value=Date.now()},1000)
onUnmounted(()=>clearInterval(timer))
function cooldown(seconds){retryUntil.value=Date.now()+seconds*1000;now.value=Date.now();try{sessionStorage.setItem(cooldownKey,String(retryUntil.value))}catch{}}
const token=ref(''),emailCode=ref(''),phoneCode=ref(''),emailOK=ref(false),phoneOK=ref(false),phoneSent=ref(false),password=ref(''),confirmation=ref(''),busy=ref(false),error=ref(''),done=ref(false)
const saveHint=computed(()=>!emailOK.value?'Verify your email to continue.':!phoneOK.value?'Verify your mobile number to continue.':password.value.length<12?'Email and phone verified. Choose a password of at least 12 characters.':password.value!==confirmation.value?'Email and phone verified. Your two passwords must match.':'Email and phone verified. Your passwords match — ready to save.');
const welcomeVariant=computed(()=>{
  if(token.value||done.value)return 'grow'
  return form.value.kind==='Student'?'discover':'connect'
})
function google(){sessionStorage.setItem('sisu_signup_role',form.value.kind);run(async()=>{const r=await request('portal_policy','google_start',{signup:1});const u=new URL(r.url);if(u.protocol!=='https:'||u.hostname!=='accounts.google.com')throw Error('Google sign-in unavailable');location.assign(u.href)})}
{const role=sessionStorage.getItem('sisu_signup_role');if(['Student','Individual Teacher','Institute'].includes(role))form.value.kind=role}
async function reveal(){await nextTick();feedback.value?.scrollIntoView({behavior:'smooth',block:'center'});feedback.value?.focus({preventScroll:true})}
function invalid(event){error.value='Please complete '+(event.target.getAttribute('aria-label')||'the highlighted required field')+'. '+event.target.validationMessage;reveal()}
async function run(fn){if(busy.value)return;busy.value=true;error.value='';status.value='Working…';try{await fn()}catch(e){if(e.retryAfterSeconds){cooldown(e.retryAfterSeconds);error.value='';status.value=''}else{error.value=e.message;status.value=''}}finally{busy.value=false;reveal()}}
function start(){run(async()=>{const r=await request('registration','self_start',{data:{...form.value,privacy_policy_version:props.policy.privacy_policy_version}});token.value=r.challenge;status.value='Email code requested. Check your inbox and enter it below.'})}
function verify(channel){run(async()=>{await request('registration','self_verify',{token:token.value,channel,code:channel==='email'?emailCode.value:phoneCode.value});if(channel==='email')emailOK.value=true;else phoneOK.value=true;status.value=channel==='email'?'Email verified. Request your phone code next.':'Phone verified. Set your password and save.'})}
function phone(){run(async()=>{await request('registration','self_phone',{token:token.value});phoneSent.value=true;status.value='Phone code requested. Enter the SMS code below.'})}
function save(){run(async()=>{await request('registration','self_complete',{token:token.value,password:password.value,confirmation:confirmation.value});password.value='';confirmation.value='';if(props.googleSession){const out=await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf()}});if(!out.ok)throw Error('Your account is saved. Sign out, then sign in again.')}location.replace('/campus')})}
function reset(){token.value='';emailOK.value=false;phoneOK.value=false;phoneSent.value=false;emailCode.value='';phoneCode.value='';password.value='';confirmation.value=''}
onMounted(()=>{if(props.googleSession)run(async()=>{const d=await request('registration','self_google_details',{},'GET');Object.assign(form.value,d);status.value='Google details filled in. Complete the remaining required fields.'})})
</script>
<template>
  <main class="verified-signup-shell">
    <div class="verified-signup-split">
      <OnboardingWelcomePanel :variant="welcomeVariant" />

      <div class="verified-signup">
        <button type="button" class="sisu-back-link" @click="emit('back')">← Back to sign in</button>
        <h1>{{token ? 'A little check, just for you.' : 'Create your SISU account'}}</h1>
        <p class="verified-lead">{{token ? 'Verify your email and mobile number, then choose your password.' : 'Your next chapter starts here.'}}</p>

        <button v-if="!googleSession&&!token&&!done" type="button" class="google-signup" :disabled="busy||!policy.google_available" @click="google">
          <GoogleIcon />
          <span>Sign up with Google</span>
          <span class="google-arrow" aria-hidden="true">→</span>
        </button>
        <p v-if="!googleSession&&!policy.google_available" class="google-note">Google signup is not available yet. You can create your account using email below.</p>
        <p v-if="googleSession" class="google-note">Google sign-in completed. Confirm your email and mobile number, then save your profile. Choose and confirm your password. After saving, you’ll return to the sign-in page.</p>

        <div ref="feedback" tabindex="-1" aria-live="polite" class="signup-feedback">
          <p v-if="remaining" class="cooldown" role="status">You’ve reached the code request limit. Try again in <strong>{{countdown}}</strong>. You can still verify a code you already received.</p>
          <p v-else-if="retryUntil" class="cooldown">00:00 — You can request a code again.</p>
          <p v-if="error" role="alert" class="error">{{error}}</p>
          <p v-else-if="status" class="verification-notice" role="status">{{status}}</p>
        </div>

        <section v-if="done" class="verified-step-card" role="status">
          <h2>Account created successfully</h2>
          <p>Your details have been saved. Please sign in with your email and password.</p>
          <button class="button primary" @click="emit('back')">Go to sign in →</button>
        </section>

        <form v-else @invalid.capture="invalid" @submit.prevent="token?save():start()">
          <fieldset :disabled="busy||!!token">
            <label>Account type · Required
              <select v-model="form.kind">
                <option>Student</option>
                <option>Individual Teacher</option>
                <option>Institute</option>
              </select>
            </label>
            <div class="signup-grid">
              <label v-for="field in required" :key="field">{{label(field)}} · Required
                <input
                  v-model="form[field]"
                  :aria-label="label(field)"
                  :readonly="googleSession&&field==='email'"
                  :type="field.includes('email')?'email':field==='phone'?'tel':'text'"
                  required
                  :maxlength="field.includes('name')?60:254"
                  :pattern="field==='username'?'[a-z][a-z0-9_]{2,29}':undefined"
                  :title="field==='username'?'Use 3–30 lowercase letters, digits or underscores; start with a letter.':undefined"
                  :placeholder="field==='phone'?'+94761234567':field==='username'?'e.g. sisu_student':''"
                />
              </label>
              <p class="phone-help">Sri Lankan mobile: use +94 and omit the first 0. For example, 0761234567 → +94761234567. Use a mobile number you can receive verification codes on.</p>
              <label v-for="field in ['website','qualifications','bio']" :key="field">{{label(field)}} · Optional
                <input
                  v-model="form[field]"
                  :aria-label="label(field)"
                  :readonly="googleSession&&field==='email'"
                  :type="field==='website'?'url':'text'"
                  maxlength="500"
                />
              </label>
            </div>
            <label class="consent">
              <input type="checkbox" v-model="form.privacy_accepted" aria-label="privacy policy acceptance" required/>
              <span>I accept the <a :href="policy.privacy_policy_url" target="_blank" rel="noopener noreferrer">privacy policy</a>.</span>
            </label>
          </fieldset>

          <p v-if="form.kind!=='Student'" class="provider-lock-note">Your teaching workspace stays locked until your plan payment is verified. Account verification does not grant a provider endorsement badge.</p>

          <button v-if="!token" class="button primary" :disabled="busy||remaining>0||!policy.privacy_policy_url">
            <span>{{busy?'Sending…':'Send email verification code'}}</span>
            <span aria-hidden="true">→</span>
          </button>

          <template v-else>
            <button type="button" class="button secondary-pill" :disabled="busy" @click="reset">Edit details / start again</button>

            <section class="verified-step-card">
              <h2>Email verification {{emailOK?'✓':''}}</h2>
              <label v-if="!emailOK">Six-digit email code
                <input v-model="emailCode" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="Six-digit code"/>
              </label>
              <button v-if="!emailOK" type="button" class="button primary" :disabled="busy||emailCode.length!==6" @click="verify('email')">
                <span>Verify email</span>
                <span aria-hidden="true">→</span>
              </button>
            </section>

            <section class="verified-step-card">
              <h2>Phone verification {{phoneOK?'✓':''}}</h2>
              <button v-if="!phoneOK" type="button" class="button primary" :disabled="busy||remaining>0||!emailOK" @click="phone">
                <span>{{phoneSent?'Resend phone code':'Send phone code'}}</span>
                <span aria-hidden="true">→</span>
              </button>
              <label v-if="phoneSent&&!phoneOK">Six-digit phone code
                <input v-model="phoneCode" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="Six-digit code"/>
              </label>
              <button v-if="phoneSent&&!phoneOK" type="button" class="button secondary-pill" :disabled="busy||phoneCode.length!==6" @click="verify('phone')">
                <span>Verify phone</span>
                <span aria-hidden="true">→</span>
              </button>
            </section>

            <div class="signup-grid">
              <label>Password · Required
                <input v-model="password" type="password" autocomplete="new-password" minlength="12" maxlength="128" required placeholder="At least 12 characters"/>
              </label>
              <label>Confirm password · Required
                <input v-model="confirmation" type="password" autocomplete="new-password" minlength="12" maxlength="128" required placeholder="Repeat password"/>
              </label>
            </div>

            <p class="save-readiness" role="status">{{saveHint}}</p>

            <button class="button primary" :disabled="busy||!emailOK||!phoneOK||(password.length<12||password!==confirmation)">
              <span>{{googleSession?'Save and verify account':'Save and create account'}}</span>
              <span aria-hidden="true">→</span>
            </button>
          </template>
        </form>
      </div>
    </div>
  </main>
</template>
<style scoped>
.verified-signup-shell {
  min-height: 100vh;
  min-height: 100dvh;
  padding: clamp(10px, 1.8vh, 20px) clamp(16px, 2.5vw, 28px);
  background: #ffffff;
  color: #19182e;
  font-family: 'Manrope', Inter, system-ui, sans-serif;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.verified-signup-split {
  display: grid;
  grid-template-columns: minmax(360px, 500px) minmax(0, 620px);
  gap: clamp(20px, 2.8vw, 40px);
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  align-items: center;
}

.verified-signup {
  width: 100%;
  max-width: 620px;
  padding: clamp(14px, 2.2vh, 28px) clamp(20px, 3vw, 36px);
  background: #ffffff;
  border-radius: 24px;
  box-sizing: border-box;
}

.sisu-back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 clamp(8px, 1.2vh, 12px);
  padding: 0;
  border: 0;
  background: none;
  color: #56288d;
  font: 500 12.5px 'Manrope', sans-serif;
  cursor: pointer;
}

.sisu-back-link:hover {
  text-decoration: underline;
}

.verified-signup h1 {
  margin: 0 0 clamp(4px, 0.7vh, 8px);
  font-family: 'Manrope', sans-serif;
  font-size: clamp(22px, 3vh, 30px);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: #19182e;
}

.verified-lead {
  margin: 0 0 clamp(10px, 1.5vh, 14px);
  font-size: 13.5px;
  color: #787788;
  line-height: 1.45;
}

.verified-signup fieldset {
  border: 0;
  padding: 0;
  margin: 0;
}

.signup-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: clamp(8px, 1.2vh, 12px) 14px;
}

.phone-help {
  grid-column: 1 / -1;
  margin: -4px 0 2px;
  font-size: 11.5px;
  color: #787788;
  line-height: 1.4;
}

.verified-signup label {
  display: grid;
  gap: 5px;
  margin: 6px 0;
  font-size: 12.5px;
  font-weight: 600;
  color: #19182e;
}

.verified-signup input:not([type='checkbox']),
.verified-signup select {
  min-height: clamp(40px, 5.2vh, 46px);
  padding: 9px 13px;
  border: 1px solid #e9e8ef;
  border-radius: 12px;
  width: 100%;
  box-sizing: border-box;
  background: #fcfcfe;
  color: #19182e;
  font: 400 13.5px 'Manrope', sans-serif;
}

.verified-signup input:not([type='checkbox']):focus,
.verified-signup select:focus {
  outline: none;
  border-color: #56288d;
  box-shadow: 0 0 0 3px rgba(86, 40, 141, 0.12);
}

.verified-signup .consent {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  font-weight: 400;
  color: #787788;
  margin: clamp(8px, 1.2vh, 12px) 0;
}

.consent input {
  width: 15px;
  height: 15px;
  accent-color: #56288d;
}

.consent a {
  color: #56288d;
  font-weight: 600;
  text-decoration: underline;
}

.provider-lock-note {
  font-size: 11.5px;
  color: #787788;
  line-height: 1.45;
  margin: 6px 0 12px;
}

.verified-signup button.button,
.verified-signup .google-signup {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  min-height: clamp(42px, 5.4vh, 48px);
  margin: 6px 0;
  padding: 10px 20px;
  border-radius: 24px;
  border: 1px solid #e9e8ef;
  background: #f2f0fc;
  color: #19182e;
  font: 700 13.5px 'Manrope', sans-serif;
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.15s ease, border-color 0.15s ease, opacity 0.15s ease;
}

.verified-signup button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.verified-signup button.primary {
  background: #56288d;
  color: #ffffff;
  border-color: #56288d;
  box-shadow: 0 8px 20px rgba(86, 40, 141, 0.16);
}

.verified-signup button.primary:hover:not(:disabled) {
  background: #472074;
}

.verified-signup button.secondary-pill {
  background: #f2f0fc;
  color: #19182e;
  border-color: #f2f0fc;
}

.verified-signup .google-signup {
  background: #ffffff;
  border: 1px solid #c4bbd5;
  border-radius: 27px;
  margin-bottom: 18px;
  color: #19182e;
  box-shadow: 0 1px 3px rgba(25, 24, 46, 0.04);
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease, transform 0.12s ease;
}

.verified-signup .google-signup:hover:not(:disabled) {
  border-color: #56288d;
  background: #f5f2fd;
  color: #56288d;
  box-shadow: 0 4px 14px rgba(86, 40, 141, 0.14);
  transform: translateY(-1px);
}

.verified-signup .google-signup:active:not(:disabled) {
  background: #ede7fa;
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(86, 40, 141, 0.12);
}

:global(.entry-dark .verified-signup .google-signup) {
  background: #25203b !important;
  color: #f3f1fb !important;
  border-color: rgba(196, 187, 213, 0.28) !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
}

:global(.entry-dark .verified-signup .google-signup:hover:not(:disabled)) {
  background: #312b4d !important;
  color: #ffffff !important;
  border-color: #8f85f3 !important;
  box-shadow: 0 4px 16px rgba(108, 106, 238, 0.25) !important;
  transform: translateY(-1px);
}

:global(.entry-dark .verified-signup .google-signup:active:not(:disabled)) {
  background: #282240 !important;
  transform: translateY(0);
}

:global(.entry-dark .google-arrow) {
  color: #c4b5fd !important;
}

.google-arrow {
  color: #56288d;
}

.google-note {
  font-size: 13px;
  color: #787788;
  line-height: 1.5;
  margin: 0 0 14px;
}

.verification-notice,
.save-readiness {
  padding: 14px 18px;
  border: 1px solid #cddfd4;
  border-radius: 16px;
  background: #eff8f2;
  color: #24543b;
  font-size: 13px;
  line-height: 1.55;
  margin: 12px 0;
}

.save-readiness {
  background: #f2f0fc;
  border-color: #e2dcf8;
  color: #56288d;
}

.error {
  padding: 14px 18px;
  border-radius: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 13px;
  line-height: 1.5;
  margin: 12px 0;
}

.verified-step-card {
  margin: 16px 0;
  padding: 20px 22px;
  border-radius: 20px;
  background: #fcfcfe;
  border: 1px solid #e9e8ef;
}

.verified-step-card h2 {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 800;
  color: #19182e;
}

.signup-feedback:focus {
  outline: 2px solid #7652a2;
  outline-offset: 4px;
}

.signup-feedback:has(.cooldown) {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #ffffff;
}

.cooldown {
  padding: 16px;
  border: 1px solid #d8cfe7;
  border-radius: 14px;
  background: #f6f3fc;
  color: #49335f;
  font-size: 13px;
}

.cooldown strong {
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1040px) {
  .verified-signup-split {
    grid-template-columns: minmax(0, 1fr);
    max-width: 680px;
    gap: 20px;
  }

  .verified-signup {
    padding: 24px 20px;
  }
}

@media (max-width: 640px) {
  .verified-signup-shell {
    justify-content: flex-start;
    padding: 12px 12px 24px;
  }

  .verified-signup-split {
    gap: 12px;
  }

  .verified-signup {
    padding: 20px;
    border-radius: 24px;
  }

  .sisu-back-link {
    margin: 0 0 12px;
  }

  .verified-signup h1 {
    font-size: 28px;
    line-height: 1.18;
    margin: 0 0 8px;
  }

  .verified-lead {
    font-size: 15px;
    margin: 0 0 14px;
  }

  .signup-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .verified-signup label {
    margin: 6px 0;
  }

  .verified-signup input:not([type='checkbox']),
  .verified-signup select {
    min-height: 48px;
    padding: 13px 14px;
    border-radius: 13px;
  }

  .verified-signup button.button,
  .verified-signup .google-signup {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }

  .verified-step-card {
    padding: 16px;
    border-radius: 18px;
    margin: 12px 0;
  }
}

@media (max-width: 380px) {
  .verified-signup {
    padding: 16px;
  }

  .verified-signup h1 {
    font-size: 24px;
  }
}
</style>
