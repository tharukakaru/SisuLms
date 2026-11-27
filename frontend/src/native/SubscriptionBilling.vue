<script setup>
import {computed,ref,onMounted,onBeforeUnmount,watch,nextTick} from 'vue'
import {request} from './client'
import Icon from '../Icon.vue'
import BrandLogo from '../BrandLogo.vue'
import UsageInvoices from './UsageInvoices.vue'
import SubscriptionPlanCard from '../pricing/BillingPlanCard.vue'
import CyberSourcePayment from './CyberSourcePayment.vue'
const props=defineProps({standalone:Boolean,onboarding:Boolean})
const emit=defineEmits(['changed'])
const data=ref(null),busy=ref(false),error=ref(''),notice=ref(''),showPlans=ref(false),showManage=ref(false)
const coreFeaturesOpen=ref(false)
const form=ref({plan:'Individual',billing_email:'',payment_method:'Card'})
const checkoutInvoice=ref(''),checkoutOpen=ref(false),checkoutFormOpen=ref(false)
const checkoutDialog=ref(null),checkoutClose=ref(null)
const checkoutBill=computed(()=>data.value?.invoices.find(b=>b.name===checkoutInvoice.value))
let checkoutReturnFocus,previousOverflow
watch(checkoutOpen,async open=>{
 if(open){checkoutReturnFocus=document.activeElement;previousOverflow=document.body.style.overflow;document.body.style.overflow='hidden';await nextTick();checkoutClose.value?.focus()}
 else{document.body.style.overflow=previousOverflow||'';checkoutReturnFocus?.focus()}
})
onBeforeUnmount(()=>{if(checkoutOpen.value)document.body.style.overflow=previousOverflow||''})
function checkoutKeys(event){
 if(event.key==='Escape'){event.preventDefault();checkoutOpen.value=false;return}
 if(event.key!=='Tab')return
 const controls=[...checkoutDialog.value.querySelectorAll('button:not([disabled]),a[href],input,select,textarea,iframe,[tabindex="0"]')].filter(el=>el.getClientRects().length)
 const first=controls[0],last=controls.at(-1)
 if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus()}
 else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus()}
}
const drafts=computed(()=>data.value?.invoices.filter(b=>b.status==='Draft')||[])
const history=computed(()=>[
 ...(data.value?.invoices.filter(b=>!['Draft','Void'].includes(b.status))||[]),
 ...(data.value?.failed_payments||[]).map(b=>({...b,name:b.invoice,attempt:b.name,status:'Failed'}))
].sort((a,b)=>String(b.creation).localeCompare(String(a.creation))))
function openCheckout(name){checkoutInvoice.value=name;checkoutOpen.value=true}
const account=computed(()=>data.value?.account)
const usd=(n,currency=account.value?.currency||'USD')=>new Intl.NumberFormat('en-US',{style:'currency',currency,minimumFractionDigits:2}).format(n/100)
const date=value=>value?new Intl.DateTimeFormat('en',{day:'numeric',month:'short',year:'numeric'}).format(new Date(String(value).replace(' ','T'))):'—'
const canInvoice=computed(()=>account.value?.billing_ready&&(account.value.state!=='Active'||account.value.renewal_available)&&!account.value.cancel_at_end)
async function load(){data.value=await request('account_billing','status');const a=data.value.account;form.value={plan:a.next_plan||a.plan,billing_email:a.billing_email||'',payment_method:a.payment_method||'Card'};if((props.standalone||a.onboarding_payment_required)&&!data.value.invoices.some(i=>['Draft','Unpaid'].includes(i.status)))showPlans.value=true}
async function run(action){busy.value=true;error.value='';notice.value='';try{await action()}catch(e){error.value=e.message}finally{busy.value=false}}
async function togglePlans(){if(showPlans.value){showPlans.value=false;return}await run(async()=>{await load();showPlans.value=true})}
async function save(){await run(async()=>{await request('account_billing','preferences',form.value);await load();notice.value='Billing preferences saved.';showManage.value=false})}
async function choose(plan){await run(async()=>{await request('account_billing','preferences',{...form.value,plan});await load();if(account.value.state!=='Active'){const bill=await request('account_billing','invoice',{start_paid:1});openCheckout(bill.invoice);await load()}showPlans.value=false;notice.value=account.value.next_plan?'Your new plan starts at the next renewal.':'Your plan is selected. Continue from your draft checkout below. Payment is not completed; access changes only after verified payment.'})}
async function invoice(){await run(async()=>{const r=await request('account_billing','invoice',{start_paid:1});openCheckout(r.invoice);await load();notice.value=r.message})}
async function cancel(){await run(async()=>{await request('account_billing','cancel',{cancel:!account.value.cancel_at_end});await load();notice.value=account.value.cancel_at_end?'Renewal cancelled. Your current access keeps its end date.':'Renewal resumed.'})}
async function download(name){await run(async()=>{const result=await request('account_billing','document',{invoice:name});const bytes=Uint8Array.from(atob(result.pdf),c=>c.charCodeAt(0));const url=URL.createObjectURL(new Blob([bytes],{type:'application/pdf'}));const a=document.createElement('a');a.href=url;a.download=result.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)})}
onMounted(async()=>{await run(async()=>{
 await load()
 const target=new URLSearchParams(location.search).get('checkout_invoice')
 if(!target)return
 const bill=data.value.invoices.find(b=>b.name===target)
 if(!bill){error.value='This checkout belongs to a different account or is no longer available. Sign in with the account that created it.';return}
 if(['Draft','Unpaid'].includes(bill.status))openCheckout(bill.name)
 else notice.value=bill.status==='Paid'?'This invoice is already paid. Your payment will not be requested again.':'This checkout is no longer payable. Select your current plan checkout below.'
})})
</script>
<template>
 <main class="billing-page" :class="{'billing-standalone':standalone,'billing-onboarding':onboarding,'billing-comparing':showPlans}" :aria-busy="busy">
  <header v-if="standalone&&!onboarding" class="billing-entry"><BrandLogo/><div><a href="/me">Account settings</a><a href="/api/method/logout">Sign out</a></div></header>
  <header class="billing-heading"><div><h2 v-if="onboarding">Subscription details</h2><h1 v-else>Your billing</h1><p>{{onboarding?'Your plan, payment details and receipts.':'Manage your subscription and download your invoices.'}}</p></div><button class="billing-button billing-refresh" :disabled="busy" @click="run(async()=>{await load();emit('changed')})"><Icon name="RotateCcw" :size="16"/>{{busy?'Updating…':'Refresh billing'}}</button></header>
  <p v-if="error" class="billing-message error" role="alert">{{error}}</p><p v-if="notice" class="billing-message" role="status">{{notice}}</p>
  <p v-if="!account&&!error" role="status">Loading your billing…</p>
  <template v-if="account">
   <UsageInvoices v-if="account.role!=='Student'"/>
   <section v-if="standalone&&account?.state==='Active'" class="billing-success" aria-labelledby="billing-success-title">
    <div class="billing-success-copy" role="status">
     <span class="billing-success-icon"><Icon name="CircleCheck" :size="28"/></span>
     <div><h2 id="billing-success-title">Payment successful</h2><p>Your plan payment has been verified.</p></div>
    </div>
    <a class="billing-dashboard-button" href="/campus"><span>Continue to dashboard</span><Icon name="ArrowRight" :size="22"/></a>
   </section>
   <div class="billing-summary-grid"><section class="billing-section billing-plan-panel" :class="{'plans-expanded':showPlans}" aria-labelledby="your-plan">
    <div class="billing-section-heading"><h2 id="your-plan">Your plan</h2><span class="billing-status" :class="{'is-paid':account.state==='Active','is-trial':account.state==='Trial'}"><Icon v-if="account.state==='Active'" name="CircleCheck" :size="14"/>{{account.state}}</span></div>
    <div class="billing-plan-row billing-current-plan"><div class="billing-plan-identity"><span class="billing-plan-icon"><Icon name="Package" :size="25"/></span><div><h3>SISU {{account.plan}}</h3><p>Monthly subscription</p></div></div><div class="billing-plan-price" v-if="account.monthly_minor!=null"><strong>{{usd(account.monthly_minor)}}</strong><span>/ month</span></div><p v-else>Your subscription price is being confirmed.</p></div>
    <div class="billing-renewal-row"><div class="billing-renewal-date"><Icon name="CalendarDays" :size="20"/><div><span>{{!account.paid_until&&account.state!=='Trial'?'Subscription begins':account.state==='Trial'?'Free trial ends':account.cancel_at_end?'Access until':'Renewal date'}}</span><strong>{{!account.paid_until&&account.state!=='Trial'?'After payment is confirmed':date(account.state==='Trial'?account.trial_until:account.paid_until)}}</strong></div></div><button v-if="account.role!=='Student'" class="billing-button billing-primary-button" :disabled="busy" :aria-expanded="showPlans" @click="togglePlans">{{showPlans?'Close plans':'View plans'}}<Icon :name="showPlans?'ChevronUp':'ArrowRight'" :size="16"/></button><span v-else class="billing-label">Student subscription</span></div>
    <div v-if="account.next_plan" class="billing-scheduled"><Icon name="Clock3" :size="18"/><div><strong>{{account.next_plan}} starts at renewal</strong><p v-if="account.next_monthly_minor!=null">{{usd(account.next_monthly_minor)}} / month<span v-if="account.paid_until"> · From {{date(account.paid_until)}}</span></p></div></div>
    <div v-if="account.renewal_available&&account.available&&!account.cancel_at_end" class="billing-scheduled" role="status"><Icon name="CalendarDays" :size="18"/><div><strong>Renewal is open</strong><p>Renew now and keep your remaining days. Your next month starts on {{date(account.access_ends_at)}}.</p><button v-if="canInvoice&&!drafts.length" class="billing-button billing-primary-button" :disabled="busy" @click="invoice">Renew plan<Icon name="ArrowRight" :size="16"/></button></div></div>
    <p v-else-if="account.state==='Active'&&!account.cancel_at_end&&account.renewal_opens_at" class="billing-caption">Renewal opens on {{date(account.renewal_opens_at)}} — four days before your access ends.</p>
    <p v-if="!account.available" class="billing-caption">{{onboarding?'Your institute workspace opens after payment is confirmed.':'Your subscription needs attention. Your workspace reopens once payment is confirmed.'}}</p>
    <section v-if="showPlans" class="billing-plan-selection" aria-label="Choose your plan"><header class="plan-selection-heading"><h2>Choose your plan</h2><p>Compare all four plans and explore their included features.</p></header><div class="billing-plans" aria-label="Available subscription plans"><SubscriptionPlanCard v-for="p in data.plans" :key="p.plan" :plan="p" :expanded="coreFeaturesOpen" @update:expanded="coreFeaturesOpen=$event" :currency="account.currency||'LKR'" :selected="p.plan===(account.next_plan||account.plan)" :disabled="busy||!account.billing_ready" @choose="choose"/><p class="billing-caption">Changes to a paid plan take effect at your next renewal.</p></div></section>
   </section>
   <section class="billing-section billing-payment-panel" aria-labelledby="payment-details">
    <div class="billing-section-heading"><h2 id="payment-details">Payment details</h2><button class="billing-link" :aria-expanded="showManage" @click="showManage=!showManage">{{showManage?'Close':'Manage'}}</button></div>
    <div class="billing-payment-row"><span class="billing-payment-icon"><Icon :name="account.payment_method==='Bank transfer'?'Building2':'CreditCard'" :size="25"/></span><div><p class="billing-primary">{{account.payment_method||'Card'}}</p><p class="billing-caption">Preferred payment method</p></div></div>
    <div class="billing-email"><span>Billing email</span><p>{{account.billing_email||'Add an email to receive your invoices.'}}</p></div>
    <p class="billing-payment-note"><Icon name="ShieldCheck" :size="17"/><span>{{data.gateway_ready?'Every payment needs your approval. No automatic charges.':'Online payments coming soon.'}}</span></p>
    <form v-if="showManage" class="billing-manage" @submit.prevent="save"><label for="billing-email">Invoice email<input id="billing-email" v-model="form.billing_email" type="email" required autocomplete="email"></label><label for="payment-preference">Preferred payment method<select id="payment-preference" v-model="form.payment_method"><option>Card</option><option>Bank transfer</option></select></label><p class="billing-caption">Saving a preference does not charge you. Online checkout appears only when configured; every payment needs your approval.</p><p v-if="form.payment_method==='Bank transfer'" class="billing-caption bank-instructions">{{data.bank_instructions||'Contact SISU for bank transfer details before sending a payment.'}}</p><div class="billing-actions"><button class="billing-button" :disabled="busy">Save changes</button><button type="button" class="billing-link" :disabled="busy" @click="cancel">{{account.cancel_at_end?'Resume renewal':'Cancel renewal'}}</button></div></form>
   </section>
   </div>
   <section v-if="drafts.length" class="billing-section" aria-labelledby="draft-checkouts"><h2 id="draft-checkouts">Your plan checkout</h2><article v-for="bill in drafts" :key="bill.name" class="billing-plan-row"><div><h3>{{bill.plan}} · {{usd(bill.amount_minor,bill.currency)}}</h3><p>Payment not completed · Draft</p><p class="billing-caption">This is an unfinished checkout, not an unpaid bill. Your plan activates after payment is verified.</p></div><button class="billing-button" :disabled="busy" @click="openCheckout(bill.name)">Continue checkout</button></article></section>
   <section class="billing-section billing-history" aria-labelledby="invoice-history">
    <div class="billing-section-heading"><div><h2 id="invoice-history">Invoices & receipts</h2><p>Your payment history, all in one place.</p></div><button v-if="canInvoice&&!drafts.length&&!account.renewal_available" class="billing-button" :disabled="busy" @click="invoice">{{account.state==='Trial'?'Start paid plan':'Buy plan'}}</button><button v-else-if="canInvoice&&!drafts.length&&!account.available" class="billing-button" :disabled="busy" @click="invoice">Renew plan</button></div>
    <div v-if="!history.length" class="billing-empty"><Icon name="FileText" :size="22"/><div><p class="billing-primary">No invoices yet</p><p>Completed payments and rejected card payments will appear here.</p></div></div>
    <div v-else class="billing-table"><table><thead><tr><th scope="col">Date</th><th scope="col">Invoice</th><th scope="col">Amount</th><th scope="col">Status</th><th scope="col"><span class="sr-only">Download</span></th></tr></thead><tbody><tr v-for="bill in history" :key="bill.attempt||bill.name"><td data-label="Date">{{date(bill.creation||bill.period_start)}}</td><td data-label="Invoice" class="billing-invoice-number">{{bill.receipt_number || (bill.status==='Failed'?'Not issued':'Awaiting payment')}}</td><td data-label="Amount" class="billing-invoice-amount">{{usd(bill.amount_minor,bill.currency)}}</td><td data-label="Status"><span class="billing-status" :class="{'is-paid':bill.status==='Paid','is-failed':bill.status==='Failed'}"><Icon v-if="bill.status==='Paid'" name="CircleCheck" :size="14"/>{{bill.status}}</span></td><td class="billing-download-cell"><span v-if="bill.status==='Failed'" class="billing-caption">Payment rejected</span><button v-else-if="bill.status==='Paid'" class="billing-button billing-download" :aria-label="'Download receipt '+bill.receipt_number" :disabled="busy" @click="download(bill.name)"><Icon name="Download" :size="16"/>Download receipt</button><button v-if="bill.status==='Unpaid'" class="billing-button" @click="openCheckout(bill.name)">Open checkout</button></td></tr></tbody></table><p v-if="history.some(bill=>bill.status==='Void')" class="billing-caption">Void means a checkout was cancelled or replaced. It is not a payment or an outstanding bill.</p><p class="billing-caption">Invoices and receipts download as PDF files. Only submitted, rejected card payments appear as Failed.</p></div>
   </section>
   <footer class="billing-footer"><span>Prices in {{account.currency}}. Class tuition is billed separately.</span><span><Icon name="FileText" :size="15"/>Receipts available as PDF</span></footer>
  </template>
 <div v-if="checkoutInvoice" v-show="checkoutOpen" class="subscription-checkout" :class="{'checkout-form-open':checkoutFormOpen}" @keydown="checkoutKeys">
  <section ref="checkoutDialog" role="dialog" aria-modal="true" aria-labelledby="checkout-heading" aria-describedby="checkout-description">
   <header class="checkout-header">
    <div class="checkout-heading-icon"><Icon name="CreditCard" :size="24"/></div>
    <button ref="checkoutClose" type="button" class="checkout-close" aria-label="Close payment checkout" @click="checkoutOpen=false"><Icon name="X" :size="21"/></button>
    <h2 id="checkout-heading">Complete your payment</h2>
    <p id="checkout-description">Review your plan, then continue to card checkout.</p>
   </header>
   <div class="checkout-body">
    <dl v-if="checkoutBill" class="checkout-summary">
     <div class="checkout-plan"><dt>Selected plan</dt><dd>SISU {{checkoutBill.plan}}<span>Monthly subscription</span></dd></div>
     <div class="checkout-total"><dt>Due today</dt><dd>{{usd(checkoutBill.amount_minor,checkoutBill.currency)}}</dd></div>
    </dl>
    <p class="checkout-renewal"><Icon name="CircleCheck" :size="16"/>One payment. No automatic renewals.</p>
    <CyberSourcePayment :key="checkoutInvoice" kind="subscription" :invoice="checkoutInvoice" :visible="checkoutOpen" review @changed="run(async()=>{await load();emit('changed')})" @screen-change="checkoutFormOpen=$event"/>
   </div>
   <footer class="checkout-footer"><Icon name="ShieldCheck" :size="19"/><p>Your plan activates after payment is verified.<br><span>Close this popup to pause. Keep this browser tab open to resume.</span></p></footer>
  </section>
 </div></main>
</template>
<style scoped>
.billing-page{max-width:1080px;margin:0 auto;color:var(--student-ink,#29252f);--billing-line:var(--student-border,#e8e5ed);--billing-muted:var(--student-muted,#797480);--billing-surface:var(--student-card,#fff)}
.billing-heading{margin:12px 0 42px}.billing-heading h1{font-size:clamp(28px,3vw,38px);letter-spacing:-1.2px;margin:0 0 12px;line-height:1.2}.billing-page p{font-size:14px;line-height:1.65;margin:5px 0;color:var(--billing-muted)}.billing-section{margin:0 0 32px}.billing-section-heading{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:16px}.billing-section h2{font-size:18px;margin:0;font-weight:700;letter-spacing:-.35px}.billing-page h3{font-size:16px;margin:0 0 4px;color:inherit}.billing-status,.billing-label{font-size:12px;color:var(--billing-muted)}.billing-status{padding:5px 10px;border-radius:7px;background:color-mix(in srgb,currentColor 6%,transparent)}.billing-plan-row,.billing-payment-row{display:flex;align-items:center;justify-content:space-between;gap:20px;border:1px solid var(--billing-line);background:var(--billing-surface);border-radius:16px;padding:23px 25px}.billing-payment-row{border-radius:12px}.billing-button{font:inherit;font-size:13px;font-weight:600;border:1px solid var(--billing-line);background:color-mix(in srgb,var(--student-ink,#30233f) 5%,var(--billing-surface));color:inherit;border-radius:9px;padding:10px 16px;cursor:pointer;white-space:nowrap}.billing-button:hover{background:color-mix(in srgb,var(--student-ink,#30233f) 10%,var(--billing-surface))}.billing-link{display:inline-flex;align-items:center;gap:7px;font:inherit;font-size:12px;font-weight:600;background:none;border:0;padding:5px 0;color:var(--student-ink,#30233f);cursor:pointer}.billing-link:hover{text-decoration:underline}.billing-page button:focus-visible{outline:2px solid #815ab1;outline-offset:4px}.billing-page button:disabled{opacity:.5;cursor:default}.billing-page .billing-caption{font-size:12px;color:var(--billing-muted);margin-top:12px}.billing-page .billing-primary{color:var(--student-ink,#29252f);font-weight:600}.billing-plans{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:20px}.billing-plans article{border:1px solid var(--billing-line);border-radius:12px;padding:18px}.billing-plans article button{margin-top:14px}.billing-plans>.billing-caption{grid-column:1/-1;margin:0}.billing-manage{padding:22px 0;max-width:540px}.billing-manage label{display:grid;gap:8px;font-size:13px;margin-bottom:18px}.billing-manage input,.billing-manage select{font:inherit;color:inherit;background:var(--billing-surface);border:1px solid var(--billing-line);border-radius:9px;padding:12px;width:100%;box-sizing:border-box}.billing-actions{display:flex;align-items:center;gap:22px;margin-top:20px}.bank-instructions{white-space:pre-line}.billing-empty{display:flex;align-items:center;gap:17px;border:1px solid var(--billing-line);border-radius:12px;padding:25px;color:var(--billing-muted)}.billing-empty p{font-size:13px}.billing-table{overflow-x:auto}.billing-table table{width:100%;border-collapse:collapse;font-size:13px}.billing-table th{text-align:left;font-size:11px;font-weight:500;color:var(--billing-muted)}.billing-table td,.billing-table th{padding:15px 12px;border-bottom:1px solid var(--billing-line);white-space:nowrap}.billing-table td:first-child,.billing-table th:first-child{padding-left:0}.billing-table td:last-child{text-align:right}.billing-footer{display:flex;align-items:center;justify-content:space-between;gap:16px;border-top:1px solid var(--billing-line);padding-top:20px;font-size:11px;color:var(--billing-muted)}.billing-message{padding:12px 16px;border:1px solid var(--billing-line);border-radius:10px;margin-bottom:20px!important}.billing-standalone{padding:40px 28px;min-height:100vh}.billing-entry{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:50px}.billing-entry>div{display:flex;gap:18px}.billing-entry a{color:inherit;font-size:13px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}@media(max-width:700px){.billing-heading{margin-bottom:30px}.billing-plans{grid-template-columns:1fr 1fr}.billing-plan-row,.billing-payment-row{padding:18px;flex-wrap:wrap}.billing-footer,.billing-entry{flex-wrap:wrap}.billing-table{max-width:100%}.billing-standalone{padding:24px 16px}.billing-plans article{padding:14px}.billing-label{display:none}}
</style>

<style scoped>
.billing-plans{grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin-top:26px}.billing-plans .subscription-plan-card{position:relative;display:flex;flex-direction:column;overflow:hidden;padding:27px;border-radius:20px;border:1px solid color-mix(in srgb,var(--plan-color) 24%,var(--billing-surface,#fff));background:linear-gradient(155deg,color-mix(in srgb,var(--plan-color) 10%,var(--billing-surface,#fff)),var(--billing-surface,#fff) 60%);box-shadow:0 7px 24px #291d3d07;transition:transform .18s,box-shadow .18s}.subscription-plan-card:before{content:'';position:absolute;top:0;left:0;right:0;height:5px;background:var(--plan-color)}.billing-plans .subscription-plan-card:hover{transform:translateY(-3px);box-shadow:0 12px 30px #291d3d12}.billing-plans .subscription-plan-card.chosen{outline:2px solid var(--plan-color);outline-offset:2px}.plan-card-top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}.plan-emblem{display:grid;place-items:center;width:50px;height:50px;border-radius:15px;color:var(--plan-color);background:color-mix(in srgb,var(--plan-color) 13%,var(--billing-surface,#fff))}.plan-selected{display:flex;align-items:center;gap:5px;padding:6px 9px;font-size:10px;font-weight:650;border-radius:30px;color:var(--plan-color);background:color-mix(in srgb,var(--plan-color) 10%,var(--billing-surface,#fff))}.billing-plans .subscription-plan-card h3{font-size:24px;margin:0 0 10px}.billing-plans .subscription-plan-card>p{font-size:13px;line-height:1.7}.subscription-plan-card ul{list-style:none;padding:0;margin:20px 0;display:grid;gap:11px}.subscription-plan-card li{display:flex;align-items:flex-start;gap:9px;font-size:12px;line-height:1.6;text-transform:capitalize}.subscription-plan-card li svg{flex-shrink:0;margin-top:2px;color:var(--plan-color)}.plan-price{margin-top:auto;padding-top:20px;border-top:1px solid color-mix(in srgb,var(--plan-color) 15%,var(--billing-surface,#fff));display:flex;align-items:baseline;flex-wrap:wrap;gap:8px}.plan-price strong{font-size:30px;letter-spacing:-.04em}.plan-price span{font-size:12px;color:var(--billing-muted)}.billing-plans .subscription-plan-card .billing-button{width:100%;min-height:43px;margin-top:20px;background:var(--plan-color);border-color:var(--plan-color);color:#fff;font-weight:650;border-radius:11px}.billing-plans .subscription-plan-card .billing-button:disabled{opacity:.65}.billing-plan-row{border-radius:16px;background:linear-gradient(115deg,var(--student-soft,#f2eafa),var(--billing-surface,#fff));border:1px solid var(--billing-line)}@media(max-width:550px){.billing-plans{grid-template-columns:1fr}.billing-plans .subscription-plan-card{padding:23px}}@media(prefers-reduced-motion:reduce){.billing-plans .subscription-plan-card:hover{transform:none}}
</style>

<style scoped>
.billing-plans{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:18px}.billing-plans .subscription-plan-card{padding:17px 15px;border-radius:12px;background:var(--billing-surface,#fff);border-color:color-mix(in srgb,#716879 25%,var(--billing-surface,#fff));box-shadow:none}.subscription-plan-card:before{height:3px}.billing-plans .subscription-plan-card:hover{transform:none;box-shadow:0 4px 12px #2117290a}.billing-plans .subscription-plan-card.chosen{outline:1px solid #79529c;outline-offset:0;background:color-mix(in srgb,#79529c 6%,var(--billing-surface,#fff))}.plan-card-top{margin-bottom:12px;gap:6px}.plan-emblem{width:32px;height:32px;border-radius:8px;background:color-mix(in srgb,var(--plan-color) 9%,var(--billing-surface,#fff))}.plan-emblem :deep(svg){width:18px;height:18px}.plan-selected{font-size:9px;padding:4px 6px;border-radius:5px}.billing-plans .subscription-plan-card h3{font-size:18px;margin-bottom:6px}.billing-plans .subscription-plan-card>p{font-size:11px;line-height:1.55}.subscription-plan-card ul{margin:13px 0;gap:7px}.subscription-plan-card li{font-size:11px;line-height:1.45;gap:6px}.subscription-plan-card li svg{width:13px;height:13px}.plan-price{padding-top:12px;gap:5px}.plan-price strong{font-size:22px;letter-spacing:-.025em}.plan-price span{font-size:10px}.billing-plans .subscription-plan-card .billing-button{min-height:33px;margin-top:12px;padding:7px 10px;border-radius:7px;font-size:11px;background:var(--plan-color);border-color:var(--plan-color)}.billing-plan-row{border-radius:10px;padding:16px;background:color-mix(in srgb,#695374 5%,var(--billing-surface,#fff))}@media(max-width:1000px){.billing-plans{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:440px){.billing-plans{grid-template-columns:1fr}.billing-plans .subscription-plan-card{padding:16px}}
</style>

<style scoped>.billing-plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}.billing-plans>.billing-caption{grid-column:1/-1}</style>
<style scoped>
.subscription-checkout{position:fixed;inset:0;z-index:1500;background:#21162b99;display:grid;place-items:center;padding:24px;box-sizing:border-box}
.subscription-checkout>section{width:min(600px,100%);max-height:calc(100dvh - 48px);display:flex;flex-direction:column;overflow:hidden;background:#fff;border-radius:16px;color:#282132;box-shadow:0 24px 72px #1e122c33;text-align:left}
.checkout-header{position:relative;flex-shrink:0;display:grid;grid-template-columns:36px 1fr;align-items:center;gap:12px;padding:24px 72px 24px 28px;background:#572b91;color:#fff}
.checkout-heading-icon{width:36px;height:36px;display:grid;place-items:center;color:#fff;background:#7046a3;border-radius:10px}
.checkout-close{position:absolute;top:20px;right:18px;display:grid;place-items:center;width:44px;height:44px;padding:0;background:transparent;border:0;border-radius:10px;color:#fff;cursor:pointer}
.checkout-close:hover{background:#7046a3}.checkout-close:focus-visible{outline:2px solid #fff;outline-offset:2px}
.checkout-header h2{font-size:24px;line-height:1.25;letter-spacing:-.025em;font-weight:750;margin:0;color:#fff}
.subscription-checkout #checkout-heading{color:#fff}
.subscription-checkout .checkout-header p{grid-column:1/-1;font-size:14px;line-height:1.6;color:#eee5fa;margin:0}
.checkout-body{min-height:0;overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;scrollbar-color:#9b85b8 #f6f2fa;padding:24px 28px 28px;background:#fff}
.checkout-summary{margin:0;padding:18px 20px;background:#f3edf9;border-radius:12px}
.checkout-summary>div{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}
.checkout-summary dt{font-size:14px;color:#655474;line-height:1.6}
.checkout-summary dd{margin:0;text-align:right;font-size:16px;font-weight:650;color:#38234f}
.checkout-plan dd span{display:block;font-size:13px;font-weight:400;line-height:1.6;color:#655474;margin-top:2px}
.checkout-summary .checkout-total{align-items:center;border-top:1px solid #dcd0e9;margin-top:16px;padding-top:16px}
.checkout-total dt{font-size:14px;font-weight:600;color:#452074}.checkout-total dd{font-size:28px;letter-spacing:-.03em;line-height:1.3;font-weight:750;font-variant-numeric:tabular-nums;color:#452074}
.subscription-checkout .checkout-renewal{display:flex;align-items:center;gap:7px;margin:12px 0 22px;font-size:12px;color:#655474;line-height:1.5}.checkout-renewal svg{color:#572b91;flex-shrink:0}
.checkout-form-open .checkout-header>p,.checkout-form-open .checkout-plan{display:none}
.checkout-form-open .checkout-summary .checkout-total{margin-top:0;padding-top:0;border-top:0}
.checkout-footer{flex-shrink:0;display:flex;align-items:flex-start;gap:10px;border-top:1px solid #e7ddef;padding:16px 28px;background:#faf7fd}.checkout-footer>svg{color:#572b91;flex-shrink:0;margin-top:2px}.subscription-checkout .checkout-footer p{font-size:12px;color:#51435f;line-height:1.6;margin:0}.checkout-footer p span{color:#6b5f75}
.subscription-checkout ::selection{background:#e5d8f5;color:#38234f}
@media(max-width:540px){.subscription-checkout{padding:12px}.subscription-checkout>section{max-height:calc(100dvh - 24px)}.checkout-header{padding:20px 58px 20px 18px;grid-template-columns:28px 1fr;gap:10px}.checkout-heading-icon{width:28px;height:32px;background:transparent}.checkout-header h2{font-size:21px}.checkout-close{top:14px;right:8px}.checkout-body{padding:18px 16px 22px}.checkout-summary{padding:14px 16px}.checkout-total dd{font-size:26px}.checkout-footer{padding:14px 18px}.checkout-footer p span{font-size:11px}}
</style>

<style scoped>
.billing-page{--billing-muted:#6b6277;--billing-line:#e5dfed;--billing-purple:#572b91;font-variant-numeric:tabular-nums}
.billing-page ::selection{background:#e7d9f7;color:#39205d}
.billing-success{display:flex;align-items:center;justify-content:space-between;gap:28px;padding:28px;margin:0 0 28px;border:1px solid #cce3d6;border-radius:16px;background:#f1f8f4}
.billing-success-copy{display:flex;align-items:center;gap:16px;min-width:0}
.billing-success-icon{display:grid;place-items:center;flex-shrink:0;width:52px;height:52px;border-radius:50%;background:#dcefe3;color:#216b49}
.billing-page .billing-success h2{margin:0 0 6px;font-size:23px;font-weight:750;line-height:1.3;letter-spacing:-.025em;color:#214b36}
.billing-page .billing-success p{margin:0;font-size:14px;line-height:1.6;color:#416551}
.billing-dashboard-button{display:inline-flex;align-items:center;justify-content:center;gap:20px;flex-shrink:0;min-height:58px;padding:16px 24px;border:0;border-radius:12px;background:var(--billing-purple);color:#fff;font:inherit;font-size:15px;font-weight:750;line-height:1.5;cursor:pointer;box-shadow:0 5px 14px #572b911a;transition:background .15s,box-shadow .15s}
.billing-dashboard-button{text-decoration:none;box-sizing:border-box}.billing-dashboard-button:hover{background:#452176;color:#fff;text-decoration:none;box-shadow:0 7px 18px #572b9126}.billing-dashboard-button:active{background:#381b62}.billing-page .billing-dashboard-button:focus-visible{outline:3px solid #572b91;outline-offset:4px}.billing-dashboard-button svg{flex-shrink:0}
@media(max-width:800px){.billing-success{align-items:stretch;flex-direction:column;gap:22px;padding:24px}.billing-dashboard-button{width:100%;justify-content:space-between}}
@media(max-width:480px){.billing-success{padding:20px;margin-bottom:20px}.billing-success-copy{align-items:flex-start;gap:12px}.billing-success-icon{width:42px;height:42px}.billing-page .billing-success h2{font-size:21px}.billing-dashboard-button{gap:12px;padding:16px 18px}}
@media(prefers-reduced-motion:reduce){.billing-dashboard-button{transition:none}}
.billing-heading{display:flex;align-items:center;justify-content:space-between;gap:24px;margin:8px 0 30px}
.billing-heading h1{font-size:34px;letter-spacing:-.035em;margin-bottom:8px}
.billing-button{display:inline-flex;align-items:center;justify-content:center;gap:9px;min-height:42px;font-size:13px;border-radius:9px;background:#fff;color:var(--billing-purple)}
.billing-refresh{flex-shrink:0}.billing-link{color:var(--billing-purple);min-height:36px;font-size:13px;text-underline-offset:4px}
.billing-summary-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);gap:22px;margin:0 0 30px;align-items:start}
.billing-summary-grid>.billing-section{margin:0;padding:26px;border:1px solid var(--billing-line);border-radius:16px;min-width:0;background:#fff}
.billing-summary-grid>.billing-plan-panel{background:#f8f5fc}
.billing-section-heading{margin-bottom:22px}.billing-section h2{font-size:18px;letter-spacing:-.02em}
.billing-status{display:inline-flex;align-items:center;gap:5px;padding:6px 9px;border-radius:6px;font-size:12px;line-height:1.2;font-weight:650;color:#67502d;background:#fff2d9}
.billing-status.is-paid{color:#1e6847;background:#e5f3eb}.billing-status.is-trial{color:#572b91;background:#ebe1f6}.billing-status.is-failed{color:#a12838;background:#fcebef}
.billing-current-plan{border:0;padding:0;background:transparent;gap:18px;border-radius:0;flex-wrap:wrap;align-items:center}
.billing-plan-identity{display:flex;align-items:center;gap:14px}.billing-plan-icon,.billing-payment-icon{display:grid;place-items:center;flex-shrink:0;width:48px;height:48px;border-radius:12px;background:#eae0f5;color:#572b91}
.billing-current-plan h3{font-size:22px;letter-spacing:-.025em;margin:0}.billing-current-plan p{font-size:13px;margin-top:3px}
.billing-plan-price{display:flex;flex-direction:column;gap:3px}.billing-plan-price strong{font-size:26px;line-height:1.2;letter-spacing:-.03em;color:#352344}.billing-plan-price span{font-size:12px;color:var(--billing-muted)}
.billing-renewal-row{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:24px;padding-top:22px;border-top:1px solid #e2d7ee}
.billing-renewal-date{display:flex;align-items:center;gap:10px;color:#75598d}.billing-renewal-date>div{display:grid;gap:4px}.billing-renewal-date span{font-size:12px;color:var(--billing-muted)}.billing-renewal-date strong{font-size:14px;font-weight:650;color:#352344}
.billing-primary-button{background:#572b91;border-color:#572b91;color:white}.billing-primary-button:hover{background:#452176}
.billing-scheduled{display:flex;align-items:flex-start;gap:10px;margin-top:23px;padding-top:20px;border-top:1px solid #e2d7ee;color:#64428a}.billing-scheduled>svg{flex-shrink:0;margin-top:2px}.billing-scheduled strong{font-size:13px;font-weight:650}.billing-scheduled p{font-size:12px;margin-bottom:0;color:#6e5c7d}
.billing-plan-panel.plans-expanded{grid-column:1/-1}.billing-plan-panel.plans-expanded+.billing-payment-panel{grid-column:1/-1}
.billing-payment-panel .billing-section-heading{margin-bottom:18px}.billing-payment-row{border:0;padding:0;justify-content:flex-start;gap:12px}.billing-payment-icon{background:#f3eef8}.billing-payment-row .billing-primary{font-size:16px;margin:0}.billing-payment-row .billing-caption{margin:2px 0 0;font-size:12px}
.billing-email{margin-top:22px}.billing-email>span{font-size:12px;color:var(--billing-muted)}.billing-email p{color:#352344;font-size:14px;overflow-wrap:anywhere}
.billing-payment-note{display:flex;gap:8px;align-items:flex-start;border-top:1px solid var(--billing-line);padding-top:18px;margin-top:18px!important;font-size:12px!important}.billing-payment-note>svg{flex-shrink:0;margin-top:2px;color:#75598d}.billing-manage{border-top:1px solid var(--billing-line);margin-top:20px;padding-bottom:0}.billing-manage input,.billing-manage select{caret-color:#572b91}.billing-manage input:focus-visible,.billing-manage select:focus-visible{outline:2px solid #815ab1;outline-offset:2px}
.billing-history{border:1px solid var(--billing-line);border-radius:16px;padding:26px;background:white}.billing-history .billing-section-heading{margin-bottom:18px}.billing-history .billing-section-heading p{font-size:13px;margin:6px 0 0}
.billing-table{scrollbar-color:#b49dcb #f6f2fa;scrollbar-width:thin}.billing-table th{font-size:12px;font-weight:600;color:#6b6277;background:#f8f6fa}.billing-table td,.billing-table th{padding:17px 14px}.billing-table td:first-child,.billing-table th:first-child{padding-left:14px}.billing-table td{font-size:13px}.billing-invoice-number,.billing-invoice-amount{font-weight:650;color:#352344}.billing-download{background:#f7f3fc;border-color:#e6dcf1;font-size:12px;min-height:38px}.billing-download:hover{background:#ede3f7}.billing-table .billing-caption{font-size:12px;line-height:1.65;margin:16px 0 0}.billing-footer{font-size:12px;border:0;padding:0 0 16px}.billing-footer>span:last-child{display:flex;align-items:center;gap:6px}.billing-message{background:#f4effa;color:#614379!important}.billing-message.error{background:#fff0f2;border-color:#f0c4cb;color:#9b2435!important}
@media(max-width:1100px){.billing-summary-grid{grid-template-columns:1fr}.billing-plan-price{margin-left:auto}.billing-payment-panel .billing-payment-row{flex-wrap:nowrap}}
@media(max-width:600px){.billing-heading{align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:24px}.billing-heading h1{font-size:29px}.billing-heading p{font-size:13px}.billing-summary-grid{gap:16px;margin-bottom:20px}.billing-summary-grid>.billing-section,.billing-history{padding:20px}.billing-current-plan h3{font-size:20px}.billing-plan-identity{gap:10px}.billing-plan-price strong{font-size:23px}.billing-plan-price{margin-left:0}.billing-renewal-row{align-items:flex-start;flex-wrap:wrap}.billing-table table,.billing-table tbody{display:block;width:100%}.billing-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.billing-table tr{display:grid;grid-template-columns:1fr;gap:13px;padding:20px 0;border-top:1px solid var(--billing-line)}.billing-table td,.billing-table td:first-child{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0;border:0;white-space:normal;text-align:right;overflow-wrap:anywhere}.billing-table td[data-label]:before{content:attr(data-label);font-size:12px;font-weight:400;color:var(--billing-muted);text-align:left}.billing-table .billing-download-cell{padding-top:3px}.billing-download-cell .billing-button{width:100%;min-height:44px}.billing-table .billing-caption{border-top:1px solid var(--billing-line);padding-top:16px;margin-top:0}.billing-footer{flex-wrap:wrap;gap:10px}.billing-plan-price span{font-size:12px}}
</style>

<style scoped>
.billing-onboarding{max-width:none;min-height:0;padding:0;--billing-muted:#685b77;--billing-line:#e6ddec;--student-ink:#2c2038;--student-muted:#685b77}.billing-onboarding .billing-heading{margin:0 0 24px}.billing-onboarding .billing-heading h2{font-size:20px;letter-spacing:-.02em;margin:0 0 6px}.billing-onboarding .billing-summary-grid{grid-template-columns:minmax(0,1.35fr) minmax(290px,1fr);align-items:start}.billing-onboarding .billing-section{min-width:0}.billing-onboarding .billing-summary-grid>.billing-section{padding:26px;background:#fff}.billing-onboarding .billing-plan-panel{border-top:3px solid #572b91}.billing-onboarding .billing-plan-price strong{font-size:28px}.billing-onboarding .billing-renewal-date strong{line-height:1.5;max-width:24ch}.billing-onboarding .billing-email p{overflow-wrap:anywhere}.billing-onboarding .billing-email{font-size:14px}.billing-onboarding .billing-button{min-height:44px;white-space:normal}.billing-onboarding .billing-link{min-height:44px}.billing-onboarding .billing-history{padding:24px}.billing-onboarding .billing-plan-row:not(.billing-current-plan){background:white}.billing-onboarding .billing-entry{display:none}
@media(max-width:850px){.billing-onboarding .billing-summary-grid{grid-template-columns:1fr}.billing-onboarding .billing-summary-grid>.billing-section{padding:22px}}
@media(max-width:600px){.billing-onboarding .billing-plan-price{margin-left:0}.billing-onboarding .billing-current-plan{gap:20px}.billing-onboarding .billing-plan-price strong{font-size:26px}.billing-onboarding .billing-history{padding:20px}.billing-onboarding .billing-manage :is(input,select){font-size:16px}}
</style>

<style scoped>
.billing-page.billing-comparing{max-width:1440px}
.billing-plan-selection{margin-top:26px;padding:30px 20px 22px;background:#0a0a0a;border-radius:16px;color:#fff;container-type:inline-size}
.billing-plan-selection .plan-selection-heading{text-align:center;margin:4px 0 30px}
.billing-plan-selection .plan-selection-heading h2{font-size:clamp(26px,3vw,40px);font-weight:500;letter-spacing:-.035em;color:#fff!important}
.billing-plan-selection .plan-selection-heading p{color:#ccc;font-size:14px;margin-top:10px}
.billing-plan-selection .billing-plans{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;align-items:stretch;margin:0}
.billing-plan-selection .billing-plans>.billing-caption{color:#ccc;text-align:center;margin-top:10px}
@container(max-width:1000px){.billing-plan-selection .billing-plans{grid-template-columns:repeat(2,minmax(0,1fr))}}
@container(max-width:440px){.billing-plan-selection .billing-plans{grid-template-columns:1fr}}
@media(max-width:600px){.billing-plan-selection{padding:24px 12px 18px;margin-inline:-10px}}
</style>
