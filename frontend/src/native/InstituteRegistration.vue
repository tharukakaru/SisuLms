<script setup>
import {ref,onMounted,onBeforeUnmount,nextTick} from 'vue'
import {request} from './client'
const props=defineProps({institute:{type:Object,required:true}}),emit=defineEmits(['close'])
const dialog=ref(null),details=ref(null),result=ref(null),busy=ref(false),error=ref(''),confirmed=ref(false),language=ref('en')
let previousFocus
async function load(){busy.value=true;error.value='';try{details.value=await request('campus_join','details',{},'GET')}catch(e){error.value=e.message}finally{busy.value=false}}
async function register(){if(busy.value||!confirmed.value||!details.value?.phone_verified)return;busy.value=true;error.value='';try{result.value=await request('campus_join',props.institute.kind==='Teacher'?'register_teacher':'register_student',{profile:props.institute.name,...(props.institute.kind==='Institute'?{language:language.value}:{})});window.dispatchEvent(new Event('sisu-memberships'));window.dispatchEvent(new Event('sisu-notifications'))}catch(e){error.value=e.message}finally{busy.value=false}}
async function enter(){busy.value=true;error.value='';try{await request('campus_context','select',{institute:result.value.institute});window.location.assign('/campus')}catch(e){error.value=e.message;busy.value=false}}
function close(){if(!busy.value){dialog.value?.close();emit('close')}}
onMounted(async()=>{previousFocus=document.activeElement;await nextTick();dialog.value.showModal();load()})
onBeforeUnmount(()=>{dialog.value?.close();previousFocus?.focus?.()})
</script>
<template>
  <dialog ref="dialog" class="institute-registration" aria-labelledby="institute-register-title" @cancel.prevent="close">
    <button type="button" class="registration-close" aria-label="Close registration" :disabled="busy" @click="close">×</button>
    <span class="eyebrow">YOUR NEXT LEARNING CHAPTER</span>
    <h2 id="institute-register-title">{{result?'You’re registered!':'Register with '+institute.display_name}}</h2>
    <p v-if="busy" role="status">{{result?'Opening your institute…':'Please wait…'}}</p>
    <p v-if="error" class="registration-error" role="alert">{{error}}</p>
    <section v-if="result" role="status">
      <p>You’re registered with {{result.institute_title}}.</p>
      <p>Your student number</p>
      <strong class="student-number">{{result.student_number}}</strong>
      <p>Class enrollment is separate. Joining an institute does not unlock paid classes.</p>
      <button v-if="result.institute" type="button" class="button primary registration-pill-primary" :disabled="busy" @click="enter">Switch to this institute →</button>
    </section>
    <form v-else-if="details" @submit.prevent="register">
      <p>We’ll use your account details below. Update your profile first if anything needs correcting.</p>
      <div class="registration-fields">
        <label>First name<input :value="details.first_name" readonly autocomplete="off"></label>
        <label>Last name<input :value="details.last_name" readonly autocomplete="off"></label>
        <label>Email<input :value="details.email" readonly type="email" autocomplete="off"></label>
        <label>Verified phone<input :value="details.phone||'Verification needed'" readonly autocomplete="off"></label>
      </div>
      <p v-if="!details.phone_verified">Verify your mobile number in your profile before registering.</p>
      <label v-if="institute.kind==='Institute'" class="registration-select-label">Preferred language
        <select v-model="language">
          <option value="en">English</option>
          <option value="si">Sinhala</option>
          <option value="ta">Tamil</option>
        </select>
      </label>
      <label class="registration-consent">
        <input v-model="confirmed" type="checkbox" required :disabled="busy">
        <span>I confirm these details and want to register with {{institute.display_name}}.</span>
      </label>
      <p>You’ll receive a student number for this institute. Registration also follows this provider for news and class updates.</p>
      <button type="submit" class="button primary registration-pill-primary" :disabled="busy||!confirmed||!details.phone_verified">Register now →</button>
    </form>
    <button v-else-if="!busy" type="button" class="button subtle registration-pill-secondary" @click="load">Try again →</button>
  </dialog>
</template>
<style scoped>
.institute-registration {
  position: fixed;
  inset: 0;
  margin: auto;
  width: min(620px, calc(100vw - 32px));
  max-height: 90vh;
  overflow: auto;
  border: 1px solid #e9e8ef;
  border-radius: 28px;
  padding: 36px 32px;
  background: #ffffff;
  color: #19182e;
  box-sizing: border-box;
  font-family: 'Manrope', Inter, system-ui, sans-serif;
  box-shadow: 0 24px 64px rgba(25, 24, 46, 0.18);
}

.institute-registration::backdrop {
  background: rgba(25, 24, 46, 0.48);
  backdrop-filter: blur(4px);
}

.eyebrow {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: #56288d;
  text-transform: uppercase;
}

.institute-registration h2 {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #19182e;
  margin: 10px 32px 12px 0;
}

.institute-registration p {
  font-size: 14px;
  color: #787788;
  line-height: 1.6;
  margin: 12px 0;
}

.registration-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.registration-fields label,
.registration-select-label {
  display: grid;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #19182e;
}

.registration-fields input,
.registration-select-label select {
  box-sizing: border-box;
  width: 100%;
  min-height: 50px;
  padding: 13px 14px;
  border: 1px solid #e9e8ef;
  border-radius: 13px;
  background: #fcfcfe;
  color: #19182e;
  font: 400 14px 'Manrope', sans-serif;
}

.registration-consent {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: #787788;
  line-height: 1.55;
  margin: 16px 0;
}

.registration-consent input {
  width: 16px;
  height: 16px;
  margin-top: 3px;
  accent-color: #56288d;
}

.registration-close {
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

.student-number {
  display: block;
  font-size: 22px;
  font-weight: 800;
  padding: 16px 20px;
  background: #f2f0fc;
  color: #56288d;
  border-radius: 16px;
  margin: 8px 0 14px;
}

.registration-pill-primary,
.registration-pill-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 54px;
  padding: 12px 22px;
  border-radius: 27px;
  font: 700 14px 'Manrope', sans-serif;
  cursor: pointer;
  box-sizing: border-box;
}

.registration-pill-primary {
  background: #56288d;
  border: 1px solid #56288d;
  color: #ffffff;
}

.registration-pill-secondary {
  background: #f2f0fc;
  border: 1px solid #f2f0fc;
  color: #19182e;
}

.registration-pill-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.registration-error {
  padding: 12px 16px;
  border-radius: 13px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b !important;
}

@media (max-width: 640px) {
  .institute-registration {
    width: calc(100vw - 24px);
    max-height: calc(100dvh - 24px);
    padding: 24px 20px;
    border-radius: 24px;
  }

  .institute-registration h2 {
    font-size: 24px;
  }

  .registration-fields {
    grid-template-columns: 1fr;
    gap: 12px;
    margin: 14px 0;
  }

  .registration-fields input,
  .registration-select-label select {
    min-height: 48px;
    padding: 13px 14px;
    border-radius: 13px;
  }

  .registration-pill-primary,
  .registration-pill-secondary {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }
}
</style>
