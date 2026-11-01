<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue'
import {request} from './client'
import {loadCheckoutLibrary,paymentMessage} from './cybersourceCheckout'
const props=defineProps({invoice:{type:String,required:true},kind:{type:String,default:'tuition'}})
const emit=defineEmits(['changed'])
const paused=ref(false),popup=ref(false)
const available=ref(false),busy=ref(false),message=ref(''),attempt=ref(null)
let client,checkout,disposed=false
onMounted(async()=>{try{const r=await request('cybersource','availability',{kind:props.kind,invoice:props.invoice});available.value=r.available;paused.value=!!r.paused}catch{available.value=false}})
function cleanup(){checkout?.destroy();client?.destroy();checkout=null;client=null}
onBeforeUnmount(()=>{disposed=true;cleanup()})
async function verify(){busy.value=true;try{const r=await request('cybersource','reconcile',{attempt:attempt.value});message.value=paymentMessage(r);if(r.status==='succeeded')emit('changed')}catch(e){message.value=e.message}finally{busy.value=false}}
async function pay(){
 if(paused.value){popup.value=true;return}
 busy.value=true;message.value='Opening secure sandbox checkout…'
 try{
  const r=await request('cybersource','start',{kind:props.kind,invoice:props.invoice})
  attempt.value=r.name
  if(!r.session){message.value=paymentMessage(r);return}
  const VAS=await loadCheckoutLibrary()
  if(disposed)return
  client=await VAS.UnifiedCheckout(r.session)
  checkout=await client.createCheckout({autoProcessing:true})
  // Result JWT is deliberately not used as payment proof. Backend searches its
  // own immutable reference and verifies the authenticated transaction report.
  await checkout.mount()
  await request('cybersource','browser_event',{attempt:r.name,event:'completed'})
  await verify()
 }catch(e){
  const cancelled=/CANCEL|CLOSE/i.test(e.reason||e.name||'')
  if(attempt.value){try{await request('cybersource','browser_event',{attempt:attempt.value,event:cancelled?'cancelled':'failed'})}catch{}}
  message.value=cancelled?'Checkout closed. Check payment status before trying again.':'Checkout could not finish. Check payment status before trying again.'
 }finally{cleanup();busy.value=false}
}
</script>
<template><span v-if="available||paused" class="cybs-payment"><button type="button" class="button primary small" :disabled="busy" @click="pay">Pay online · sandbox</button><button v-if="attempt" type="button" class="button subtle small" :disabled="busy" @click="verify">Check payment status</button><div v-if="popup" role="alertdialog" aria-modal="true" aria-label="Payment unavailable" class="payment-unavailable"><p>Payment gateway isn�t connected yet. Please try again later.</p><button type="button" @click="popup=false">Close</button></div><small v-if="message" role="status">{{message}}</small><small>Test payments only. You approve every payment; no automatic renewals.</small></span></template>
<style scoped>.cybs-payment{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.cybs-payment small{flex-basis:100%;max-width:380px;white-space:normal;font-size:11px;line-height:1.6}</style>

<style scoped>.payment-unavailable{position:fixed;inset:30% 15% auto;z-index:1000;padding:28px;background:white;color:#231c30;border:1px solid #ddd;border-radius:16px;box-shadow:0 0 0 100vmax #0006}</style>
