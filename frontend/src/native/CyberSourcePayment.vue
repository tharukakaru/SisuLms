<script setup>
import {ref,computed,onMounted,onBeforeUnmount,nextTick,watch} from 'vue'
import {request} from './client'
import {loadCheckoutLibrary,paymentMessage,reusableCheckout} from './cybersourceCheckout'
import Icon from '../Icon.vue'
import CheckoutCaptcha from './CheckoutCaptcha.vue'

const props=defineProps({invoice:{type:String,required:true},kind:{type:String,default:'tuition'},visible:{type:Boolean,default:true},review:Boolean})
const emit=defineEmits(['changed','screen-change'])
const checkoutTargetId='cybs-checkout-'+crypto.randomUUID()
const checkoutScreenId=checkoutTargetId+'-screen'
const formOpen=ref(false)
function showForm(open){formOpen.value=open;emit('screen-change',open)}
let screenObserver,screenResize,openingStarted=0
function observeScreen(){
 const element=document.getElementById(checkoutScreenId)
 const selection=document.getElementById(checkoutTargetId)
 if(!element||!selection)return
 // The SDK owns visibility and sizing of its cross-origin frame. Do not hide
 // its container while waiting for an SDK event (that prevents initial sizing).
 const sync=()=>{
  if(!props.visible)return
  const formVisible=element.getBoundingClientRect().height>5
  showForm(formVisible)
  if(preparing.value&&(formVisible||props.visible&&selection.getBoundingClientRect().height>5)){
   preparing.value=false;measure('payment UI visible',openingStarted)
  }
 }
 screenObserver=new MutationObserver(sync)
 screenObserver.observe(element.parentNode,{childList:true,subtree:true,attributes:true,attributeFilter:['style','hidden']})
 screenResize=new ResizeObserver(sync);screenResize.observe(element);screenResize.observe(selection);sync()
}
const paused=ref(false),popup=ref(false),available=ref(false),busy=ref(false),message=ref('')
const attempt=ref(null),gatewayMode=ref('unavailable'),retained=ref(false),blocked=ref(false),paid=ref(false)
let submissionGrant=null
let verificationTimer
const verificationChecks=ref(0),verificationIssue=ref(false)
function scheduleVerification(result){
 clearTimeout(verificationTimer)
 if(disposed||result.status!=='pending'||!(result.transaction_id||['processing','completed'].includes(result.browser_event))||verificationChecks.value>=12)return
 const delay=Math.max(15000,(Number(result.next_check_after||0)*1000-Date.now())+1000)
 verificationTimer=setTimeout(()=>{verificationChecks.value++;verify()},delay)
}
const heldStatus=ref(null),clock=ref(Date.now())
const preparing=ref(false),loadingText=ref(''),loadingSince=ref(0),retryLoading=ref(false)
const reloadRequired=ref(false)
const checkoutUrl=ref('')
const captcha=ref({required:false,configured:false,site_key:''}),captchaToken=ref(''),captchaWidget=ref(null)
const captchaNeeded=computed(()=>captcha.value.required&&!checkoutUrl.value&&!retained.value&&!(queuedContext?.session&&queuedContext.session_expires*1000>clock.value))
let session,queuedContext,disposed=false,generation=0,clockTimer=setInterval(()=>{clock.value=Date.now()},1000)
function loadingStep(text){preparing.value=true;loadingText.value=text;loadingSince.value=Date.now();clock.value=Date.now()}
function measure(stage,started){if(['localhost','checkout.localhost','127.0.0.1'].includes(location.hostname))console.debug('[SISU checkout timing]',stage,Math.round(performance.now()-started)+'ms')}
const remaining=computed(()=>heldStatus.value?.status==='pending'&&!heldStatus.value?.transaction_id&&!['processing','completed'].includes(heldStatus.value?.browser_event)?Math.max(0,Math.ceil(((heldStatus.value?.retry_after||0)*1000-clock.value)/1000)):0)
const retryCountdown=computed(()=>`${Math.floor(remaining.value/60)}:${String(remaining.value%60).padStart(2,'0')}`)
const displayMessage=computed(()=>heldStatus.value?paymentMessage(heldStatus.value,props.kind,clock.value):message.value)
const awaitingVerification=computed(()=>!paid.value&&heldStatus.value?.status==='pending'&&(!!heldStatus.value?.transaction_id||['processing','completed'].includes(heldStatus.value?.browser_event)))
const verificationPaused=computed(()=>awaitingVerification.value&&verificationChecks.value>=12&&!busy.value)
async function resumeVerification(){verificationChecks.value=0;await verify()}
const needsReview=computed(()=>heldStatus.value?.status==='review'&&!heldStatus.value?.resume_allowed)
const buttonLabel=computed(()=>checkoutUrl.value?'Continue to secure checkout':reloadRequired.value?'Reload page':paid.value?'Payment verified':busy.value?'Opening checkout…':heldStatus.value?.session_unavailable?'Retry opening checkout':retryLoading.value?'Retry loading checkout':retained.value?'Resume card checkout':remaining.value?`Retry available in ${retryCountdown.value}`:blocked.value?'Check and reopen checkout':props.review?'Continue to card payment':'Pay securely · LKR')
onMounted(async()=>{try{const r=await request('cybersource','availability',{kind:props.kind,invoice:props.invoice});captcha.value=r.captcha||{required:false,configured:false};available.value=r.available;paused.value=!!r.paused;gatewayMode.value=r.mode||'unavailable';checkoutUrl.value=r.checkout_url||'';if(checkoutUrl.value)message.value='Continue on the secure checkout site with this same invoice. You may need to sign in again. Opening checkout does not charge you.';await nextTick();if(!disposed&&props.review)observeScreen()}catch{available.value=false}})
function cleanup(){try{session?.destroy()}catch{}session=null;retained.value=false;showForm(false)}
function pause(){
 preparing.value=false
 // The parent hides this persistent dialog. Keep the SDK and its pending mount
 // intact: unmount/remount can leave orphaned provider frames and lose form state.
 // A full page refresh recovers the same unsubmitted attempt through the server.
}
watch(()=>props.visible,value=>{if(!value)pause()})
onBeforeUnmount(()=>{disposed=true;generation++;queuedContext=null;screenObserver?.disconnect();screenResize?.disconnect();clearInterval(clockTimer);clearTimeout(verificationTimer);cleanup()})
async function verify(){
 if(busy.value)return
 busy.value=true;verificationIssue.value=false
 try{const r=await request('cybersource','reconcile',{attempt:attempt.value});heldStatus.value=r;message.value=paymentMessage(r,props.kind);blocked.value=!r.retry_allowed&&r.status!=='failed';scheduleVerification(r);if(r.status==='succeeded'){paid.value=true;cleanup();emit('changed')}}
 catch(e){message.value=e.message;verificationIssue.value=true;if(heldStatus.value)scheduleVerification(heldStatus.value)}finally{busy.value=false}
}
async function pay(){
 if(busy.value||paid.value||remaining.value)return
 if(checkoutUrl.value){location.assign(checkoutUrl.value);return}
 if(reloadRequired.value){location.reload();return}
 if(paused.value){popup.value=true;return}
 if(captchaNeeded.value&&!captchaToken.value){message.value="Complete the verification checkbox to continue.";return}
 busy.value=true
 clearTimeout(verificationTimer);verificationChecks.value=0
 heldStatus.value=null
 retryLoading.value=false
 loadingStep('Preparing your secure checkout…')
 const started=performance.now()
 openingStarted=started
 const current=++generation
 let stage='session-request'
 try{
  if(!session?.canResume()){
   cleanup()
   let r=queuedContext?.session_expires*1000>Date.now()?queuedContext:await request('cybersource','start',{kind:props.kind,invoice:props.invoice,captcha_token:captchaToken.value})
   if(r.retry_allowed)r=await request('cybersource','start',{kind:props.kind,invoice:props.invoice,captcha_token:captchaToken.value})
   captchaWidget.value?.reset();captchaToken.value='';
   measure('session response',started)
   attempt.value=r.name;gatewayMode.value=r.mode||gatewayMode.value
   submissionGrant=r.submission_grant||null
   message.value=paymentMessage(r,props.kind)
   if(!r.session){heldStatus.value=r;blocked.value=!r.retry_allowed&&r.status!=='failed';scheduleVerification(r);if(r.status==='succeeded'){paid.value=true;emit('changed')}return}
   queuedContext=r
   // A response arriving after close is retained only in this component, never in storage.
   stage='library-load'
   loadingStep('Loading secure card checkout…')
   const libraryStarted=performance.now()
   const VAS=await loadCheckoutLibrary(r.session,r.mode)
   measure('library loaded',libraryStarted)
   if(disposed)return
   stage='client-initialization'
   loadingStep('Connecting to the payment provider…')
   const client=await VAS.UnifiedCheckout(r.session)
   // Collect first, then explicitly mark submission before processing. A close
   // during collection can resume; an ambiguous submitted payment cannot.
   const checkout=await client.createCheckout({autoProcessing:false})
   queuedContext=null
   checkout.on('mounted',()=>{if(disposed)return;if(!props.review)preparing.value=false;measure('checkout mount requested',openingStarted)})
   checkout.on('paymentMethodSelected',()=>{if(!disposed)showForm(true)})
   checkout.on('paymentMethodCancelled',()=>{if(!disposed)showForm(false)})
   session=reusableCheckout(client,checkout,r.session_expires)
   retained.value=true;blocked.value=false
  }
  if(current!==generation||!props.visible){message.value='Checkout is ready. Resume card checkout when you are ready.';return}
  stage='checkout-display'
  loadingStep('Opening your card payment options…')
  message.value='Choose Checkout with card to continue. Keep this browser tab open until you finish.'
  await nextTick()
  const outcome=await session.mount(props.review?{paymentSelection:'#'+checkoutTargetId,paymentScreen:'#'+checkoutScreenId}:'#'+checkoutTargetId)
  if(disposed||outcome.detached||current!==generation)return
  stage='payment-processing';retained.value=false;blocked.value=true
  preparing.value=false;message.value='Processing your payment. Keep this tab open; please do not pay again.'
  await request('cybersource','browser_event',{attempt:attempt.value,event:'processing',submission_grant:submissionGrant})
  await session.complete(outcome.result)
  stage='payment-verification'
  await request('cybersource','browser_event',{attempt:attempt.value,event:'completed'})
  cleanup();busy.value=false
  await verify()
 }catch(e){
  if(stage==='session-request'){captchaWidget.value?.reset();captchaToken.value=''}
  if(disposed||current!==generation)return
  const cancelled=/CANCEL|CLOSE/i.test(e?.reason||e?.code||e?.name||'')
  if(cancelled&&session?.canResume()){
   try{session.pause()}catch{cleanup()}
   retained.value=!!session?.canResume()
   message.value='Checkout closed. Payment is not completed. Resume card checkout when you are ready.'
  }else if(stage==='library-load'&&e?.code==='CHECKOUT_RELOAD_REQUIRED'){
   reloadRequired.value=true;blocked.value=false
   message.value='The secure checkout library was updated. Reload this page, then open your plan checkout again. No payment was submitted.'
  }else if(stage==='library-load'&&queuedContext?.session_expires*1000>Date.now()){
   retryLoading.value=true;blocked.value=false
   message.value='The secure checkout could not load. Check your connection, then retry here. Your existing checkout will be reused.'
  }else{
   queuedContext=null
   cleanup();blocked.value=!!attempt.value
   message.value=stage==='session-request'?(e.message||'Checkout could not be opened. Try again.'):'Checkout could not finish. Check payment status before trying again.'
  }
  if(attempt.value&&!retryLoading.value&&!reloadRequired.value)try{await request('cybersource','browser_event',{attempt:attempt.value,event:cancelled?'cancelled':'failed'})}catch{}
 }finally{if(current===generation){busy.value=false;preparing.value=false}}
}
</script>
<template><div v-if="available||paused" class="cybs-payment" :class="{'review-payment':review}">
 <CheckoutCaptcha v-if="captchaNeeded&&captcha.configured&&!paid&&!awaitingVerification&&!needsReview" ref="captchaWidget" :site-key="captcha.site_key" @token="captchaToken=$event"/>
 <p v-if="captchaNeeded&&!captcha.configured" role="alert">Checkout verification is awaiting configuration. Please contact SISU support.</p>
 <button v-if="!paid&&!needsReview&&!awaitingVerification&&!(review&&busy&&retained)" type="button" class="checkout-primary" :class="review ? '' : 'button primary small'" :disabled="busy||paid||remaining>0||(captchaNeeded&&!captchaToken)" @click="pay"><Icon v-if="review" :name="paid?'CircleCheck':remaining?'Clock3':'LockKeyhole'" :size="18"/><span>{{buttonLabel}}</span><Icon v-if="review&&!busy&&!paid&&!remaining" name="ArrowRight" :size="18"/></button>
 <section v-if="awaitingVerification||paid||needsReview" class="verification-state" :class="{'verification-success':paid,'verification-delayed':verificationPaused||needsReview}" role="status" aria-live="polite" aria-atomic="true">
  <span class="verification-symbol"><Icon v-if="paid" name="CircleCheck" :size="28"/><Icon v-else-if="verificationPaused||needsReview" name="Clock3" :size="27"/><span v-else class="checkout-spinner" aria-hidden="true"></span></span>
  <div><h3>{{paid?'Payment confirmed':needsReview?'Your payment needs review':verificationPaused?'Confirmation is taking longer':'Please wait…'}}</h3>
   <p>{{paid?'Your payment has been verified. Your access is now updated.':needsReview?'We could not confirm the result automatically. Contact SISU with your payment details before trying to pay again.':verificationPaused?'Your payment is still unconfirmed. You can resume verification without making another payment.':verificationIssue?'Connection interrupted. We’re automatically retrying verification.':'We’re confirming your payment securely. This window will update automatically.'}}</p>
   <span v-if="!paid" class="verification-reassurance"><Icon name="ShieldCheck" :size="15"/>Please don’t pay again while we confirm the result.</span>
   <button v-if="verificationPaused" type="button" class="verification-resume" @click="resumeVerification">Resume verification<Icon name="RotateCcw" :size="16"/></button>
  </div>
 </section>
 <button v-else-if="attempt&&!retained&&!paid&&!preparing" type="button" class="checkout-status-button" :class="review?'':'button subtle small'" :disabled="busy" @click="verify">{{busy?'Verifying…':'Verify previous attempt'}}</button>
 <div v-if="popup" role="alertdialog" aria-modal="true" aria-label="Payment unavailable" class="payment-unavailable"><p>Online checkout is temporarily unavailable. No payment has been taken.</p><button type="button" @click="popup=false">Close</button></div>
 <div v-if="preparing" class="checkout-loading" role="status" aria-live="polite"><span class="checkout-spinner" aria-hidden="true"></span><div><strong>{{loadingText}}</strong><p>{{clock-loadingSince>8000?'This is taking a little longer. Keep this tab open; you won’t be charged just for opening checkout.':'Your payment details stay with the secure payment provider.'}}</p></div></div>
 <p v-else-if="displayMessage&&!formOpen&&!awaitingVerification&&!paid&&!needsReview" class="checkout-message" role="status">{{displayMessage}}</p>
 <small v-if="!review||gatewayMode==='sandbox'">{{gatewayMode==='sandbox'?'Sandbox: test payments only.':'Customer-authorized LKR payments only.'}} No automatic renewals.</small>
 <div v-show="!formOpen" :id="checkoutTargetId" class="cybs-checkout-target"></div>
 <div v-if="review" :id="checkoutScreenId" class="cybs-checkout-screen"></div>
</div></template>
<style scoped>
.review-payment{gap:12px;margin:0}
.cybs-checkout-screen{width:100%;flex-basis:100%;min-width:0}.cybs-checkout-screen:deep(iframe){max-width:100%;border:0}
.checkout-loading{display:flex;align-items:flex-start;gap:12px;flex-basis:100%;padding:16px 0;min-height:72px;box-sizing:border-box;color:#51435f;font-size:14px;line-height:1.5}.checkout-loading strong{font-weight:600}.checkout-loading p{font-size:13px;margin:4px 0 0;color:#6b5f75}.checkout-spinner{width:18px;height:18px;flex-shrink:0;margin-top:2px;border:2px solid #dfd3ec;border-top-color:#572b91;border-radius:50%;animation:checkout-spin .8s linear infinite}@keyframes checkout-spin{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.checkout-spinner{animation:none}}
.cybs-payment.review-payment .checkout-primary{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:52px;padding:14px 18px;border-radius:10px;background:#572b91;color:#fff;border:0;font-size:15px;font-weight:650;line-height:1.5;box-shadow:none;cursor:pointer;transition:background .15s}
.review-payment .checkout-primary>span{flex:1;text-align:center}.cybs-payment.review-payment .checkout-primary:hover:not(:disabled){background:#452074}.cybs-payment.review-payment .checkout-primary:disabled{background:#eee7f5;color:#665475;cursor:default;opacity:1}
.review-payment button:focus-visible{outline:2px solid #7544a8;outline-offset:4px}
.review-payment .checkout-status-button{min-height:44px;font-size:14px;border:0;background:transparent;color:#572b91;padding:8px 0;text-decoration:underline;text-underline-offset:3px}
.review-payment .checkout-message{font-size:14px;color:#655773;line-height:1.6;margin:0;max-width:100%;overflow-wrap:anywhere}
.review-payment .cybs-checkout-target{margin-top:4px}.review-payment .cybs-checkout-target:empty{display:none}
</style>
<style scoped>.cybs-payment{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.cybs-checkout-target{flex-basis:100%;width:100%;min-width:0}.cybs-payment .checkout-message{flex-basis:100%;font-size:14px;line-height:1.6;margin:8px 0;white-space:normal}.cybs-payment small{flex-basis:100%;max-width:380px;white-space:normal;font-size:11px;line-height:1.6}</style>



<style scoped>.payment-unavailable{position:fixed;top:30%;left:50%;transform:translateX(-50%);width:min(480px,85vw);box-sizing:border-box;text-align:left;line-height:1.6;z-index:1000;padding:28px;background:white;color:#231c30;border:1px solid #ddd;border-radius:16px;box-shadow:0 0 0 100vmax #0006}</style>

<style scoped>
.cybs-payment .verification-state{display:flex;align-items:flex-start;gap:17px;width:100%;box-sizing:border-box;padding:24px 20px;margin:8px 0;background:#f7f3fc;border-radius:12px;color:#572b91}
.verification-symbol{width:44px;height:44px;display:grid;place-items:center;flex-shrink:0;background:#ebe1f5;border-radius:50%}.verification-symbol .checkout-spinner{width:24px;height:24px;margin:0;border-width:3px;border-color:#d6c5e7;border-top-color:#572b91}
.cybs-payment .verification-state h3{font-size:19px;font-weight:700;letter-spacing:-.02em;line-height:1.35;margin:0 0 7px;color:#382448}
.cybs-payment .verification-state p{font-size:14px;line-height:1.65;margin:0;color:#685573;max-width:48ch}
.verification-reassurance{display:flex;align-items:flex-start;gap:7px;margin-top:16px;font-size:12px;line-height:1.6;color:#6a557b}.verification-reassurance svg{flex-shrink:0;margin-top:2px}
.cybs-payment .verification-success{background:#edf7f1;color:#246b49}.verification-success .verification-symbol{background:#dceee3}.cybs-payment .verification-success h3{color:#24583d}.cybs-payment .verification-success p{color:#476653}
.cybs-payment .verification-delayed{background:#fff7e9}.verification-delayed .verification-symbol{background:#f5e8ce;color:#876022}
.verification-resume{display:inline-flex;align-items:center;gap:8px;margin-top:16px;padding:10px 14px;min-height:42px;border:1px solid #d6c4e6;border-radius:8px;background:white;color:#572b91;font:inherit;font-size:13px;font-weight:650;cursor:pointer}.verification-resume:hover{background:#eee6f6}.verification-resume:focus-visible{outline:2px solid #7544a8;outline-offset:3px}
@media(max-width:480px){.cybs-payment .verification-state{padding:20px 16px;gap:12px}.verification-symbol{width:36px;height:36px}.cybs-payment .verification-state h3{font-size:18px}.cybs-payment .verification-state p{font-size:13px}}
</style>
