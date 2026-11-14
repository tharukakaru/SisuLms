<script setup>
import OtpCodeInput from '../shared/OtpCodeInput.vue'
import CountrySelect from '../shared/CountrySelect.vue'
import PhoneInput from '../shared/PhoneInput.vue'
import {computed,ref,nextTick,onMounted,onUnmounted} from 'vue'
import {request,csrf} from './client'
import {passwordStrength} from './passwordStrength'
import TeacherSignupLayout from './TeacherSignupLayout.vue'
import VerificationLayout from './VerificationLayout.vue'
import {ArrowLeft,ArrowRight,X,Mail,Smartphone,CheckCircle2,Check,RotateCw,Pencil,Eye,EyeOff,LockKeyhole,ShieldCheck} from 'lucide-vue-next'
const props=defineProps({policy:Object,googleSession:Boolean,studentOnly:Boolean});const emit=defineEmits(['back','verified'])
const refreshedPolicy=ref(null)
const policy=computed(()=>refreshedPolicy.value||props.policy||{})
async function reloadPolicy(){await run(async()=>{refreshedPolicy.value=await request('portal_policy','public',{},'GET');if(!policy.value.privacy_policy_url)throw Error('Signup is unavailable: the privacy policy has not been published.');status.value=''})}
const form=ref({kind:'Student',first_name:'',last_name:'',email:'',phone:'',username:'',country:'Sri Lanka',timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,grade:'',subject:'',organization:'',job:'',backup_name:'',backup_email:'',website:'',qualifications:'',bio:'',privacy_accepted:false})
const teacherSignup=computed(()=>['Individual Teacher','Institute Teacher'].includes(form.value.kind)&&!props.googleSession)
const instituteSignup=computed(()=>form.value.kind==='Institute'&&!props.googleSession)
const providerSignup=computed(()=>teacherSignup.value||instituteSignup.value)
const extra=computed(()=>form.value.kind==='Student'?['grade']:['Individual Teacher','Institute Teacher'].includes(form.value.kind)?['subject']:['organization','job','backup_name','backup_email'])
const required=computed(()=>['first_name','last_name','email','phone','username','country','timezone',...extra.value])
const label=f=>({first_name:'First name',last_name:'Last name',backup_email:'Recovery contact email',backup_name:'Recovery contact name',job:'Your position',grade:'Grade / study level',subject:'Subject / expertise',organization:'Institute name'}[f]||f.replaceAll('_',' ').replace(/^./,s=>s.toUpperCase()))
const feedback=ref(null),status=ref('')
const successDialog=ref(null),studentLoginUrl='/login?redirect-to=/campus'
function closeSuccess(){location.assign(studentLoginUrl)}
function backToSignIn(){
 if(!props.googleSession){emit('back');return}
 run(async()=>{
  const response=await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf()}})
  if(!response.ok)throw Error('We couldn’t sign you out. Please try again.')
  location.assign(studentLoginUrl)
 })
}
onUnmounted(()=>successDialog.value?.close())
const verificationDialog=ref(null),verificationFeedback=ref(null),resumeVerification=ref(null),verificationOpen=ref(false),detailsForm=ref(null)
async function openVerification(){await nextTick();if(!verificationDialog.value||verificationDialog.value.open)return;verificationDialog.value.showModal();verificationOpen.value=true}
function closeVerification(){if(busy.value)return;showPassword.value=false;showConfirmation.value=false;verificationDialog.value?.close();verificationOpen.value=false;nextTick(()=>resumeVerification.value?.focus())}
onUnmounted(()=>verificationDialog.value?.close())
const cooldownKey='sisu-verification-5m-retry-until'
const now=ref(Date.now()),retryUntil=ref(0)
try{const saved=Number(sessionStorage.getItem(cooldownKey));if(saved>now.value&&saved<now.value+7200000)retryUntil.value=saved}catch{}
const remaining=computed(()=>Math.max(0,Math.ceil((retryUntil.value-now.value)/1000)))
const countdown=computed(()=>`${String(Math.floor(remaining.value/60)).padStart(2,'0')}:${String(remaining.value%60).padStart(2,'0')}`)
const timer=setInterval(()=>{now.value=Date.now()},1000)
onUnmounted(()=>clearInterval(timer))
function cooldown(seconds){retryUntil.value=Date.now()+seconds*1000;now.value=Date.now();try{sessionStorage.setItem(cooldownKey,String(retryUntil.value))}catch{}}
const token=ref(''),emailCode=ref(''),phoneCode=ref(''),emailOK=ref(false),phoneOK=ref(false),phoneSent=ref(false),password=ref(''),confirmation=ref(''),busy=ref(false),error=ref(''),done=ref(false)
const studentComplete=computed(()=>done.value&&form.value.kind==='Student')
const verificationStep=ref('email'),phoneDraft=ref(''),verificationHeading=ref(null)
const showPassword=ref(false),showConfirmation=ref(false)
const passwordLength=computed(()=>Array.from(password.value).length)
const strength=computed(()=>passwordStrength(password.value))
const stepNumber=computed(()=>({email:1,phone:2,code:3,password:4}[verificationStep.value]))
const stepTitle=computed(()=>({email:'Verify email',phone:'Confirm your phone number',code:'Verify phone',password:'Set your password'}[verificationStep.value]))
const stepDescription=computed(()=>({email:'Enter the six-digit code sent to your email.',phone:'Is this the right mobile number? You can correct it below.',code:'Enter the six-digit SMS code sent to your phone.',password:'Choose a password with at least 8 characters.'}[verificationStep.value]))
const phoneUnchanged=computed(()=>phoneOK.value&&phoneDraft.value===form.value.phone)
const primaryLabel=computed(()=>({email:emailOK.value?'Continue':'Verify email',phone:phoneUnchanged.value?'Continue':'Send verification code',code:'Verify phone',password:'Save and verify account'}[verificationStep.value]))
const primaryDisabled=computed(()=>busy.value||(verificationStep.value==='email'?!emailOK.value&&emailCode.value.length!==6:verificationStep.value==='phone'?!phoneUnchanged.value&&(remaining.value>0||!/^\+[1-9][0-9]{7,14}$/.test(phoneDraft.value)):verificationStep.value==='code'?phoneCode.value.length!==6:!creationReady.value||passwordLength.value<8||password.value!==confirmation.value))
function goStep(step){showPassword.value=false;showConfirmation.value=false;verificationStep.value=step;error.value='';status.value='';nextTick(()=>verificationHeading.value?.focus())}
function previousStep(){if(busy.value)return;if(verificationStep.value==='phone')goStep('email');else{phoneDraft.value=form.value.phone;goStep('phone')}}
function submitVerification(){if(primaryDisabled.value)return;if(verificationStep.value==='email'){if(emailOK.value)goStep('phone');else verify('email')}else if(verificationStep.value==='phone')phone();else if(verificationStep.value==='code')verify('phone');else save()}
const creationReady=computed(()=>emailOK.value&&(providerSignup.value||phoneOK.value))
const saveHint=computed(()=>!emailOK.value?'Verify your email to continue.':!providerSignup.value&&!phoneOK.value?'Verify your mobile number to continue.':passwordLength.value<8?'Email verified. Choose a password of at least 8 characters.':password.value!==confirmation.value?'Email verified. Your two passwords must match.':'Email verified. Your passwords match — ready to save.');
function google(){sessionStorage.setItem('sisu_signup_role',form.value.kind);run(async()=>{const r=await request('portal_policy','google_start',{signup:1});const u=new URL(r.url);if(u.protocol!=='https:'||u.hostname!=='accounts.google.com')throw Error('Google sign-in unavailable');location.assign(u.href)})}
{const role=sessionStorage.getItem('sisu_signup_role');if(!props.googleSession&&!props.studentOnly&&['Student','Individual Teacher','Institute Teacher','Institute'].includes(role))form.value.kind=role}
async function reveal(){if(done.value)return;await nextTick();const target=verificationOpen.value?verificationFeedback.value:feedback.value;target?.scrollIntoView({behavior:'smooth',block:'nearest'});target?.focus({preventScroll:true})}
function invalid(event){error.value='Please complete '+(event.target.getAttribute('aria-label')||'the highlighted required field')+'. '+event.target.validationMessage;reveal()}
async function run(fn){if(busy.value)return;busy.value=true;error.value='';status.value='Working…';const originalStep=verificationStep.value;try{await fn()}catch(e){if(e.retryAfterSeconds){cooldown(e.retryAfterSeconds);error.value='';status.value=''}else{error.value=e.message==='Account details are unavailable. Sign in if you already registered.'?'These account details cannot be used for a new account. If you already registered, use Sign in here or Reset password above. For a new account, use a different email and an unused username.':e.message;status.value=''}}finally{busy.value=false;if(verificationOpen.value&&originalStep!==verificationStep.value){await nextTick();verificationHeading.value?.focus()}else reveal()}}
function start(){
  if (providerSignup.value &&
      (passwordLength.value < 8 ||
       password.value !== confirmation.value)) {
    error.value = "Enter matching passwords of at least 8 characters."
    reveal()
    return
  }
  run(async()=>{const r=await request('registration','self_start',{data:{...form.value,teaching_path:form.value.kind==='Institute Teacher'?'institute':'individual',kind:form.value.kind==='Institute Teacher'?'Individual Teacher':form.value.kind,privacy_policy_version:policy.value.privacy_policy_version}});token.value=r.challenge;emailCode.value='';emailOK.value=false;phoneOK.value=false;phoneSent.value=false;phoneDraft.value=form.value.phone;verificationStep.value='email';status.value='Email code requested. Check your inbox and enter it below.';if(props.googleSession)await openVerification()})}
function verify(channel){run(async()=>{await request('registration','self_verify',{token:token.value,channel,code:channel==='email'?emailCode.value:phoneCode.value});if(channel==='email'){emailOK.value=true;phoneDraft.value=form.value.phone;goStep('phone')}else{phoneOK.value=true;goStep('password')}status.value=channel==='email'?'Email verified. Confirm your phone number next.':'Phone verified. Choose your password.'})}
function phone(){if(busy.value)return;if(props.googleSession&&phoneUnchanged.value){goStep('password');return}run(async()=>{const number=props.googleSession?phoneDraft.value:form.value.phone;await request('registration','self_phone',{token:token.value,phone:number});form.value.phone=number;phoneDraft.value=number;phoneSent.value=true;phoneOK.value=false;phoneCode.value='';goStep('code');status.value='SMS code requested. Check your phone.'})}
function save(){run(async()=>{await request('registration','self_complete',{token:token.value,password:password.value,confirmation:confirmation.value});password.value='';confirmation.value='';if(props.googleSession){const out=await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf()}});if(!out.ok)throw Error('Your account is saved. Sign out, then sign in again.')}done.value=true;verificationDialog.value?.close();verificationOpen.value=false;status.value='';if(form.value.kind==='Student'){await nextTick();successDialog.value?.showModal()}})}
function reset(){verificationStep.value='email';phoneDraft.value='';closeVerification();error.value='';status.value='';token.value='';emailOK.value=false;phoneOK.value=false;phoneSent.value=false;emailCode.value='';phoneCode.value='';password.value='';confirmation.value='';nextTick(()=>detailsForm.value?.querySelector('input:not([readonly]):not([disabled])')?.focus())}
onMounted(()=>{if(!policy.value.privacy_policy_url&&!props.googleSession)reloadPolicy();if(props.googleSession)run(async()=>{const d=await request('registration','self_google_details',{},'GET');Object.assign(form.value,d,{kind:'Student'});status.value='Google details filled in. Complete the remaining required fields.'})})

</script>
<template>
<VerificationLayout v-if="token&&!googleSession&&!done" @back="emit('back')">
  <h1>{{!emailOK?'A little check, just for you.':!phoneOK&&!providerSignup?'Let’s make this space yours.':'Your next chapter is ready.'}}</h1>
  <p class="verification-intro">{{!emailOK?'Enter the code sent to your application email. You can resend the code or change the address.':!phoneOK&&!providerSignup?'Verify your mobile number to continue.':'Choose your password to finish setting up your account.'}}</p>
  <form v-if="!emailOK" @submit.prevent="verify('email')">
    <label>Email verification code<input v-model="emailCode" aria-label="Six-digit email code" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="Six-digit code"></label>
    <button class="teacher-submit" :disabled="busy||emailCode.length!==6">{{busy?'Verifying…':'Verify email & continue'}}<ArrowRight :size="16" aria-hidden="true"/></button>
    <div class="verification-actions"><button type="button" :disabled="busy||remaining>0" @click="start">Resend email code</button><button type="button" :disabled="busy" @click="reset">Change email / edit details</button></div>
  </form>
  <template v-else-if="!phoneOK&&!providerSignup">
    <form @submit.prevent="phone">
      <label>Mobile number<input :value="form.phone" type="tel" readonly autocomplete="tel" placeholder="+94"></label>
      <button class="teacher-submit" :disabled="busy||remaining>0||!emailOK">{{busy?'Sending…':phoneSent?'Resend verification code':'Send verification code'}}<ArrowRight :size="16" aria-hidden="true"/></button>
    </form>
    <form class="verification-phone-form" @submit.prevent="verify('phone')">
      <label>Verification code<input v-model="phoneCode" aria-label="Six-digit phone code" :disabled="!phoneSent||busy" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="Six-digit code"></label>
      <button class="teacher-submit verification-secondary" :disabled="busy||!phoneSent||phoneCode.length!==6">Verify number<ArrowRight :size="16" aria-hidden="true"/></button>
    </form>
    <div class="verification-actions"><button type="button" :disabled="busy" @click="reset">Change number / edit details</button></div>
  </template>
  <form v-else @invalid.capture="invalid" @submit.prevent="save">
    <label v-if="!providerSignup">Password · Required<input v-model="password" type="password" autocomplete="new-password" minlength="8" maxlength="128" required></label>
    <label v-if="!providerSignup">Confirm password · Required<input v-model="confirmation" type="password" autocomplete="new-password" minlength="8" maxlength="128" required></label>
    <p class="verification-intro" role="status">{{saveHint}}</p>
    <button class="teacher-submit" :disabled="busy||!creationReady||(passwordLength<8||password!==confirmation)">Save and create account<ArrowRight :size="16" aria-hidden="true"/></button>
    <div class="verification-actions"><button type="button" :disabled="busy" @click="reset">Change signup details</button></div>
  </form>
  <div ref="feedback" tabindex="-1" aria-live="polite" class="verification-feedback">
    <p v-if="remaining" role="status">You’ve reached the code request limit. Try again in <strong>{{countdown}}</strong>. You can still verify a code you already received.</p>
    <p v-else-if="retryUntil">00:00 — You can request a code again.</p>
    <p v-if="error" role="alert" class="error">{{error}}</p><p v-else-if="busy" role="status">{{status}}</p>
  </div>
</VerificationLayout>
<TeacherSignupLayout v-else :active="providerSignup" :institute="instituteSignup"><main class="verified-signup" :class="{'teacher-signup-form':providerSignup,'institute-signup-form':instituteSignup,'student-signup-form':googleSession,'signup-completed':studentComplete}"><template v-if="!studentComplete"><button type="button" class="signup-back" :class="{'teacher-signup-back':providerSignup}" :disabled="busy" @click="backToSignIn"><ArrowLeft :size="18" aria-hidden="true"/><span>Back to sign in</span></button><h1>{{providerSignup?'Tell us your story.':'Create your SISU account'}}</h1><p v-if="providerSignup" class="teacher-signup-intro">{{instituteSignup?'Apply for your institute or school workspace.':'Apply for your teacher account.'}}</p><button v-if="!providerSignup&&!googleSession&&!token&&!done" type="button" class="google-signup" :disabled="busy||!policy.google_available" @click="google"><img :src="'/assets/frappe/icons/social/google.svg'" alt="" width="22" height="22"/> Sign up with Google</button><p v-if="!providerSignup&&!googleSession&&!policy.google_available" class="google-note">Google signup is not available yet. You can create your account using email below.</p><p v-if="googleSession">Complete your student profile, verify your email and phone, then set a password. You’ll return to sign in when you’re done.</p><div ref="feedback" tabindex="-1" aria-live="polite" class="signup-feedback"><p v-if="remaining" class="cooldown" role="status">You’ve reached the code request limit. Try again in <strong>{{countdown}}</strong>. You can still verify a code you already received.</p><p v-else-if="retryUntil" class="cooldown">00:00 — You can request a code again.</p><p v-if="error" role="alert" class="error">{{error}}</p><p v-else-if="status" class="verification-notice" role="status">{{status}}</p></div><section v-if="done" role="status"><h2>Account created successfully</h2><p>Your details have been saved. Please sign in with your email and password.</p><button class="button primary" @click="emit('back')">Back to login</button></section><form v-else ref="detailsForm" @invalid.capture="invalid" @submit.prevent="token?openVerification():start()"><fieldset :disabled="busy||!!token"><p v-if="googleSession||studentOnly" class="signup-account-type">Account type <strong>Student</strong><span>All fields are required.</span></p><label v-else-if="!providerSignup">Account type · Required<select v-model="form.kind"><option>Student</option><option>Individual Teacher</option><option>Institute Teacher</option><option value="Institute">Institute admin</option></select></label><template v-if="teacherSignup">
  <div class="teacher-field-group" role="group" aria-labelledby="teacher-name-label"><span id="teacher-name-label">Your full name</span><div class="teacher-paired-fields">
    <label><span class="teacher-sr-only">First name</span><input v-model="form.first_name" aria-label="First name" required maxlength="60" placeholder="First name" autocomplete="given-name"></label>
    <label><span class="teacher-sr-only">Last name</span><input v-model="form.last_name" aria-label="Last name" required maxlength="60" placeholder="Last name" autocomplete="family-name"></label>
  </div></div>
  <label>Email<input v-model="form.email" aria-label="Email" type="email" required maxlength="254" placeholder="teacher@example.com" autocomplete="email"></label>
  <label>Preferred username<input v-model="form.username" aria-label="Username" required maxlength="60" pattern="[a-zA-Z][a-zA-Z0-9_]{2,29}" title="Use 3–30 letters, digits or underscores; start with a letter. Usernames are saved in lowercase." placeholder="Choose a username" autocomplete="username"></label>
  <label>Phone number<PhoneInput v-model="form.phone" aria-label="Phone" required /></label>
  <label>Subject / expertise<input v-model="form.subject" aria-label="Subject / expertise" required maxlength="254" placeholder="e.g. Combined Mathematics"></label>
  <label>Professional qualifications<input v-model="form.qualifications" aria-label="Qualifications" maxlength="500" placeholder="Your qualifications"></label>
  <div class="teacher-field-group" role="group" aria-labelledby="teacher-location-label"><span id="teacher-location-label">Country / time zone</span><div class="teacher-paired-fields">
    <label><span class="teacher-sr-only">Country</span><CountrySelect v-model="form.country" aria-label="Country" required /></label>
    <label><span class="teacher-sr-only">Timezone</span><input v-model="form.timezone" aria-label="Timezone" required maxlength="254" placeholder="e.g. Asia/Colombo"></label>
  </div></div>

</template><template v-else-if="instituteSignup">
  <label>Institute name<input v-model="form.organization" aria-label="Institute name" required maxlength="254" placeholder="Your institute" autocomplete="organization"></label>
  <div class="teacher-field-group" role="group" aria-labelledby="institute-admin-label"><span id="institute-admin-label">Administrator full name</span><div class="teacher-paired-fields">
    <label><span class="teacher-sr-only">Administrator first name</span><input v-model="form.first_name" aria-label="Administrator first name" required maxlength="60" placeholder="First name" autocomplete="given-name"></label>
    <label><span class="teacher-sr-only">Administrator last name</span><input v-model="form.last_name" aria-label="Administrator last name" required maxlength="60" placeholder="Last name" autocomplete="family-name"></label>
  </div></div>
  <label>Your role at the institute<input v-model="form.job" aria-label="Your role at the institute" required maxlength="254" placeholder="Owner, principal or administrator" autocomplete="organization-title"></label>
  <label>Email<input v-model="form.email" aria-label="Email" type="email" required maxlength="254" placeholder="institute@example.com" autocomplete="email"></label>
  <label>Phone number<PhoneInput v-model="form.phone" aria-label="Phone number" required /></label>
  <label>Recovery contact name<input v-model="form.backup_name" aria-label="Recovery contact name" required maxlength="60" placeholder="Enter contact name"></label>
  <label>Recovery contact email<input v-model="form.backup_email" aria-label="Recovery contact email" type="email" required maxlength="254" placeholder="recovery@example.com"></label>
  <label>Preferred username<input v-model="form.username" aria-label="Username" required maxlength="60" pattern="[a-zA-Z][a-zA-Z0-9_]{2,29}" title="Use 3–30 letters, digits or underscores; start with a letter. Usernames are saved in lowercase." placeholder="Choose a username" autocomplete="username"></label>
  <div class="teacher-field-group" role="group" aria-labelledby="institute-location-label"><span id="institute-location-label">Country / time zone</span><div class="teacher-paired-fields">
    <label><span class="teacher-sr-only">Country</span><CountrySelect v-model="form.country" aria-label="Country" required /></label>
    <label><span class="teacher-sr-only">Timezone</span><input v-model="form.timezone" aria-label="Timezone" required maxlength="254" placeholder="e.g. Asia/Colombo"></label>
  </div></div>
</template><div v-else class="signup-grid"><label v-for="field in required" :key="field">{{label(field)}}<template v-if="!googleSession"> · Required</template><PhoneInput v-if="field==='phone'" v-model="form[field]" required /><CountrySelect v-else-if="field==='country'" v-model="form[field]" required /><input v-else v-model="form[field]" :aria-label="label(field)" :readonly="googleSession&&field==='email'" :type="field.includes('email')?'email':field==='phone'?'tel':'text'" required :maxlength="field.includes('name')?60:254" :pattern="field==='username'?'[a-zA-Z][a-zA-Z0-9_]{2,29}':undefined" :title="field==='username'?'Use 3–30 letters, digits or underscores; start with a letter.':undefined" :placeholder="field==='phone'?'+94761234567':field==='username'?'e.g. sisu_student':''"/></label><p class="phone-help">Choose your country code and enter a mobile number that can receive verification codes.</p><label v-for="field in (form.kind==='Student'?[]:['website','qualifications','bio'])" :key="field">{{label(field)}} · Optional<PhoneInput v-if="field==='phone'" v-model="form[field]" required /><CountrySelect v-else-if="field==='country'" v-model="form[field]" required /><input v-else v-model="form[field]" :aria-label="label(field)" :readonly="googleSession&&field==='email'" :type="field==='website'?'url':'text'" maxlength="500"/></label></div>

<div v-if="providerSignup" class="teacher-password-fields">
  <label>Password · Required
    <input v-model="password"
      aria-label="Password"
      type="password"
      autocomplete="new-password"
      minlength="8"
      maxlength="128"
      required>
  </label>
  <label>Confirm password · Required
    <input v-model="confirmation"
      aria-label="Confirm password"
      type="password"
      autocomplete="new-password"
      minlength="8"
      maxlength="128"
      required>
  </label>
  <p v-if="confirmation && password !== confirmation"
     class="teacher-help" role="alert">
    Passwords must match.
  </p>
</div>
<label class="consent" :class="{'teacher-consent':providerSignup}"><input type="checkbox" v-model="form.privacy_accepted" aria-label="privacy policy acceptance" required/>I accept the <a :href="policy.privacy_policy_url" target="_blank" rel="noopener noreferrer">privacy policy</a>.</label></fieldset><p v-if="!policy.privacy_policy_url" class="teacher-help" role="status">We could not load the signup privacy policy. <button type="button" :disabled="busy" @click="reloadPolicy">Retry loading signup</button></p><p v-if="form.kind!=='Student'&&!providerSignup">Your teaching workspace stays locked until your plan payment is verified. Account verification does not grant a provider endorsement badge.</p><button v-if="!token" class="button primary" :class="{'teacher-submit':providerSignup}" :disabled="busy||remaining>0||!policy.privacy_policy_url">{{busy?'Sending…':providerSignup?'Verify email & continue':'Send email verification code'}}<ArrowRight v-if="providerSignup" :size="16" aria-hidden="true"/></button><p v-if="teacherSignup" class="teacher-help">Your teaching workspace stays locked until your plan payment is verified. Account verification does not grant a provider endorsement badge.</p><p v-if="providerSignup&&!policy.privacy_policy_url" class="teacher-help">Signup will be available once the site’s privacy policy is published.</p><button v-if="token" ref="resumeVerification" type="button" class="button primary" :disabled="busy" aria-haspopup="dialog" @click="openVerification">Continue verification</button></form></template>
<dialog ref="verificationDialog" class="signup-verification-popup" :class="{'password-dialog':verificationStep==='password'}" aria-labelledby="signup-verification-title" aria-describedby="signup-step-description" @cancel.prevent.stop="closeVerification">
  <header class="popup-header">
    <div class="popup-heading"><h2 ref="verificationHeading" id="signup-verification-title" tabindex="-1" autofocus>{{stepTitle}}</h2><p id="signup-step-description">{{stepDescription}}</p><ol class="step-progress" :aria-label="`Signup progress: step ${stepNumber} of 4`"><li v-for="(step,index) in ['Email','Phone','Code','Password']" :key="step" :class="{complete:index+1<stepNumber,current:index+1===stepNumber}" :aria-current="index+1===stepNumber?'step':undefined"><span class="step-marker"><Check v-if="index+1<stepNumber" :size="13" aria-hidden="true"/><template v-else>{{index+1}}</template></span><span>{{step}}</span></li></ol></div>
    <button type="button" class="popup-close" aria-label="Close account verification" :disabled="busy" @click="closeVerification"><X :size="22" aria-hidden="true"/></button>
  </header>
  <form class="popup-form" @invalid.capture="invalid" @submit.prevent="submitVerification">
    <div class="popup-body">
      <div ref="verificationFeedback" class="popup-feedback" tabindex="-1" aria-live="polite">
        <p v-if="remaining" class="cooldown" role="status">You can request another code in <strong>{{countdown}}</strong>. You can still verify a code you already received.</p>
        <p v-if="error" class="error" role="alert">{{error}}</p><p v-else-if="busy" role="status">{{status}}</p>
      </div>
      <section v-if="verificationStep==='email'" class="popup-step code-step">
        <div class="verification-contact"><Mail :size="20" aria-hidden="true"/><div><small>Code sent to</small><strong>{{form.email}}</strong></div></div>
        <p v-if="emailOK" class="verification-complete" role="status">Your email is verified.</p>
        <template v-else><OtpCodeInput v-model="emailCode" label="Email verification code" :disabled="busy" :invalid="!!error" @update:model-value="error=''"/><div class="resend-row"><button type="button" class="text-action" :disabled="busy||remaining>0" @click="start"><RotateCw :size="15" aria-hidden="true"/>Resend email code</button></div></template>
      </section>
      <section v-else-if="verificationStep==='phone'" class="popup-step">
        <label>Mobile number<PhoneInput v-model="phoneDraft" aria-label="Mobile number" required :disabled="busy"/></label>
        <p class="verification-help">Use a number you can access. We’ll send a verification code by SMS.</p>
        <p v-if="phoneUnchanged" class="verification-complete" role="status">This number is already verified.</p>
      </section>
      <section v-else-if="verificationStep==='code'" class="popup-step code-step">
        <div class="verification-contact"><Smartphone :size="20" aria-hidden="true"/><div><small>Code sent to</small><strong>{{form.phone}}</strong></div></div>
        <OtpCodeInput v-model="phoneCode" label="Phone verification code" :disabled="busy" :invalid="!!error" @update:model-value="error=''"/>
        <div class="resend-row"><button type="button" class="text-action" :disabled="busy||remaining>0" @click="phone"><RotateCw :size="15" aria-hidden="true"/>Resend SMS code</button></div>
      </section>
      <section v-else class="popup-step password-step">
        <div class="password-control">
          <label for="signup-password">Password</label>
          <div class="password-input-shell">
            <LockKeyhole :size="18" class="password-field-icon" aria-hidden="true"/>
            <input id="signup-password" v-model="password" :type="showPassword?'text':'password'" autocomplete="new-password" minlength="8" maxlength="128" required :disabled="busy" aria-describedby="signup-password-strength signup-password-help"/>
            <button type="button" class="password-visibility" :disabled="busy" :aria-label="showPassword?'Hide password':'Show password'" :aria-pressed="showPassword" @click="showPassword=!showPassword"><EyeOff v-if="showPassword" :size="17" aria-hidden="true"/><Eye v-else :size="17" aria-hidden="true"/><span>{{showPassword?'Hide':'Show'}}</span></button>
          </div>
        </div>
        <div class="password-strength" :data-score="strength.score">
          <div class="strength-caption" id="signup-password-strength"><span>Password strength</span><strong>{{strength.label}}</strong></div>
          <div class="strength-track" role="meter" aria-label="Password strength" aria-valuemin="0" aria-valuemax="4" :aria-valuenow="strength.score" :aria-valuetext="strength.label"><span v-for="part in 4" :key="part" :class="{filled:part<=strength.score}"></span></div>
        </div>
        <p id="signup-password-help" class="password-requirement" :class="{met:passwordLength>=8}"><CheckCircle2 v-if="passwordLength>=8" :size="16" aria-hidden="true"/><span v-else class="requirement-dot" aria-hidden="true"></span>At least 8 characters</p>
        <div class="password-control confirmation-control">
          <label for="signup-confirm-password">Confirm password</label>
          <div class="password-input-shell" :class="{'is-matched':confirmation&&passwordLength>=8&&password===confirmation,'is-mismatched':confirmation&&password!==confirmation}">
            <LockKeyhole :size="18" class="password-field-icon" aria-hidden="true"/>
            <input id="signup-confirm-password" v-model="confirmation" :type="showConfirmation?'text':'password'" autocomplete="new-password" minlength="8" maxlength="128" required :disabled="busy" :aria-invalid="confirmation&&password!==confirmation?true:undefined" aria-describedby="signup-password-match"/>
            <button type="button" class="password-visibility" :disabled="busy" :aria-label="showConfirmation?'Hide confirm password':'Show confirm password'" :aria-pressed="showConfirmation" @click="showConfirmation=!showConfirmation"><EyeOff v-if="showConfirmation" :size="17" aria-hidden="true"/><Eye v-else :size="17" aria-hidden="true"/><span>{{showConfirmation?'Hide':'Show'}}</span></button>
          </div>
        </div>
        <p id="signup-password-match" class="password-match" :class="{'is-matched':confirmation&&passwordLength>=8&&password===confirmation,'is-mismatched':confirmation&&password!==confirmation}" role="status"><template v-if="confirmation&&password!==confirmation">Passwords do not match yet.</template><template v-else-if="confirmation&&passwordLength>=8"><CheckCircle2 :size="17" aria-hidden="true"/>Passwords match. You’re ready to save.</template><template v-else>Enter the same password again to confirm.</template></p>
      </section>
    </div>
    <footer class="popup-footer">
      <div class="step-actions"><button class="button primary" :disabled="primaryDisabled"><span>{{busy?'Please wait…':primaryLabel}}</span><ShieldCheck v-if="!busy&&verificationStep==='password'" :size="18" aria-hidden="true"/><ArrowRight v-else-if="!busy" :size="18" aria-hidden="true"/></button><button v-if="verificationStep!=='email'" type="button" class="text-action" :disabled="busy" @click="previousStep"><ArrowLeft :size="16" aria-hidden="true"/>{{verificationStep==='phone'?'Back':verificationStep==='code'?'Change number':'Review phone number'}}</button></div>
      <div class="details-recovery"><button type="button" class="text-action" :disabled="busy" @click="reset"><Pencil :size="14" aria-hidden="true"/>Change signup details</button><small>You’ll verify your email and phone again.</small></div>
    </footer>
  </form>
</dialog>
<dialog ref="successDialog" class="signup-verification-popup signup-success-popup" aria-labelledby="signup-success-title" aria-describedby="signup-success-description" @cancel.prevent="closeSuccess">
  <button type="button" class="popup-close success-close" aria-label="Close signup confirmation" @click="closeSuccess"><X :size="22" aria-hidden="true"/></button>
  <CheckCircle2 class="success-icon" :size="48" :stroke-width="1.5" aria-hidden="true"/>
  <h2 id="signup-success-title">Account created successfully</h2>
  <p id="signup-success-description">Your student account is ready. Log in with your email and password to open your campus.</p>
  <a class="button primary signup-login-link" :href="studentLoginUrl" autofocus>Log in<ArrowRight :size="18" aria-hidden="true"/></a>
</dialog></main></TeacherSignupLayout></template>
<style scoped>.verification-notice,.save-readiness{padding:14px 18px;border:1px solid #cddfd4;border-radius:14px;background:#eff8f2;color:#24543b;line-height:1.6}.save-readiness{background:#f5f2fc;border-color:#ded5ee;color:#49335f}.verified-signup{max-width:820px;margin:35px auto;padding:28px;background:var(--surface,#fff);border-radius:20px}.verified-signup fieldset{border:0;padding:0}.signup-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.verified-signup label{display:grid;gap:8px;margin:14px 0}.verified-signup input,.verified-signup select{padding:12px;border:1px solid #b9b3c6;border-radius:8px;width:100%;box-sizing:border-box}.verified-signup .consent{display:flex;align-items:center}.consent input{width:auto}.verified-signup button{margin:8px 8px 8px 0;padding:10px 15px}.verified-signup button{min-height:44px;border:1px solid #c4bbd5;border-radius:10px;background:#f5f1fa;color:#38224e;font:600 15px/1.4 system-ui;cursor:pointer}.verified-signup button:disabled{opacity:.55;cursor:not-allowed}.verified-signup button.primary{background:#592b91;color:white;border-color:#592b91}.verified-signup .google-signup{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;padding:14px 20px;background:#fff;border:1px solid #b9b3c6;box-shadow:0 2px 5px #24113712}.google-mark{font:700 22px system-ui;color:#4285f4}.google-note{font-size:14px;color:#64566f}.signup-feedback:focus{outline:2px solid #7652a2;outline-offset:5px}.verified-signup section{margin:22px 0}@media(max-width:600px){.signup-grid{grid-template-columns:1fr}}.signup-feedback:has(.cooldown){position:sticky;top:0;z-index:2;background:var(--surface,#fff)}.cooldown{padding:16px;border:1px solid #d8cfe7;border-radius:12px;background:#f6f3fc;color:#49335f}.cooldown strong{font-variant-numeric:tabular-nums}
.signup-verification-popup{box-sizing:border-box;width:min(520px,calc(100vw - 32px));max-height:calc(100dvh - 32px);padding:0;border:0;border-radius:16px;background:var(--surface,#fff);color:var(--text,#28203b);box-shadow:0 24px 72px #24113740;overflow:hidden}
.signup-verification-popup[open]{display:flex;flex-direction:column}
.signup-verification-popup::backdrop{background:#21132b88}
.popup-header{position:relative;padding:28px 28px 0;flex-shrink:0}
.popup-heading{min-width:0}.popup-header h2{margin:0;padding-right:38px;font-size:26px;line-height:1.25;letter-spacing:-.025em}
.popup-header h2:focus{outline:none}.popup-header p{margin:8px 0 0;padding-right:20px;color:#64566f;font-size:14px;line-height:1.6}
.verified-signup .popup-close{display:grid;place-items:center;flex-shrink:0;width:44px;height:44px;padding:0;margin:0;background:transparent;border-color:transparent}
.popup-header .popup-close{position:absolute;right:14px;top:16px}
.step-progress{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;padding:12px 8px;margin:22px 0 0;list-style:none;background:#f7f5fa;border-radius:10px}
.step-progress li{display:flex;align-items:center;justify-content:center;gap:6px;min-width:0;color:#6b6078;font-size:12px;line-height:1.4}
.step-marker{display:flex;align-items:center;justify-content:center;width:22px;height:22px;flex-shrink:0;border:1px solid #c9c1d4;border-radius:50%;font-size:11px;font-weight:600;font-variant-numeric:tabular-nums}
.step-progress .current{color:#592b91;font-weight:700}.step-progress .current .step-marker{color:#fff;background:#592b91;border-color:#592b91}
.step-progress .complete{color:#592b91}.step-progress .complete .step-marker{background:#ede5f6;border-color:#ede5f6}
.popup-form{display:flex;flex-direction:column;min-height:0;margin:0;overflow:hidden}
.popup-body{padding:24px 28px 20px;overflow:auto;overscroll-behavior:contain;scrollbar-color:#b9afc9 #f5f1fa;scrollbar-width:thin;min-height:0}
.popup-feedback:empty{display:none}.popup-feedback p{margin:0 0 16px;line-height:1.5;font-size:14px}.popup-feedback .error{padding:12px;border-radius:8px;background:#fff2f4;color:#923147}.popup-feedback:focus-visible{outline:2px solid #592b91;outline-offset:3px}
.verified-signup .popup-step{margin:0}.popup-step h3{margin:0 0 8px;font-size:18px;line-height:1.4}
.verification-contact{display:flex;align-items:center;justify-content:center;gap:10px;margin:0 0 24px;color:#592b91;overflow-wrap:anywhere}
.verification-contact svg{flex-shrink:0}.verification-contact div{min-width:0;text-align:left}.verification-contact small{display:block;color:#64566f;font-size:13px;margin-bottom:3px}.verification-contact strong{display:block;font-size:15px;font-weight:600;color:#28203b}
.verification-help{margin:8px 0;color:#64566f;line-height:1.5;font-size:14px}.verification-complete{font-size:14px;color:#24543b;font-weight:600}.popup-step .verification-complete{margin:12px 0}
.resend-row{display:flex;justify-content:center;margin-top:8px}.verified-signup .resend-row button{margin:0;font-size:13px}
.popup-footer{display:flex;flex-direction:column;gap:16px;flex-shrink:0;padding:0 28px 20px;background:var(--surface,#fff)}
.verified-signup .popup-footer button{margin:0}.popup-body input{font-size:16px;caret-color:#592b91}.popup-body ::selection{background:#e3d5f7;color:#28203b}
.signup-verification-popup button:focus-visible,.signup-verification-popup input:focus-visible{outline:2px solid #592b91;outline-offset:3px}
.signup-verification-popup button:not(:disabled):hover{filter:brightness(.96)}
.verified-signup .text-action{display:inline-flex;align-items:center;justify-content:center;gap:7px;background:transparent;border-color:transparent;color:#592b91;text-decoration:none;padding:8px 4px;font-family:inherit}
.verified-signup .text-action:hover:not(:disabled){text-decoration:underline;text-underline-offset:4px}
.step-actions{display:flex;flex-direction:column;align-items:stretch;gap:4px}.step-actions>.primary{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:48px;margin-inline-start:0}
.verified-signup .step-actions>.primary:disabled{opacity:1;background:#eae3f3;border-color:#eae3f3;color:#6c587e;box-shadow:none}
.details-recovery{display:flex;flex-direction:column;align-items:center;gap:0;border-top:1px solid #eee8f3;padding-top:8px}.verified-signup .details-recovery .text-action{font-size:13px;color:#64566f;min-height:44px}.details-recovery small{font-size:12px;color:#64566f;line-height:1.5;text-align:center}
@media(max-width:600px){.signup-verification-popup{width:calc(100vw - 24px);max-height:calc(100dvh - 24px)}.popup-header{padding:24px 20px 0}.popup-header h2{font-size:24px}.popup-header p{padding-right:0}.popup-header .popup-close{right:10px;top:12px}.popup-body{padding:22px 20px 16px}.popup-footer{padding:0 20px 16px;gap:12px}.step-progress{gap:4px;padding:10px 4px;margin-top:20px}.step-progress li{flex-direction:column;gap:5px}.verification-contact strong{font-size:14px}}

.password-control{margin:0 0 12px}
.verified-signup .password-control label{display:block;margin:0 0 9px;font-size:14px;font-weight:600;color:#382c47}
.password-input-shell{display:flex;align-items:center;gap:10px;min-height:54px;padding:4px 5px 4px 14px;border:1px solid #a695b8;border-radius:12px;background:#fcfbfe;box-sizing:border-box}
.password-input-shell:focus-within{border-color:#592b91;outline:2px solid #592b91;outline-offset:2px;background:#fff}
.password-field-icon{flex-shrink:0;color:#79628d}
.verified-signup .password-input-shell input{width:0;flex:1;min-width:0;min-height:44px;padding:8px 0;border:0;border-radius:0;background:transparent;box-shadow:none;font-family:inherit;font-size:16px;color:#28203b}
.verified-signup .password-input-shell input:focus-visible{outline:none}
.verified-signup .password-visibility{display:inline-flex;align-items:center;justify-content:center;gap:6px;flex-shrink:0;min-width:78px;min-height:44px;margin:0;padding:8px 10px;border:0;border-radius:8px;background:#f0eaf7;color:#592b91;font-family:inherit;font-size:13px;font-weight:600;line-height:1.4}
.verified-signup .password-visibility:hover:not(:disabled){background:#e8ddf3}
.strength-caption{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:8px;font-size:13px;line-height:1.4;color:#64566f}.strength-caption strong{font-weight:600}
.strength-track{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;height:5px}.strength-track span{border-radius:3px;background:#e8e1ef}.strength-track .filled{background:#a33246}
.password-strength[data-score="2"] .filled{background:#9b6a16}.password-strength[data-score="3"] .filled{background:#537a25}.password-strength[data-score="4"] .filled{background:#246344}
.password-strength[data-score="4"] strong{color:#246344}
.password-requirement{display:flex;align-items:center;gap:7px;margin:10px 0 18px;font-size:13px;line-height:1.5;color:#64566f}.password-requirement.met{color:#246344}.requirement-dot{width:6px;height:6px;border:1px solid #79628d;border-radius:50%;margin:0 4px}
.password-input-shell.is-matched{border-color:#518167}.password-input-shell.is-mismatched{border-color:#a33246}
.password-match{display:flex;align-items:center;gap:7px;margin:10px 0 0;font-size:13px;line-height:1.5;color:#64566f;min-height:20px}.password-match svg{flex-shrink:0}.password-match.is-matched{color:#246344}.password-match.is-mismatched{color:#923147}
.password-dialog .popup-body{padding-top:20px;padding-bottom:16px}.password-dialog .popup-footer{gap:8px}.verified-signup .password-dialog .step-actions>.primary{min-height:52px;border-radius:12px;font-family:inherit;font-weight:700}
.password-dialog .step-actions>.text-action{font-size:13px;font-weight:500}
@media(max-width:380px){.password-input-shell{gap:7px;padding-left:10px}.verified-signup .password-visibility{min-width:68px;padding:8px 7px}.password-field-icon{width:16px}}

.student-signup-form{max-width:800px;padding:32px;margin:24px auto;border-radius:16px}
.student-signup-form>h1{font-size:30px;line-height:1.25;margin:20px 0 10px;letter-spacing:-.025em}
.student-signup-form>p{color:#64566f;line-height:1.6;max-width:66ch;margin:0 0 20px}
.student-signup-form>.signup-feedback:empty{display:none}
.student-signup-form .verification-notice{padding:12px 16px;font-size:14px;border-radius:10px;margin:0 0 24px}
.signup-account-type{display:flex;align-items:center;gap:10px;font-size:14px;color:#64566f;margin:0 0 24px;padding-bottom:16px;border-bottom:1px solid #e5dfed}
.signup-account-type strong{color:#592b91;font-weight:600}.signup-account-type span{margin-left:auto;font-size:12px}
.student-signup-form .signup-grid{gap:22px 20px}
.student-signup-form .signup-grid label{margin:0;font-size:14px;font-weight:500;line-height:1.5}
.student-signup-form .signup-grid input{min-height:46px;font-size:15px;background:#fff}
.student-signup-form .signup-grid input[readonly]{background:#f8f6fb;color:#64566f}
.student-signup-form .phone-help{grid-column:1/-1;font-size:13px;line-height:1.5;color:#64566f;margin:0}
.student-signup-form .consent{flex-wrap:wrap;gap:6px;font-size:14px;margin:24px 0 16px}
.student-signup-form .consent input{width:18px;height:18px;margin:0 4px 0 0;accent-color:#592b91}
.student-signup-form>form>.primary{width:100%;margin:0;min-height:48px}
.student-signup-form .signup-grid input:focus-visible{outline:2px solid #592b91;outline-offset:2px}
@media(max-width:600px){.student-signup-form{padding:20px 16px;margin:0 auto;border-radius:0}.student-signup-form>h1{font-size:26px}.student-signup-form .signup-grid{gap:18px}.signup-account-type{flex-wrap:wrap}.signup-account-type span{flex-basis:100%;margin-left:0}}

.signup-success-popup{position:fixed;width:min(460px,calc(100vw - 32px));padding:36px 28px 28px;text-align:center;overflow:auto}
.signup-success-popup[open]{display:block}
.verified-signup .success-close{position:absolute;right:8px;top:8px}
.success-icon{display:block;margin:8px auto 20px;color:#592b91}
.signup-success-popup h2{font-size:26px;line-height:1.25;letter-spacing:-.02em;margin:0 0 12px}
.signup-success-popup p{color:#64566f;font-size:15px;line-height:1.6;margin:0 0 28px}
.verified-signup .signup-login-link{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:12px 20px;border-radius:10px;background:#592b91;color:#fff;font-size:15px;font-weight:600;text-decoration:none;box-sizing:border-box}
.signup-success-popup .signup-login-link{width:100%}
.signup-login-link:hover{background:#482174}.signup-login-link:focus-visible{outline:2px solid #592b91;outline-offset:4px}
@media(max-width:600px){.signup-success-popup{padding:32px 24px 24px}.signup-success-popup h2{font-size:24px}}
.verified-signup.signup-completed{margin:0;padding:0;background:transparent}

.verified-signup .signup-back{display:inline-flex;align-items:center;gap:8px;margin:0 0 4px;padding:8px 10px;min-height:44px;border-color:transparent;background:transparent;color:#592b91;font-family:inherit;font-size:14px;font-weight:600;box-shadow:none;text-decoration:none}
.verified-signup .signup-back:hover:not(:disabled){background:#f5f1fa;color:#482174}
.verified-signup .signup-back:focus-visible{outline:2px solid #592b91;outline-offset:3px}
.signup-back svg{flex-shrink:0}
</style>
