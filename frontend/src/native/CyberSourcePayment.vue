<script setup>

import {ref,onMounted,onBeforeUnmount,nextTick} from 'vue'

import {request} from './client'

import {loadCheckoutLibrary,paymentMessage} from './cybersourceCheckout'

const props=defineProps({invoice:{type:String,required:true},kind:{type:String,default:'tuition'}})

const emit=defineEmits(['changed'])

const checkoutTargetId='cybs-checkout-'+crypto.randomUUID()
const paused=ref(false),popup=ref(false)

const available=ref(false),busy=ref(false),message=ref(''),attempt=ref(null),gatewayMode=ref('unavailable')

let client,checkout,disposed=false

onMounted(async()=>{try{const r=await request('cybersource','availability',{kind:props.kind,invoice:props.invoice});available.value=r.available;paused.value=!!r.paused;gatewayMode.value=r.mode||'unavailable'}catch{available.value=false}})

function cleanup(){try{checkout?.destroy()}catch{}try{client?.destroy()}catch{}checkout=null;client=null}

onBeforeUnmount(()=>{disposed=true;cleanup()})

async function verify(){busy.value=true;try{const r=await request('cybersource','reconcile',{attempt:attempt.value});message.value=paymentMessage(r,props.kind);if(r.status==='succeeded')emit('changed')}catch(e){message.value=e.message}finally{busy.value=false}}

async function pay(){

 if(paused.value){popup.value=true;return}

 let stage='session-request'

 busy.value=true;message.value='Opening secure checkout…'

 try{

  const r=await request('cybersource','start',{kind:props.kind,invoice:props.invoice})

  attempt.value=r.name

  if(!r.session){message.value=paymentMessage(r,props.kind);return}

  stage='library-load'

  const VAS=await loadCheckoutLibrary(r.session, r.mode)

  if(disposed)return

  stage='client-initialization'

  client=await VAS.UnifiedCheckout(r.session)

  stage='checkout-creation'

  checkout=await client.createCheckout({autoProcessing:true})

  // Result JWT is deliberately not used as payment proof. Backend searches its

  // own immutable reference and verifies the authenticated transaction report.

  stage='checkout-display'

  await nextTick()
  if(disposed)return
  await checkout.mount('#'+checkoutTargetId)

  stage='payment-verification'

  await request('cybersource','browser_event',{attempt:r.name,event:'completed'})

  await verify()

 }catch(e){

  const cancelled=/CANCEL|CLOSE/i.test(e?.reason||e?.name||'')

  const reason=String(e?.reason||e?.code||'')

  const safeReason=/^[A-Z][A-Z0-9_]{2,70}$/.test(reason)?reason:'UNSPECIFIED'

  const diagnostic=`${stage}: ${safeReason}`

  if(attempt.value){try{await request('cybersource','browser_event',{attempt:attempt.value,event:cancelled?'cancelled':'failed'})}catch{}}

  message.value=cancelled?'Checkout closed. Check payment status before trying again.':`Checkout could not finish (${diagnostic}). Check payment status before trying again.`

 }finally{cleanup();busy.value=false}

}

</script>

<template><div v-if="available||paused" class="cybs-payment"><button type="button" class="button primary small" :disabled="busy" @click="pay">Pay securely · LKR</button><button v-if="attempt" type="button" class="button subtle small" :disabled="busy" @click="verify">Check payment status</button><div v-if="popup" role="alertdialog" aria-modal="true" aria-label="Payment unavailable" class="payment-unavailable"><p>Online checkout is temporarily unavailable. No payment has been taken.</p><button type="button" @click="popup=false">Close</button></div><small v-if="message" role="status">{{message}}</small><small>{{gatewayMode==='sandbox'?'Sandbox: test payments only.':'Customer-authorized LKR payments only.'}} No automatic renewals.</small><div :id="checkoutTargetId" class="cybs-checkout-target"></div></div></template>

<style scoped>.cybs-payment{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.cybs-checkout-target{flex-basis:100%;width:100%;min-width:0}.cybs-payment small{flex-basis:100%;max-width:380px;white-space:normal;font-size:11px;line-height:1.6}</style>



<style scoped>.payment-unavailable{position:fixed;top:30%;left:50%;transform:translateX(-50%);width:min(480px,85vw);box-sizing:border-box;text-align:left;line-height:1.6;z-index:1000;padding:28px;background:white;color:#231c30;border:1px solid #ddd;border-radius:16px;box-shadow:0 0 0 100vmax #0006}</style>
