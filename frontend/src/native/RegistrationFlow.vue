<script setup>
import {ref,computed,onMounted} from 'vue'
import VerifiedSignup from './VerifiedSignup.vue'
import OnboardingWelcomePanel from './OnboardingWelcomePanel.vue'
import {request} from './client'
const emit=defineEmits(['back','dashboard'])
const stage=ref('choose'),kind=ref(''),policy=ref({}),busy=ref(false),error=ref(''),accepted=ref(false),challenge=ref(''),code=ref(''),reference=ref('')
const form=ref({full_name:'',email:'',organization:'',organization_type:'Institute',country:'',timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,language:'English',subject:'',phone:'',website:'',job:'Owner',backup_name:'',backup_email:'',username:'',qualifications:'',tagline:''})
const welcomeVariant=computed(()=>{
  if(stage.value==='choose'||stage.value==='learner')return 'discover'
  if(stage.value==='provider'||stage.value==='details')return 'connect'
  return 'grow'
})
async function run(fn){busy.value=true;error.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}
async function google(){await run(async()=>{const r=await request('portal_policy','google_start');const u=new URL(r.url);if(u.protocol!=='https:'||u.hostname!=='accounts.google.com')throw Error('Google sign-in is not available.');location.assign(u.href)})}
async function submit(){await run(async()=>{const r=await request('registration','request_code',{data:{...form.value,kind:kind.value,privacy_accepted:accepted.value,privacy_policy_version:policy.value.privacy_policy_version}});challenge.value=r.challenge;stage.value='verify'})}
async function verify(){await run(async()=>{const r=await request('registration','verify_code',{challenge:challenge.value,code:code.value});reference.value=r.reference;stage.value='done'})}
onMounted(()=>run(async()=>policy.value=await request('portal_policy','public',{},'GET')))
</script>
<template>
  <VerifiedSignup v-if="policy.self_signup_enabled" :policy="policy" @back="emit('back')" @dashboard="emit('dashboard')"/>
  <main v-else class="application-shell">
    <div class="application-layout">
      <OnboardingWelcomePanel :variant="welcomeVariant" />

      <section class="panel application-form">
        <button type="button" class="sisu-back-link" @click="emit('back')">← Back to sign in</button>

        <p v-if="error" class="error application-alert" role="alert">{{error}}</p>

        <template v-if="stage==='choose'">
          <h2>Choose your SISU role</h2>
          <p class="application-lead">Your next chapter starts here.</p>
          <div class="application-choices">
            <button type="button" class="application-choice" @click="stage='learner'">
              <div>
                <strong>I’m a learner</strong>
                <span>Find teachers, join classes and make room to grow.</span>
              </div>
              <i aria-hidden="true">→</i>
            </button>
            <button type="button" class="application-choice" @click="stage='provider'">
              <div>
                <strong>I’m a teacher</strong>
                <span>Teach your classes and manage your memberships.</span>
              </div>
              <i aria-hidden="true">→</i>
            </button>
            <button type="button" class="application-choice" @click="kind='Institute';stage='details'">
              <div>
                <strong>We’re an institute</strong>
                <span>Manage your team, programmes and classrooms.</span>
              </div>
              <i aria-hidden="true">→</i>
            </button>
          </div>
        </template>

        <template v-else-if="stage==='learner'">
          <h2>Your learning starts here.</h2>
          <p class="application-lead">Create your SISU learner account with Google.</p>
          <p class="application-body-note">Students sign in with Google, then complete their profile and phone verification. One account can follow and join multiple teachers and institutes. Your account includes one 14-day trial. Your monthly price is shown on the Subscription page before payment. Class tuition is separate.</p>
          <div class="application-actions">
            <button type="button" class="sisu-pill-btn sisu-pill-primary" :disabled="busy||!policy.google_available" @click="google">
              <span>Continue with Google</span>
              <span aria-hidden="true">→</span>
            </button>
            <p v-if="!policy.google_available" class="field-help">Google sign-in will appear here when the site’s Google connection is configured.</p>
            <button type="button" class="sisu-pill-btn sisu-pill-quiet" @click="stage='choose'">
              <span>Choose another path</span>
              <span class="sisu-purple-arrow" aria-hidden="true">→</span>
            </button>
          </div>
        </template>

        <template v-else-if="stage==='provider'">
          <h2>Choose your provider account</h2>
          <p class="application-lead">Teach independently or administer an institute.</p>
          <div class="application-choices">
            <button type="button" class="application-choice" @click="kind='Individual Teacher';stage='details'">
              <div>
                <strong>Individual teacher</strong>
                <span>Your own profile, classes and institute memberships.</span>
              </div>
              <i aria-hidden="true">→</i>
            </button>
            <button type="button" class="application-choice" @click="kind='Institute';stage='details'">
              <div>
                <strong>Institute or school</strong>
                <span>A branded workspace for your teaching community.</span>
              </div>
              <i aria-hidden="true">→</i>
            </button>
          </div>
        </template>

        <form v-else-if="stage==='details'" class="application-details-form" @submit.prevent="submit">
          <h2>Tell us your story.</h2>
          <p class="application-lead">{{kind==='Institute'?'Apply for your institute or school workspace.':'Apply for your teacher account.'}}</p>
          <p class="application-body-note">We review every provider. Approval starts account setup; a verified badge and code follow profile and phone verification.</p>

          <template v-if="kind==='Institute'">
            <label>Institute name<input v-model="form.organization" required maxlength="120" placeholder="Your institute"></label>
            <label>Administrator full name<input v-model="form.full_name" required maxlength="120" placeholder="Enter administrator name"></label>
            <label>Your role at the institute<input v-model="form.job" required maxlength="120" placeholder="Owner, principal or administrator"></label>
          </template>
          <template v-else>
            <label>Your full name<input v-model="form.full_name" required maxlength="120" placeholder="Enter your name"></label>
          </template>

          <label>Email<input v-model="form.email" type="email" required :placeholder="kind==='Institute'?'institute@example.invalid':'teacher@example.invalid'"></label>
          <label>Preferred username<input v-model="form.username" pattern="[a-z][a-z0-9_]{2,29}" maxlength="30" required placeholder="Choose a username"></label>
          <label>Phone number<input v-model="form.phone" type="tel" pattern="\+[1-9][0-9]{7,14}" required placeholder="+94"></label>
          <p class="field-help">You will verify this number by SMS during secure account setup.</p>

          <template v-if="kind==='Institute'">
            <label>Recovery contact name<input v-model="form.backup_name" required placeholder="Enter contact name"></label>
            <label>Recovery contact email<input v-model="form.backup_email" type="email" required placeholder="recovery@example.invalid"></label>
          </template>
          <label v-else>Subject / expertise<input v-model="form.subject" required maxlength="120" placeholder="Combined Mathematics"></label>

          <label>Professional qualifications<input v-model="form.qualifications" maxlength="240" placeholder="Your qualifications"></label>
          <label>Tagline<input v-model="form.tagline" maxlength="120" placeholder="Short headline for your profile"></label>
          <div class="application-field-row">
            <label>Country<input v-model="form.country" required placeholder="Sri Lanka"></label>
            <label>Time zone<input v-model="form.timezone" required placeholder="Asia/Colombo"></label>
          </div>
          <label>Website (optional)<input v-model="form.website" type="url" placeholder="https://"></label>

          <label v-if="policy.privacy_policy_url" class="application-consent">
            <input v-model="accepted" type="checkbox" required>
            <span>I agree to the <a :href="policy.privacy_policy_url" target="_blank" rel="noopener noreferrer">privacy policy</a> ({{policy.privacy_policy_version}}).</span>
          </label>
          <div v-else class="application-policy">
            Privacy policy space reserved.<br>The Sisu team will add its published policy here before accepting applications.
          </div>

          <div class="application-actions">
            <button type="submit" class="sisu-pill-btn sisu-pill-primary" :disabled="busy||!accepted||!policy.provider_applications_enabled">
              <span>Verify email & submit</span>
              <span aria-hidden="true">→</span>
            </button>
            <button type="button" class="sisu-pill-btn sisu-pill-secondary" @click="stage='provider'">
              <span>Back</span>
            </button>
          </div>
        </form>

        <form v-else-if="stage==='verify'" class="application-details-form" @submit.prevent="verify">
          <h2>A little check, just for you.</h2>
          <p class="application-lead">Enter the six-digit code sent to {{form.email}}. It expires in ten minutes.</p>
          <label>Email verification code<input v-model="code" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code" required placeholder="Six-digit code"></label>
          <div class="application-actions">
            <button type="submit" class="sisu-pill-btn sisu-pill-primary" :disabled="busy">
              <span>Verify & send for review</span>
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </form>

        <template v-else>
          <h2>Your application is with us.</h2>
          <p class="application-lead">Reference: {{reference}}. Your provider application is awaiting review. We will email you a decision or a request for more information.</p>
          <div class="application-choice application-status-card">
            <div>
              <strong>Awaiting review</strong>
              <span>Keep an eye on your email for the next step. After approval, use the secure setup email to create your password, then verify your phone and complete your profile.</span>
            </div>
          </div>
          <div class="application-actions">
            <button type="button" class="sisu-pill-btn sisu-pill-secondary" @click="emit('back')">
              <span>Back to sign in</span>
              <span class="sisu-purple-arrow" aria-hidden="true">→</span>
            </button>
          </div>
        </template>
      </section>
    </div>
  </main>
</template>
<style>
.application-shell {
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

.application-layout {
  display: grid;
  grid-template-columns: minmax(360px, 500px) minmax(0, 620px);
  gap: clamp(20px, 2.8vw, 40px);
  max-width: 1180px;
  width: 100%;
  margin: 0 auto;
  align-items: center;
}

.application-form {
  box-sizing: border-box;
  width: 100%;
  max-width: 620px;
  padding: clamp(14px, 2.2vh, 28px) clamp(20px, 3vw, 36px);
  border-radius: 24px;
  background: #ffffff;
  border: 0;
  box-shadow: none;
}

.application-form h2 {
  font-family: 'Manrope', sans-serif;
  font-size: clamp(22px, 3vh, 30px);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: #19182e;
  margin: 0 0 clamp(4px, 0.7vh, 8px);
}

.application-lead {
  font-size: 13.5px;
  font-weight: 400;
  color: #787788;
  line-height: 1.45;
  margin: 0 0 clamp(10px, 1.6vh, 16px);
}

.application-body-note {
  font-size: 12.5px;
  color: #787788;
  line-height: 1.5;
  margin: 0 0 clamp(10px, 1.6vh, 16px);
}

.application-choices {
  display: grid;
  gap: clamp(10px, 1.5vh, 14px);
  margin-top: clamp(10px, 1.6vh, 16px);
}

.application-choice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  width: 100%;
  text-align: left;
  padding: clamp(14px, 2vh, 18px) clamp(16px, 2.4vw, 22px);
  border: 1px solid #e9e8ef;
  border-radius: 18px;
  background: #fcfcfe;
  color: #19182e;
  font-family: inherit;
  cursor: pointer;
  box-sizing: border-box;
  transition: border-color 0.15s ease, background 0.15s ease, transform 0.12s ease;
}

button.application-choice:hover {
  border-color: #56288d;
  background: #f8f6fe;
}

.application-choice > div {
  display: grid;
  gap: 4px;
  flex: 1;
}

.application-choice strong {
  font-size: clamp(16px, 2.2vh, 18px);
  font-weight: 800;
  color: #19182e;
  line-height: 1.25;
}

.application-choice span {
  font-size: 13px;
  font-weight: 400;
  line-height: 1.4;
  color: #787788;
}

.application-choice i {
  font-style: normal;
  font-size: 17px;
  font-weight: 700;
  color: #56288d;
  flex-shrink: 0;
}

.application-status-card {
  cursor: default;
  margin-bottom: clamp(10px, 1.6vh, 16px);
}

.application-details-form {
  display: grid;
  gap: clamp(10px, 1.4vh, 14px);
}

.application-field-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: clamp(10px, 1.4vh, 14px);
}

.application-form label {
  display: grid;
  gap: 5px;
  font-size: 12.5px;
  font-weight: 600;
  color: #19182e;
  margin: 0;
}

.application-form input:not([type='checkbox']):not([type='radio']),
.application-form select,
.application-form textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: clamp(40px, 5.2vh, 46px);
  padding: 10px 13px;
  border: 1px solid #e9e8ef;
  border-radius: 12px;
  min-width: 0;
  background: #fcfcfe;
  color: #19182e;
  font-family: 'Manrope', sans-serif;
  font-size: 13.5px;
  font-weight: 400;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.application-form input:not([type='checkbox']):not([type='radio'])::placeholder {
  color: #787788;
}

.application-form input:not([type='checkbox']):not([type='radio']):focus,
.application-form select:focus,
.application-form textarea:focus {
  outline: none;
  border-color: #56288d;
  box-shadow: 0 0 0 3px rgba(86, 40, 141, 0.12);
}

.application-form .field-help {
  margin: -4px 0 0;
  font-size: 11.5px;
  color: #787788;
}

.application-form .application-consent {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 11.5px;
  font-weight: 400;
  color: #787788;
  line-height: 1.45;
  margin-top: 2px;
}

.application-consent input[type='checkbox'] {
  width: 15px;
  height: 15px;
  accent-color: #56288d;
  margin: 0;
}

.application-consent a {
  color: #56288d;
  font-weight: 600;
  text-decoration: underline;
}

.application-policy {
  background: #fcfcfe;
  border: 1px solid #e9e8ef;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 11.5px;
  color: #787788;
  line-height: 1.5;
}

.application-actions {
  display: grid;
  gap: clamp(8px, 1.1vh, 11px);
  margin-top: 4px;
}

.sisu-pill-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  min-height: clamp(42px, 5.4vh, 48px);
  padding: 10px 20px;
  border-radius: 24px;
  font-family: 'Manrope', sans-serif;
  font-size: 13.5px;
  font-weight: 700;
  cursor: pointer;
  box-sizing: border-box;
  text-decoration: none;
  transition: background 0.15s ease, border-color 0.15s ease, opacity 0.15s ease;
}

.sisu-pill-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.sisu-pill-primary {
  background: #56288d;
  border: 1px solid #56288d;
  color: #ffffff;
  box-shadow: 0 8px 20px rgba(86, 40, 141, 0.16);
}

.sisu-pill-primary:hover:not(:disabled) {
  background: #472074;
}

.sisu-pill-secondary {
  background: #f2f0fc;
  border: 1px solid #f2f0fc;
  color: #19182e;
}

.sisu-pill-secondary:hover:not(:disabled) {
  background: #e6e1f9;
}

.sisu-pill-quiet {
  background: #ffffff;
  border: 1px solid #e9e8ef;
  color: #19182e;
}

.sisu-pill-quiet:hover:not(:disabled) {
  border-color: #56288d;
  background: #fcfcfe;
}

.sisu-purple-arrow {
  color: #56288d;
}

.application-alert {
  padding: 12px 16px;
  border-radius: 13px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 13px;
  margin-bottom: 16px;
}

@media (max-width: 1040px) {
  .application-layout {
    grid-template-columns: minmax(0, 1fr);
    max-width: 680px;
    gap: 20px;
  }

  .application-form {
    padding: 24px 20px;
  }
}

@media (max-width: 640px) {
  .application-shell {
    justify-content: flex-start;
    padding: 12px 12px 24px;
  }

  .application-layout {
    gap: 12px;
  }

  .application-form {
    padding: 20px;
    border-radius: 24px;
  }

  .application-form h2 {
    font-size: 28px;
    line-height: 1.18;
    margin: 0 0 8px;
  }

  .application-lead {
    font-size: 15px;
    line-height: 1.5;
    margin: 0 0 14px;
  }

  .application-body-note {
    margin: 0 0 14px;
  }

  .application-choices {
    gap: 10px;
    margin-top: 12px;
  }

  .application-choice {
    padding: 20px 16px;
    border-radius: 20px;
    gap: 12px;
  }

  .application-choice strong {
    font-size: 20px;
    line-height: 1.35;
  }

  .application-choice span {
    font-size: 14px;
    line-height: 1.42;
  }

  .application-details-form {
    gap: 12px;
  }

  .application-field-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .application-form input:not([type='checkbox']):not([type='radio']),
  .application-form select,
  .application-form textarea {
    min-height: 48px;
    padding: 13px 14px;
    border-radius: 13px;
    font-size: 14px;
  }

  .application-actions {
    gap: 10px;
  }

  .sisu-pill-btn {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }
}

@media (max-width: 380px) {
  .application-form {
    padding: 16px;
  }

  .application-form h2 {
    font-size: 24px;
  }

  .application-choice strong {
    font-size: 18px;
  }
}
</style>
