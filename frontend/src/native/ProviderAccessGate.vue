<script setup>
import {ref,onMounted} from 'vue'
import InstituteJoinPicker from './InstituteJoinPicker.vue'
import MobileVerification from './MobileVerification.vue'
import {request} from './client'
import SubscriptionBilling from './SubscriptionBilling.vue'
import TeacherSignupLayout from './TeacherSignupLayout.vue'
import PaymentRequired from './PaymentRequired.vue'
import {ArrowLeft,ArrowRight} from 'lucide-vue-next'
const joinMode=ref('')
const phoneVerified=ref(false)
const requestsPending=ref(false)
async function verifiedPhone(value){
  phoneVerified.value=value
  if(!value)return
  try{
    const data=await request('profiles','institute_join_options',{},'GET')
    requestsPending.value=data.requests.some(row=>row.status==='Pending')
    if(requestsPending.value)joinMode.value='Review requests'
  }catch{/* The request picker displays actionable errors when opened. */}
}
function back(){if(billingOpen.value){billingOpen.value=false}else if(joinMode.value){joinMode.value=''}else if(individual.value){individual.value=false}else if(window.history.length>1){window.history.back()}}
const props=defineProps({role:String,selectionOnly:Boolean,initialIndividual:Boolean,checking:Boolean,error:String});const emit=defineEmits(['changed','continue']);const panel=ref(null)
const billingOpen=ref(false)
const individual=ref(props.initialIndividual)
function continueIndividual(){if(props.selectionOnly)emit('continue');else individual.value=true}
onMounted(async()=>{panel.value?.focus();if(props.selectionOnly){try{const data=await request('profiles','me',{},'GET');await verifiedPhone(data.phone_verified)}catch{}}})
</script>
<template>
<PaymentRequired v-if="!selectionOnly&&!billingOpen&&(role!=='Teacher'||individual)" :checking="checking" :error="error" @back="back" @billing="billingOpen=true" @check="emit('changed')"/>
<TeacherSignupLayout v-else-if="role==='Teacher'" active class="teacher-workspace-layout">
  <main class="teacher-workspace-content">
    <section ref="panel" class="teacher-workspace-panel" tabindex="-1" aria-labelledby="teacher-workspace-title">
      <button type="button" class="workspace-back" @click="back"><ArrowLeft :size="13" aria-hidden="true"/>Back</button>
      <h1 id="teacher-workspace-title">{{requestsPending?'Your institute requests are under review':'Welcome to your teacher workspace'}}</h1>
      <MobileVerification v-if="selectionOnly&&!phoneVerified" onboarding @verified="verifiedPhone"/>
      <template v-if="(!selectionOnly||phoneVerified)&&!joinMode&&!individual">
        <p class="workspace-intro">Choose how you want to begin.</p>
        <nav class="workspace-options" aria-label="Teaching options">
          <button type="button" class="workspace-primary" @click="continueIndividual">Continue as individual teacher<ArrowRight :size="16" aria-hidden="true"/></button>
          <button type="button" class="workspace-secondary" @click="joinMode='Existing teacher confirmation'">Join your registered institute<ArrowRight :size="16" aria-hidden="true"/></button>
          <button type="button" class="workspace-apply" @click="joinMode='New application'">Apply to an institute<ArrowRight :size="16" aria-hidden="true"/></button>
        </nav>
        <slot/>
      </template>
      <InstituteJoinPicker v-else-if="(!selectionOnly||phoneVerified)&&joinMode" :key="joinMode" :purpose="joinMode" @back="joinMode=''"/>
      <SubscriptionBilling v-else-if="!selectionOnly||phoneVerified" standalone @changed="emit('changed')"/>
    </section>
  </main>
</TeacherSignupLayout>
<main v-else class="provider-gate"><div class="workspace-preview" inert aria-hidden="true"><header>SISU · {{role==='Teacher'?'Teacher':'Institute'}} workspace</header><nav>Overview · Classes · Students · Assignments</nav><div class="workspace-panels"><section v-for="title in ['Your classes','Learning activity','Upcoming sessions']" :key="title"><h2>{{title}}</h2><div class="preview-line"/><div class="preview-line"/></section></div></div><section ref="panel" class="subscription-overlay" tabindex="-1" aria-labelledby="gate-title"><button v-if="billingOpen" type="button" class="workspace-back" @click="back"><ArrowLeft :size="13" aria-hidden="true"/>Back</button><h1 id="gate-title">Welcome to your {{role==='Teacher'?'teacher':'institute'}} workspace</h1><p>{{role==='Teacher'?'Choose how you teach. Manage your own classes with an individual plan, or request access to an institute’s teaching workspace.':'Choose a plan for your institute to continue.'}}</p><nav v-if="role==='Teacher'" class="join-links"><button :aria-pressed="!joinMode" @click="joinMode=''"><strong>Teach independently</strong><span>Your classes, students and personal subscription.</span></button><button :aria-pressed="joinMode==='Existing teacher confirmation'" @click="joinMode='Existing teacher confirmation'"><strong>I teach at an institute</strong><span>Ask your institute to confirm your teaching access.</span></button><button :aria-pressed="joinMode==='New application'" @click="joinMode='New application'"><strong>Find an institute</strong><span>Apply to join a new teaching community.</span></button></nav><InstituteJoinPicker v-if="joinMode" :key="joinMode" :purpose="joinMode" @back="joinMode=''"/><SubscriptionBilling v-else standalone @changed="emit('changed')"/></section></main></template>
<style scoped>.join-links{display:flex;flex-wrap:wrap;gap:14px;margin:20px 0}.join-links button{background:none;border:0;color:#593092;text-decoration:underline;cursor:pointer;padding:8px}.provider-gate{min-height:100vh;background:#f6f3fb;padding:32px 16px;position:relative}.workspace-preview{position:fixed;inset:0;padding:40px;filter:blur(5px);opacity:.38;pointer-events:none}.workspace-preview header{font:700 26px system-ui}.workspace-preview nav{margin:28px 0}.workspace-panels{display:grid;grid-template-columns:repeat(3,1fr);gap:25px}.workspace-panels section{padding:30px;background:white;border-radius:20px;height:220px}.preview-line{height:20px;background:#e5dfec;margin:24px 0;border-radius:8px}.subscription-overlay{position:relative;max-width:960px;margin:auto;background:white;border-radius:22px;padding:28px;box-shadow:0 15px 80px #34234c30}.subscription-overlay>h1{font:700 26px system-ui;color:#39214d}.subscription-overlay:focus{outline:none}.subscription-overlay :deep(.billing-standalone){min-height:0;padding:0}.subscription-overlay :deep(.billing-page){max-width:100%}@media(max-width:600px){.subscription-overlay{padding:16px}.workspace-panels{grid-template-columns:1fr}}</style>

<style scoped>.join-links{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.join-links button{display:flex;flex-direction:column;gap:9px;text-align:left;text-decoration:none;padding:18px;border:1px solid #e5ddef;border-radius:16px;background:#fff;font:inherit;line-height:1.5}.join-links button[aria-pressed=true]{border-color:#6c6aee;background:#f3f1ff;box-shadow:0 0 0 1px #6c6aee}.join-links strong{font-size:14px}.join-links span{font-size:12px;color:#786c85}.join-links button:focus-visible{outline:3px solid #b9b5fa;outline-offset:3px}.subscription-overlay>p{color:#786c85;line-height:1.7;max-width:700px}@media(max-width:680px){.join-links{grid-template-columns:1fr}}</style>

<style scoped>
.teacher-workspace-content{display:flex;align-items:center;min-width:0;padding:48px 48px 48px 0;color:#19182e;font-family:'Manrope Variable',sans-serif}
.teacher-workspace-panel{width:100%;min-width:0;outline:none}
.workspace-back{display:flex;align-items:center;gap:4px;min-height:24px;width:fit-content;padding:0;border:0;background:none;color:#56288d;font:400 13px/24px 'Manrope Variable',sans-serif;cursor:pointer}
.workspace-back:hover{text-decoration:underline}
.teacher-workspace-panel h1{font:800 36px/1.2 'Manrope Variable',sans-serif;letter-spacing:-1.2px;margin:24px 0 20px;color:#19182e}
.workspace-intro{font-size:14px;line-height:24px;color:#78758b;margin:0 0 20px}
.workspace-options{display:grid;gap:20px}
.workspace-options button{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;min-height:54px;padding:14px 20px;border:0;border-radius:999px;font:700 14px/24px 'Manrope Variable',sans-serif;cursor:pointer}
.workspace-primary{background:#56288d;color:#fff}
.workspace-primary:hover{background:#462073}
.workspace-secondary{background:#f3effc;color:#19182e}
.workspace-secondary:hover{background:#eae2f8}
.workspace-options .workspace-apply{background:transparent;color:#19182e}
.workspace-options .workspace-apply:hover{color:#56288d;background:#fcfbfe}
.workspace-apply svg{color:#56288d}
.teacher-workspace-panel :is(button,a):focus-visible{outline:3px solid #8b61bb;outline-offset:4px}
.teacher-workspace-panel :deep(.billing-standalone){min-height:0;padding:0}
.teacher-workspace-panel :deep(.billing-page){max-width:100%}
@media(min-width:1000px) and (max-width:1250px){.teacher-workspace-content{padding-right:24px}.teacher-workspace-panel h1{font-size:32px}}
@media(max-width:999px){.teacher-workspace-content{padding:0;min-height:calc(100dvh - 210px)}}
@media(max-width:480px){.teacher-workspace-panel h1{font-size:30px;letter-spacing:-1px}.workspace-options button{font-size:13px}}
</style>
