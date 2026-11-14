<script setup>
import {ref,onMounted,onUnmounted} from 'vue'
import {ArrowRight,LogIn,X} from 'lucide-vue-next'
import {endSession} from '../logout'
const props=defineProps({authenticated:Boolean})
const dialog=ref(null),busy=ref(false),error=ref('')
async function login(){
 if(busy.value)return
 busy.value=true;error.value=''
 try{
  if(props.authenticated)await endSession()
  window.location.assign('/login?redirect-to=/campus')
 }catch{error.value='We couldn’t open the login page. Please try again.';busy.value=false}
}
onMounted(()=>dialog.value?.showModal())
onUnmounted(()=>dialog.value?.close())
</script>
<template>
<dialog ref="dialog" class="existing-account-dialog" aria-labelledby="existing-account-title" aria-describedby="existing-account-description" @cancel.prevent="login">
  <button class="existing-close" type="button" aria-label="Close and go to login" :disabled="busy" @click="login"><X :size="22" aria-hidden="true"/></button>
  <LogIn class="existing-symbol" :size="40" :stroke-width="1.6" aria-hidden="true"/>
  <h2 id="existing-account-title">Account already exists</h2>
  <p id="existing-account-description">You already have a SISU account with this email. Log in to continue to your student campus.</p>
  <p v-if="error" role="alert" class="existing-error">{{error}}</p>
  <button class="existing-login" type="button" :disabled="busy" @click="login" autofocus>{{busy?'Opening login…':'Log in'}}<ArrowRight v-if="!busy" :size="18" aria-hidden="true"/></button>
</dialog>
</template>
<style scoped>
.existing-account-dialog{box-sizing:border-box;width:min(460px,calc(100vw - 32px));max-height:calc(100dvh - 32px);padding:44px 28px 28px;border:0;border-radius:16px;color:#292432;background:#fff;text-align:center;box-shadow:0 24px 72px #24113740}
.existing-account-dialog::backdrop{background:#241b35a6}
.existing-symbol{color:#592b91;margin:0 auto 20px;display:block}
.existing-account-dialog h2{font-size:26px;line-height:1.25;letter-spacing:-.025em;margin:0 0 14px;font-weight:800}
.existing-account-dialog p{font-size:15px;line-height:1.65;color:#71647e;margin:0 0 24px}
.existing-account-dialog button{font:inherit;cursor:pointer;min-height:48px}
.existing-account-dialog .existing-close{position:absolute;right:10px;top:10px;display:grid;place-items:center;width:44px;min-height:44px;margin:0;padding:0;border:0;background:transparent;color:#49345e;border-radius:10px}
.existing-account-dialog .existing-login{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;margin:0;padding:12px 20px;border:0;border-radius:11px;background:#592b91;color:#fff;font-weight:700}
.existing-account-dialog .existing-login:hover{background:#472075}
.existing-account-dialog button:focus-visible{outline:3px solid #bba2d8;outline-offset:3px}
.existing-account-dialog button:disabled{opacity:.65;cursor:wait}
.existing-account-dialog .existing-error{color:#a12532}
</style>
