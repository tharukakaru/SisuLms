<script setup>
import {ref,onMounted,onBeforeUnmount,nextTick} from 'vue'
import {request} from './client'
import VerifiedSignup from './VerifiedSignup.vue'
defineProps({user:String})
const dialog=ref(null),policy=ref(null),verified=ref(false),loading=ref(true),error=ref(''),success=ref(false)
let previousFocus
async function open(){previousFocus=document.activeElement;await nextTick();dialog.value?.showModal()}
function close(){dialog.value?.close();previousFocus?.focus?.()}
async function load(){loading.value=true;error.value='';try{const [state,p]=await Promise.all([request('registration','account_status',{},'GET'),request('portal_policy','public',{},'GET')]);verified.value=state.verified;policy.value=p;if(!state.verified)await open()}catch(e){error.value=e.message}finally{loading.value=false}}
function complete(){verified.value=true;success.value=true}
onMounted(load)
onBeforeUnmount(close)
</script>
<template><div v-if="!verified&&!loading" class="verification-banner"><span>Verify your account to follow teachers and register for learning.</span><button class="button primary" @click="open">Verify account</button></div><p v-if="error" role="alert">{{error}} <button @click="load">Try again</button></p><dialog ref="dialog" class="account-verification" aria-labelledby="verify-account-title" @cancel.prevent="close"><button class="verify-close" aria-label="Close verification" @click="close">×</button><template v-if="success"><h2 id="verify-account-title">Your account is verified!</h2><p>Your email, mobile number and profile are saved. You can now follow providers and register.</p><button class="button primary" @click="close">Back to dashboard</button></template><template v-else><h2 id="verify-account-title">Let’s verify your account</h2><p>Confirm your email, then your mobile number, and save your profile. Your dashboard is ready behind this window.</p><VerifiedSignup v-if="policy" :policy="policy" google-session @back="close" @verified="complete"/></template></dialog></template>
<style scoped>.verification-banner{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px;margin-bottom:20px;background:#f3effb;border:1px solid #ddd2ee;border-radius:16px}.account-verification{position:fixed;inset:0;margin:auto;width:min(920px,calc(100vw - 24px));max-height:90vh;overflow:auto;padding:28px;border:1px solid #ded5ed;border-radius:24px;background:var(--student-card,#fff);color:var(--student-ink,#322442)}.account-verification::backdrop{background:#21132b88}.verify-close{float:right;border:0;background:transparent;font-size:28px;cursor:pointer}.account-verification h2{margin-bottom:12px}.account-verification p{line-height:1.7}.account-verification :deep(.verified-signup){margin:16px 0;padding:0;max-width:none}.account-verification :deep(.verified-signup>h1){display:none}@media(max-width:600px){.verification-banner{align-items:start;flex-direction:column}.account-verification{padding:20px}}</style>
