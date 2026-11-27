<script setup>
import {ref,nextTick} from 'vue'
import BrandLogo from '../BrandLogo.vue'
import InstituteSetupLayout from './InstituteSetupLayout.vue'
import Icon from '../Icon.vue'
import MobileVerification from './MobileVerification.vue'
import ProviderProfileSetup from './ProviderProfileSetup.vue'
import InstituteJoinPicker from './InstituteJoinPicker.vue'
import {csrf,decode} from './client'
const props=defineProps({session:Object,unifiedTeacher:Boolean})
const emit=defineEmits(['completed'])
function verifiedPhone(value){verified.value=value;if(value&&props.unifiedTeacher&&props.session.onboarding_kind==='Teacher'&&props.session.provider_profile_required===false){emit('completed')}}
const confirmation=ref(null)
async function completed(){saved.value=true;if(props.session.onboarding_kind==='Institute'){emit('completed');return}if(props.unifiedTeacher&&props.session.onboarding_kind==='Teacher'){emit('completed');return}await nextTick();confirmation.value?.showModal()}
const verified=ref(false),saved=ref(false),busy=ref(false),error=ref('')
async function login(){
 if(!verified.value||!saved.value||busy.value)return
 busy.value=true;error.value=''
 try{await decode(await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf()}}));location.assign('/login?redirect-to=/campus')}
 catch(e){error.value=e.message;busy.value=false}
}
</script>
<template><component :is="session.onboarding_kind==='Institute'?InstituteSetupLayout:'div'" :title="verified?'Complete your institute profile':'Verify your mobile number'" :description="verified?'Add the details learners will see when they discover your institute.':'Confirm your mobile number to secure your institute administrator account.'" :step="verified?1:0"><section class="first-login" :class="{'institute-first-login':session.onboarding_kind==='Institute'}"><template v-if="session.onboarding_kind!=='Institute'"><BrandLogo/><h1>Let’s make this space yours.</h1><p>Complete these steps once to set up your account.</p></template>
<MobileVerification v-if="!verified" onboarding hide-heading @verified="verifiedPhone"/>
<ProviderProfileSetup v-if="verified&&!saved" :member="{user:session.user,full_name:session.user,role:session.onboarding_kind==='Institute'?'Admin':'Teacher'}" @completed="completed"/>
<dialog ref="confirmation" class="saved-dialog" aria-labelledby="saved-title" @cancel.prevent><button type="button" class="saved-close" aria-label="Close confirmation" @click="confirmation.close()"><Icon name="X" :size="20"/></button><span class="saved-check"><Icon name="Check" :size="26"/></span><h2 id="saved-title">Profile details saved successfully</h2><p>Your information is saved securely.</p><button v-if="session.teaching_path==='institute'" class="continue" @click="confirmation.close()">Continue to institute selection</button><button v-else class="continue" :disabled="busy" @click="login">Back to sign in</button><p v-if="error" role="alert">{{error}}</p></dialog>
<section v-if="verified&&saved" class="success" role="status" aria-live="polite"><h2>Profile details saved successfully</h2><p>Your profile and mobile number are saved.{{session.teaching_path==='institute'?' Choose your institutes below.':' You can return to login now.'}}</p></section>
<InstituteJoinPicker v-if="verified&&saved&&session.teaching_path==='institute'" purpose="New application" onboarding/>
<button v-else-if="verified&&saved" class="continue" :disabled="busy" @click="login">{{busy?'Returning to login…':'Back to login'}}</button>
<p v-if="error" role="alert">{{error}}</p></section></component></template>
<style scoped>.first-login{max-width:960px;margin:40px auto;padding:24px;font-family:'Manrope Variable',sans-serif;color:#211b31}.first-login>p{color:#787087}.success{background:#ecf8ef;color:#24633d;border:1px solid #c7e6d1;border-radius:16px;padding:22px;margin:24px 0}.continue{background:#56288d;color:white;border:0;border-radius:32px;padding:18px 30px;font-family:inherit;font-size:15px;font-weight:600;margin:24px 0;cursor:pointer}.continue:disabled{opacity:.45;cursor:not-allowed}</style>

<style scoped>.saved-dialog{position:fixed;inset:0;margin:auto;width:min(440px,calc(100vw - 40px));box-sizing:border-box;padding:30px;border:1px solid #c7e6d1;border-radius:20px;background:#effaf3;color:#24633d}.saved-dialog::backdrop{background:#211b3166}.saved-dialog h2{font-size:23px}.saved-dialog p{line-height:1.7}</style>

<style scoped>
.institute-first-login{max-width:760px;margin:0 auto;padding:0}.institute-first-login :deep(.setup-profile){margin:0;max-width:none;padding:32px}.saved-dialog{background:#fff;color:#2c2038;border:1px solid #e6ddec;padding:36px;text-align:center;max-height:calc(100dvh - 40px);overflow:auto}.saved-dialog h2{margin:20px 0 12px;line-height:1.3}.saved-dialog p{color:#685b77}.saved-close{position:absolute;top:12px;right:12px;display:grid;place-items:center;width:44px;height:44px;border:0;border-radius:10px;background:transparent;color:#685b77;cursor:pointer}.saved-check{display:grid;place-items:center;width:56px;height:56px;margin:0 auto;background:#eef8f1;border-radius:50%;color:#24754a}.saved-dialog .continue{width:100%;margin:12px 0 0;border-radius:10px;min-height:48px}.first-login :is(button,a):focus-visible{outline:3px solid #9066ba;outline-offset:3px}.institute-first-login .success{margin:0 0 24px}.institute-first-login>.continue{border-radius:10px}@media(max-width:600px){.institute-first-login :deep(.setup-profile){padding:20px}.saved-dialog{padding:32px 24px}}
</style>
