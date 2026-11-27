<script setup>
import {ref,onMounted} from 'vue'
import BrandLogo from '../BrandLogo.vue'
import Icon from '../Icon.vue'
import SubscriptionBilling from './SubscriptionBilling.vue'
import {request,csrf,decode} from './client'

const props=defineProps({invoice:{type:String,required:true},user:String})
const checking=ref(true),allowed=ref(false),switching=ref(false),error=ref('')
async function check(){
 checking.value=true;allowed.value=false;error.value=''
 try{
  const data=await request('account_billing','status')
  allowed.value=!!data.invoices?.some(row=>row.name===props.invoice)
 }catch{error.value='We could not check this checkout. Retry, or sign in with the account that started it.'}
 finally{checking.value=false}
}
async function switchAccount(){
 if(switching.value)return
 switching.value=true;error.value=''
 try{
  await decode(await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf()}}))
  const target='/campus?'+new URLSearchParams({checkout_invoice:props.invoice})+'#subscription'
  location.assign('/login?'+new URLSearchParams({'redirect-to':target}))
 }catch{error.value='Could not sign out. Please try again.';switching.value=false}
}
onMounted(check)
</script>
<template>
 <SubscriptionBilling v-if="allowed" standalone/>
 <main v-else class="checkout-entry">
  <section aria-labelledby="checkout-entry-title" :aria-busy="checking||switching">
   <BrandLogo/>
   <h1 id="checkout-entry-title">{{checking?'Checking your checkout…':'Continue with the correct account'}}</h1>
   <p v-if="checking" role="status">Confirming this payment belongs to your current account.</p>
   <template v-else>
    <p>This checkout is not available in your current account or workspace. It may belong to another account, or may no longer be available.</p>
    <div class="checkout-account"><Icon name="UserRound" :size="22"/><div><span>Signed in on this checkout site</span><strong>{{user}}</strong></div></div>
    <p>The secure checkout site has a separate login session. Sign in with the same account you used to choose the plan.</p>
    <p v-if="error" role="alert" class="checkout-error">{{error}}</p>
    <button type="button" class="checkout-primary" :disabled="switching" @click="switchAccount">{{switching?'Signing out…':'Sign in with another account'}}<Icon name="ArrowRight" :size="18"/></button>
    <button type="button" class="checkout-retry" :disabled="switching" @click="check">Check again</button>
    <a href="/campus">Return to my campus</a>
    <small>No payment is started from this screen.</small>
   </template>
  </section>
 </main>
</template>
<style scoped>
.checkout-entry{min-height:100dvh;box-sizing:border-box;background:#faf8fc;padding:48px 20px;display:grid;place-items:center;font-family:'Manrope Variable',sans-serif;color:#2c2038}.checkout-entry section{max-width:520px;box-sizing:border-box;width:100%;padding:36px;background:#fff;border:1px solid #e6ddec;border-radius:18px}.checkout-entry h1{font-size:28px;line-height:1.25;margin:28px 0 16px;font-weight:800;text-wrap:balance}.checkout-entry p{font-size:14px;line-height:1.75;color:#685b77}.checkout-account{display:flex;align-items:center;gap:12px;padding:18px;margin:22px 0;background:#f5effa;border-radius:10px;color:#572b91}.checkout-account span{display:block;font-size:12px;margin-bottom:5px}.checkout-account strong{font-size:14px;overflow-wrap:anywhere}.checkout-account div{min-width:0}.checkout-account svg{flex-shrink:0}.checkout-entry button{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;min-height:48px;padding:12px 18px;border-radius:10px;font:600 14px 'Manrope Variable',sans-serif;cursor:pointer;margin-top:12px}.checkout-primary{background:#572b91;border:1px solid #572b91;color:#fff}.checkout-primary:hover{background:#452174}.checkout-retry{background:#fff;border:1px solid #d9cbe7;color:#572b91}.checkout-entry button:disabled{opacity:.6;cursor:wait}.checkout-entry a{display:flex;align-items:center;justify-content:center;min-height:44px;margin-top:10px;color:#572b91;font-size:14px}.checkout-entry small{display:block;text-align:center;font-size:12px;color:#685b77;margin-top:18px}.checkout-entry .checkout-error{color:#9b2435;background:#fff1f4;padding:12px;border-radius:8px}.checkout-entry :is(a,button):focus-visible{outline:3px solid #9066ba;outline-offset:3px}@media(max-width:520px){.checkout-entry{padding:20px 14px}.checkout-entry section{padding:26px}.checkout-entry h1{font-size:25px}}
</style>
