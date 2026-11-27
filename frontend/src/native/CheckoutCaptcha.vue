<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue'
const props=defineProps({siteKey:{type:String,required:true}})
const emit=defineEmits(['token'])
const target=ref(null),error=ref(''),loading=ref(true)
let widget=null,disposed=false,timer
function reset(){if(widget!==null)window.grecaptcha?.reset(widget);emit('token','')}
defineExpose({reset})
async function mount(){
 loading.value=true;error.value=''
 try{
  if(!window.grecaptcha?.render){
   await new Promise((resolve,reject)=>{
    let script=document.querySelector('script[data-sisu-recaptcha]')
    if(!script){script=document.createElement('script');script.src='https://www.google.com/recaptcha/api.js?render=explicit';script.async=true;script.defer=true;script.dataset.sisuRecaptcha='true';document.head.appendChild(script)}
    const started=Date.now()
    function ready(){if(disposed){resolve();return}if(window.grecaptcha?.render){resolve();return}if(Date.now()-started>12000){script.remove();reject(Error('Verification could not load. Check your connection and try again.'));return}timer=setTimeout(ready,100)}ready()
   })
  }
  if(disposed)return
  widget=window.grecaptcha.render(target.value,{sitekey:props.siteKey,size:target.value.clientWidth<304?'compact':'normal',callback:token=>{error.value='';emit('token',token)},'expired-callback':()=>emit('token',''),'error-callback':()=>{emit('token','');error.value='Verification was interrupted. Please try again.'}})
 }catch(e){error.value=e.message}finally{loading.value=false}
}
function retry(){if(widget!==null){error.value='';reset()}else mount()}
onMounted(mount)
onBeforeUnmount(()=>{disposed=true;clearTimeout(timer);emit('token','')})
</script>
<template><section class="checkout-captcha" aria-label="Checkout verification"><p>Verify you’re human to open secure checkout.</p><div ref="target"></div><p v-if="loading" role="status">Loading Google verification…</p><div v-if="error" role="alert"><p>{{error}}</p><button type="button" @click="retry">Retry verification</button></div></section></template>
<style scoped>.checkout-captcha{width:100%;min-width:0;padding:14px 0}.checkout-captcha p{font-size:13px;line-height:1.6;color:#655773;margin:0 0 12px}.checkout-captcha button{min-height:44px;background:white;border:1px solid #d6c4e6;border-radius:8px;padding:8px 14px;color:#572b91;font:inherit}.checkout-captcha button:focus-visible{outline:2px solid #572b91;outline-offset:3px}</style>
