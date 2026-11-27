<script setup>
import {ref} from 'vue'
import {request} from './client'
const parts=location.hash.replace('#password-confirm=','').split('.'),done=ref(false),busy=ref(false),error=ref('')
history.replaceState(null,'',location.pathname)
async function confirm(){busy.value=true;error.value='';try{await request('password_reset','confirm',{token:parts[0],proof:parts[1]});done.value=true}catch(e){error.value=e.message}finally{busy.value=false}}
</script>
<template><main class="confirmation-page"><h1>{{done?'Email confirmed':'Confirm your password reset'}}</h1><p v-if="done">You can close this tab and return to the SISU Settings tab where you requested the reset. Choose and save your new password there.</p><template v-else><p>Only confirm if you requested a password reset from your SISU account.</p><button :disabled="busy" @click="confirm">{{busy?'Confirming…':'Confirm password reset'}}</button></template><p v-if="error" role="alert">{{error}}</p></main></template>
<style scoped>.confirmation-page{max-width:560px;margin:12vh auto;padding:32px;border:1px solid #ded2ed;border-radius:24px;background:#faf7ff;color:#382548;font:16px/1.8 system-ui}.confirmation-page button{padding:14px 22px;border:0;border-radius:12px;color:white;background:#6332a1;font:inherit}</style>
