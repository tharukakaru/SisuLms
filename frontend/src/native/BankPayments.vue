<script setup>
import {ref,onMounted,computed,watch,nextTick} from 'vue'
import {RefreshCw,Upload,FileText,CheckCircle2,Copy,ArrowRight,Landmark,X,Clock3} from 'lucide-vue-next'
import {request as directRequest,upload as directUpload} from './client'
function request(module,method,args={},verb='POST'){return bridge.value?directRequest('public_student','action',{module,method,args}):directRequest(module,method,args,verb)}
function upload(module,method,body){if(bridge.value){body.append('invoice',form.value.invoice);return directUpload('public_student','upload_proof',body)}return directUpload(module,method,body)}
import WhatsAppComposer from './WhatsAppComposer.vue'
import {previewMode} from '../preview/mode'
const props=defineProps({general:Boolean,sharedCampus:Boolean,selectedClass:Object,member:Object,invoices:{type:Array,default:()=>[]},rooms:{type:Array,default:()=>[]}}),emit=defineEmits(['changed'])
const bridge=computed(()=>props.member.role==='Student'&&(props.general||props.sharedCampus))
const loadedInvoices=ref(null),invoices=computed(()=>loadedInvoices.value??props.invoices)
let paymentIntent='';try{paymentIntent=sessionStorage.getItem('sisu-payment-invoice')||''}catch{}
const reasons=['Slip is unclear or unreadable','Incorrect payment amount','Payment not received','Incorrect bank account','Duplicate or previously used slip','Wrong class or invoice','Other']
const copied=ref(false),success=ref(''),fileInput=ref(null),submitting=ref(false)
const today=()=>new Date().toLocaleDateString('en-CA')
const fileSize=size=>size<1024*1024?Math.max(1,Math.round(size/1024))+' KB':(size/(1024*1024)).toFixed(1)+' MB'
function clearFile(){file.value=null;if(fileInput.value)fileInput.value.value=''}
function selectFile(event){
 const selectedFile=event.target.files?.[0];error.value='';success.value=''
 if(!selectedFile){clearFile();return}
 if(selectedFile.size>5*1024*1024){clearFile();error.value='This file is too large. Choose a bank slip smaller than 5 MB.';return}
 if(!/\.(pdf|png|jpe?g|docx?|txt)$/i.test(selectedFile.name)){clearFile();error.value='Choose a PDF, JPG, PNG, Word document or text file.';return}
 file.value=selectedFile
}
const analysis=ref(null),bank=ref(null)
let bankSequence=0
async function loadBank(){const sequence=++bankSequence;bank.value=null;copied.value=false;const row=invoices.value.find(i=>i.name===form.value.invoice);if(row)try{const result=await request('class_keys','bank_details',{classroom:row.classroom},'GET');if(sequence===bankSequence)bank.value=result}catch(e){error.value=e.message}}
async function copyBank(){try{await navigator.clipboard.writeText(bank.value.instructions);copied.value=true}catch{error.value='Select and copy the bank details manually.'}}
const page=ref(0),reviewMode=ref('View'),whatsapp=ref(null)
const rows=ref([]),error=ref(''),busy=ref(false),selected=ref(null),file=ref(null),proofName=ref(''),tab=ref('Pending')
const reviewDialog=ref(null)
let reviewOpener=null
function closeReview(){if(!busy.value)selected.value=null}
function reviewKeys(event){
 if(event.key==='Escape'){event.preventDefault();event.stopPropagation();closeReview();return}
 if(event.key!=='Tab')return
 const controls=[...reviewDialog.value.querySelectorAll('button,a[href],input,select,textarea')].filter(el=>!el.disabled&&el.offsetParent!==null)
 const first=controls[0],last=controls.at(-1)
 if(!first){event.preventDefault();return}
 if(event.shiftKey&&(document.activeElement===first||document.activeElement===reviewDialog.value)){event.preventDefault();last.focus()}
 else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
}
watch(selected,async value=>{
 if(value){reviewOpener=document.activeElement;await nextTick();reviewDialog.value?.querySelector('button')?.focus()}
 else if(reviewOpener?.isConnected){reviewOpener.focus();reviewOpener=null}
})
const form=ref({invoice:'',reference:'',amount:'',transfer_date:new Date().toLocaleDateString('en-CA'),access_kind:'Month',starts_at:'',ends_at:'',note:'',rejection_reason:''})
const configuredDuration=computed(()=>{const r=props.rooms.find(r=>r.name===selected.value?.classroom);return r?.access_duration_days||!!r?.programme})
const student=computed(()=>props.member.role==='Student'),filtered=computed(()=>rows.value.filter(r=>tab.value==='All'||r.status===tab.value))
const roomName=id=>props.rooms.find(r=>r.name===id)?.title||id,money=n=>'LKR '+new Intl.NumberFormat('en-LK').format((n||0)/100)
async function run(fn){busy.value=true;error.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}
async function load(){
 if(student.value){
  if(bridge.value){const data=await directRequest('public_student','billing',{...(paymentIntent?{invoice:paymentIntent}:{}),...(props.selectedClass?.name?{classroom:props.selectedClass.name}:{})},'GET');loadedInvoices.value=data.invoices;rows.value=data.slips}
  else{const [bills,slips]=await Promise.all([directRequest('api','invoices',{...(paymentIntent?{preferred_invoice:paymentIntent}:{}),...(props.selectedClass?.name?{preferred_classroom:props.selectedClass.name}:{})}),request('commercial','slips',{page:page.value})]);loadedInvoices.value=bills;rows.value=slips}
  const due=invoices.value.filter(i=>i.status==='Unpaid')
  const room=props.selectedClass
  const match=due.find(i=>i.name===paymentIntent)||due.find(i=>room&&(i.classroom===room.name||room.programme&&i.programme===room.programme))||due.find(i=>i.name===form.value.invoice)||(due.length===1?due[0]:null)
  if(match){form.value.invoice=match.name;pickInvoice()}else if(!due.some(i=>i.name===form.value.invoice)){form.value.invoice='';form.value.amount='';bank.value=null}
 }else rows.value=await request('commercial','slips',{page:page.value})
}
function startReview(row,mode='View'){analysis.value=null;proofName.value='';reviewMode.value=mode;form.value.rejection_reason='';selected.value=row;const room=props.rooms.find(r=>r.name===row.classroom);form.value.note='';form.value.starts_at='';form.value.access_kind=room?.programme?'Course':room?.paid_access_kind||'Month';form.value.ends_at=room?.paid_access_end?.replace(' ','T')||''}
function pickInvoice(){form.value.amount=invoices.value.find(i=>i.name===form.value.invoice)?.amount||'';loadBank()}
async function submit(){submitting.value=true;try{await run(async()=>{if(!file.value)throw Error('Choose a slip');if(file.value.size>5*1024*1024)throw Error('Slip must be at most 5 MB');const body=new FormData();body.append('file',file.value);const f=previewMode?{name:file.value.name}:await upload('commercial','upload_proof',body);await request('commercial','submit_slip',{...form.value,proof:f.name});paymentIntent='';try{sessionStorage.removeItem('sisu-payment-invoice')}catch{};await load();clearFile();form.value.reference='';tab.value='Pending';success.value='Slip submitted. Your payment is pending review by your teacher or institute.';emit('changed')})}finally{submitting.value=false}}
async function review(decision){await run(async()=>{await request('commercial','review_slip',{...form.value,name:selected.value.name,decision});selected.value=null;await load();emit('changed')})}
const submitted=value=>value?new Date(value.includes('T')||value.endsWith('Z')?value:value.replace(' ','T')+'+05:30').toLocaleString('en-LK',{timeZone:'Asia/Colombo',dateStyle:'medium',timeStyle:'short'}):'Not recorded'
function showProof(row){if(previewMode){proofName.value='Preview proof: fictional transfer, not a bank confirmation.';return}window.open('/api/method/institute_lms.'+(bridge.value?'public_student':'commercial')+'.proof?'+new URLSearchParams({name:row.name}),'_blank','noopener')}
function chooseInvoice(row){form.value.invoice=row.name;pickInvoice();document.getElementById('bank-transfer')?.scrollIntoView({behavior:'smooth',block:'start'})}
defineExpose({chooseInvoice})
watch(()=>[props.selectedClass,invoices.value],()=>{
 const room=props.selectedClass;if(!room||paymentIntent)return
 const invoice=invoices.value.find(i=>i.status==='Unpaid'&&(i.classroom===room.name||(room.programme&&i.programme===room.programme)))
 if(invoice&&form.value.invoice!==invoice.name){form.value.invoice=invoice.name;pickInvoice()}
},{immediate:true})
onMounted(()=>run(load))
const paidInvoices=computed(()=>invoices.value.filter(i=>i.status==='Paid'))
</script>
<template>
<section id="bank-transfer" class="panel bank-payments">
  <header class="payment-heading">
    <div><h2>{{student?'Pay by bank transfer':'Bank payment reviews'}}</h2><p>{{student?'Submit your transfer details and bank slip for review.':'Check the money received in your bank account before approving a slip.'}}</p></div>
    <button class="button subtle refresh-button" :disabled="busy" @click="run(load)"><RefreshCw :size="16" aria-hidden="true"/> {{busy?'Refreshing…':'Refresh'}}</button>
  </header>
  <p v-if="error" class="error payment-feedback" role="alert">{{error}}</p>
  <p v-if="success" class="payment-feedback payment-success" role="status"><CheckCircle2 :size="20" aria-hidden="true"/>{{success}}</p>
  <p v-if="proofName" role="status">{{proofName}}</p>
  <p v-if="member.role==='Admin'" class="field-help">Manage receiving bank details in My profile → Bank details for student payments. They apply to every institute class and programme.</p>
  <p v-if="member.role==='Teacher'&&!member.institute_teacher" class="field-help">Manage your receiving bank details in My profile → Bank details for student payments. They apply to all your independent classes.</p>
  <div v-if="student&&!invoices.some(i=>i.status==='Unpaid')&&!busy" class="settled-message"><CheckCircle2 :size="22" aria-hidden="true"/><div><h3>You’re all caught up</h3><p>No outstanding fees. To join another class, choose Enroll now in My classrooms.</p><a href="#classrooms">Explore my classrooms <ArrowRight :size="16" aria-hidden="true"/></a></div></div>
  <section v-if="student&&paidInvoices.length" class="paid-invoice-summary"><h3>Confirmed payments</h3><p v-for="bill in paidInvoices" :key="bill.name">{{bill.programme_title||bill.classroom_title||roomName(bill.classroom)}} <strong>{{bill.currency||'LKR'}} {{Number(bill.amount).toLocaleString()}} · Paid</strong></p></section>
  <form v-if="student&&invoices.some(i=>i.status==='Unpaid')" class="transfer-layout" @submit.prevent="submit" :aria-busy="busy">
    <div class="transfer-fields">
      <h3>Transfer details</h3><p class="section-description">Match these details to your bank receipt.</p>
      <label class="payment-field">Class or programme<select v-model="form.invoice" @change="pickInvoice" required :disabled="busy"><option value="">Choose a class or programme</option><option v-for="i in invoices.filter(i=>i.status==='Unpaid')" :key="i.name" :value="i.name">{{i.programme_title||i.classroom_title||roomName(i.classroom)}} · LKR {{Number(i.amount).toLocaleString('en-LK')}}</option></select></label>
      <div class="transfer-row">
        <label class="payment-field">Reference (Student Name or NIC)<input v-model="form.reference" required maxlength="140" placeholder="Enter student name or NIC" :disabled="busy" aria-describedby="reference-help"><small id="reference-help">Use the student name or NIC entered as your payment reference.</small></label>
        <label class="payment-field">Transfer date<input v-model="form.transfer_date" type="date" :max="today()" required :disabled="busy"></label>
      </div>
      <div class="upload-section">
        <span class="upload-title" id="bank-slip-label">Bank slip</span>
        <label class="slip-upload" :class="{'has-file':file,'is-busy':busy}">
          <input ref="fileInput" type="file" accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.txt" required :disabled="busy" @change="selectFile" aria-labelledby="bank-slip-label" aria-describedby="bank-slip-help">
          <span class="upload-icon"><FileText v-if="file" :size="24" aria-hidden="true"/><Upload v-else :size="24" aria-hidden="true"/></span>
          <span class="upload-copy"><strong>{{file?file.name:'Choose your bank slip'}}</strong><span>{{file?fileSize(file.size)+' · Ready to upload':'Select a clear copy of your payment receipt'}}</span></span>
          <span class="upload-action">{{file?'Change file':'Browse files'}}</span>
        </label>
        <div class="upload-help"><small id="bank-slip-help">PDF, JPG, PNG, Word or text · Up to 5 MB</small><button v-if="file" type="button" class="remove-file" :disabled="busy" @click="clearFile"><X :size="14" aria-hidden="true"/>Remove file</button></div>
      </div>
      <div class="submit-area"><button class="button primary submit-slip" :disabled="busy||!form.invoice||!file"><span>{{busy?'Submitting…':'Submit slip for review'}}</span><ArrowRight :size="18" aria-hidden="true"/></button><p>Your class unlocks after approval and enrollment-key confirmation.</p></div>
    </div>
    <aside class="transfer-summary" aria-label="Bank transfer information">
      <div class="amount-summary"><span>Payment amount</span><strong>{{form.invoice?'LKR '+Number(form.amount).toLocaleString('en-LK',{minimumFractionDigits:2,maximumFractionDigits:2}):'Choose a class'}}</strong><small>The amount is set by your class invoice.</small></div>
      <div class="bank-information"><h3><Landmark :size="19" aria-hidden="true"/> Bank details</h3><template v-if="bank"><span class="recipient-label">Payment recipient</span><strong class="bank-recipient">{{bank.recipient}}</strong><p class="bank-instructions">{{bank.instructions||'Contact your provider for bank details before paying.'}}</p><button type="button" class="button subtle copy-bank" v-if="bank.instructions" @click="copyBank"><CheckCircle2 v-if="copied" :size="16" aria-hidden="true"/><Copy v-else :size="16" aria-hidden="true"/>{{copied?'Bank details copied':'Copy bank details'}}</button><span class="sr-only" role="status">{{copied?'Bank details copied to clipboard':''}}</span></template><p v-else>{{form.invoice?'Loading bank details…':'Choose a class to see its payment recipient and bank details.'}}</p></div>
      <div class="review-explanation"><Clock3 :size="18" aria-hidden="true"/><p>Your teacher or institute checks the transfer before approval. You’ll then receive a personal enrollment key.</p></div>
      <p class="bank-reminder">Transfer only to the bank account confirmed by your teacher or institute.</p>
    </aside>
  </form>
  <section class="submission-history" aria-label="Bank slip submissions">
    <div class="history-heading"><h3>{{student?'Your submissions':'Payment submissions'}}</h3><p>{{student?'Track your payment review status.':'Review submitted transfers and payment receipts.'}}</p></div>
    <div class="tabs payment-tabs" aria-label="Filter submissions"><button v-for="s in ['Pending','Approved','Rejected','All']" :key="s" :class="{selected:tab===s}" :aria-pressed="tab===s" @click="tab=s">{{s}}<span class="submission-count">{{s==='All'?rows.length:rows.filter(r=>r.status===s).length}}</span></button></div>
    <div v-if="filtered.length" class="table-wrap review-table" :class="{'student-history':student}"><table><thead><tr><th v-if="!student">Student</th><th>Class</th><th>Submitted</th><th>Transfer / amount</th><th>Status</th><th>Actions</th></tr></thead><tbody><tr v-for="r in filtered" :key="r.name"><td v-if="!student" data-label="Student"><strong>{{r.student_name||r.student}}</strong><small>LMS ID · {{r.student_lms_id||r.student}}</small><small>{{r.contact_number||'Contact number not added'}}</small></td><td data-label="Class">{{roomName(r.classroom)}}</td><td data-label="Submitted">{{submitted(r.submitted_at||r.creation)}}<small>Sri Lanka time</small></td><td data-label="Transfer"><strong>{{money(r.claimed_minor)}}</strong><small>{{r.reference}} · {{r.transfer_date}}</small></td><td data-label="Status"><span class="badge" :class="r.status==='Approved'?'green':r.status==='Rejected'?'peach':'violet'">{{r.status}}</span><small v-if="r.rejection_reason">{{r.rejection_reason}}</small></td><td data-label="Actions"><div class="review-actions"><button class="button subtle small" @click="startReview(r)">View details</button><template v-if="!student&&r.status==='Pending'"><button class="button primary small" @click="startReview(r,'Approve')">Approve</button><button class="button subtle small reject-action" @click="startReview(r,'Reject')">Reject</button></template></div></td></tr></tbody></table></div>
    <div v-else class="history-empty"><FileText :size="24" aria-hidden="true"/><h4>{{busy?'Loading submissions…':tab==='All'?'No submissions yet':'No '+tab.toLowerCase()+' submissions'}}</h4><p>{{busy?'Your payment history will appear here.':tab==='Pending'?'Slips awaiting review will appear here once submitted.':'Choose another filter to see your other submissions.'}}</p></div>
    <div class="inline"><button v-if="page>0" class="button subtle small" @click="page--;run(load)">Newer submissions</button><button v-if="rows.length===50" class="button subtle small" @click="page++;run(load)">Older submissions</button></div>
  </section>
<div v-if="selected" class="modal-backdrop payment-review-backdrop" @click.self="closeReview">
  <section ref="reviewDialog" class="modal bank-review" role="dialog" aria-modal="true" aria-labelledby="payment-review-title" tabindex="-1" @keydown="reviewKeys">
    <header class="review-header">
      <div><h2 id="payment-review-title">{{reviewMode==='View'?'Payment submission':reviewMode+' bank payment'}}</h2><span class="review-status" :class="'status-'+selected.status.toLowerCase()">{{selected.status==='Pending'?'Pending review':selected.status}}</span></div>
      <button class="review-close" aria-label="Close payment review" :disabled="busy" @click="closeReview"><X :size="21" aria-hidden="true"/></button>
    </header>
    <div class="review-body">
      <section class="review-student" aria-label="Student details"><h3>{{selected.student_name||selected.student}}</h3><dl class="review-facts student-facts"><div><dt>LMS ID</dt><dd>{{selected.student_lms_id||selected.student}}</dd></div><div><dt>Contact number</dt><dd>{{selected.contact_number||'Not added'}}</dd></div></dl></section>
      <section class="review-payment" aria-label="Transfer details">
        <div class="review-class"><span>Class or programme</span><h3>{{roomName(selected.classroom)}}</h3></div>
        <dl class="review-facts">
          <div><dt>Payment amount</dt><dd class="review-amount">{{money(selected.claimed_minor)}}</dd></div>
          <div><dt>Reference (Student Name or NIC)</dt><dd>{{selected.reference||'Not provided'}}</dd></div>
          <div><dt>Transfer date</dt><dd>{{selected.transfer_date||'Not recorded'}}</dd></div>
          <div><dt>Submitted</dt><dd>{{submitted(selected.submitted_at||selected.creation)}}<small>Sri Lanka time</small></dd></div>
        </dl>
      </section>
      <div class="receipt-actions"><button class="button primary" @click="showProof(selected)"><FileText :size="18" aria-hidden="true"/>View bank slip<ArrowRight :size="17" aria-hidden="true"/></button><button v-if="!student" class="button subtle" :disabled="busy" @click="run(async()=>{analysis=await request('workspace','analyse_slip',{name:selected.name})})">{{busy?'Analysing�':'Analyse slip'}}</button></div>
      <aside v-if="analysis" class="review-note"><h3>{{analysis.mode}}</h3><dl class="review-facts"><div v-for="(value,key) in analysis.checks" :key="key"><dt>{{key.replaceAll('_',' ')}}</dt><dd>{{value?'Found':'Not confirmed'}}</dd></div></dl><p>Repeated reference: {{analysis.duplicate_reference?'Check for duplicate payment':'None found'}}</p><p>{{analysis.notice}}</p></aside>
      <p v-if="proofName" role="status">{{proofName}}</p>
      <section v-if="selected.review_note" class="review-note"><h3>Review note</h3><p>{{selected.review_note}}</p></section>
      <p v-if="error" role="alert" class="error payment-feedback">{{error}}</p>
      <div class="review-decision">
<template v-if="!student&&selected.status==='Pending'"><div class="tabs"><button :class="{selected:reviewMode==='Approve'}" @click="reviewMode='Approve'">Approve</button><button :class="{selected:reviewMode==='Reject'}" @click="reviewMode='Reject'">Reject</button></div><template v-if="reviewMode==='Approve'"><p v-if="configuredDuration" class="field-help">Approved access uses the duration saved on this class or programme. Its end is calculated from the access start below.</p><label v-if="!configuredDuration">Access duration<select v-model="form.access_kind"><option v-for="k in ['Day','Week','Month','Year','Session','Course','Custom']">{{k}}</option></select></label><label>Access starts (Sri Lanka time; leave empty for now)<input type="datetime-local" v-model="form.starts_at"></label><label v-if="!configuredDuration&&['Session','Course','Custom'].includes(form.access_kind)">Access ends (Sri Lanka time)<input type="datetime-local" v-model="form.ends_at" required></label><label>How did you verify the bank payment?<textarea v-model="form.note" required maxlength="800" placeholder="Check the received amount in your bank account and record the confirmation."/></label><button class="button primary" :disabled="busy||!form.note.trim()" @click="review('Approved')">Confirm payment & approve access</button></template><template v-if="reviewMode==='Reject'"><label>Rejection reason<select v-model="form.rejection_reason" required><option value="">Choose a reason</option><option v-for="reason in reasons" :key="reason">{{reason}}</option></select></label><label>{{form.rejection_reason==='Other'?'Explain the reason':'Additional details for the student (optional)'}}<textarea v-model="form.note" maxlength="800" :required="form.rejection_reason==='Other'"/></label><button class="button primary" :disabled="busy||!form.rejection_reason||(form.rejection_reason==='Other'&&!form.note.trim())" @click="review('Rejected')">Reject & notify student</button></template></template></div>
    </div>
    <footer class="review-footer"><p>Institute class payments belong to the institute. Independent class payments belong to the teacher. Approval records the received payment; it does not transfer money.</p></footer>
  </section>
</div><WhatsAppComposer v-if="whatsapp" :rooms="rooms" :initial-class="whatsapp.classroom" :student="whatsapp.student" :slip="whatsapp.name" @close="whatsapp=null"/>
</section></template>
<style scoped>
.bank-payments{--payment-muted:#625c73;--payment-line:#e3dfed;--payment-soft:#f7f5fb;padding:32px;border-radius:16px;color:var(--ink,#29283c)}
.bank-payments h2,.bank-payments h3,.bank-payments h4,.bank-payments p{margin:0}
.payment-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:30px}
.bank-payments h2{font-size:26px;line-height:1.3;letter-spacing:-.025em}.payment-heading p{color:var(--payment-muted);font-size:15px;line-height:1.6;margin-top:8px;max-width:70ch}
.bank-payments .button{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;font-size:14px;border-radius:10px}.refresh-button{flex-shrink:0}.bank-payments button:disabled{cursor:not-allowed}
.bank-payments .payment-feedback{padding:16px;margin-bottom:20px;border-radius:10px;line-height:1.6}.payment-success{display:flex;align-items:center;gap:12px;background:var(--mint,#e9f4ee);color:#24543e}.payment-success svg{flex-shrink:0}
.bank-payments .transfer-layout{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(280px,1fr);gap:40px;max-width:none;align-items:start}
.transfer-fields{min-width:0}.bank-payments h3{font-size:18px;line-height:1.4;font-weight:700}.bank-payments .section-description{margin:6px 0 24px;color:var(--payment-muted);line-height:1.6}
.bank-payments .payment-field{display:flex;flex-direction:column;gap:9px;margin:0 0 24px;font-size:14px;font-weight:600;color:var(--ink,#29283c)}
.bank-payments input,.bank-payments select{min-height:48px;box-sizing:border-box;width:100%;min-width:0;padding:12px 14px;border:1px solid #cfc8de;border-radius:10px;background:var(--surface,#fff);color:var(--ink,#29283c);font-size:15px;line-height:1.5;caret-color:var(--brand)}
.bank-payments input::placeholder{color:var(--payment-muted)}.bank-payments input:focus-visible,.bank-payments select:focus-visible,.slip-upload:focus-within{outline:2px solid var(--brand);outline-offset:3px}
.transfer-row{display:grid;grid-template-columns:1fr 1fr;gap:20px}.payment-field small,.upload-help small{font-size:12px;font-weight:400;color:var(--payment-muted);line-height:1.5}
.upload-title{display:block;font-weight:600;margin-bottom:10px}.bank-payments .slip-upload{position:relative;display:flex;align-items:center;gap:14px;border:1px dashed #aba0c1;border-radius:12px;padding:22px 18px;margin:0;background:var(--payment-soft);cursor:pointer;min-width:0;transition:background .18s ease,border-color .18s ease}
.slip-upload:hover{border-color:var(--brand);background:var(--violet,#f0edfb)}.slip-upload.has-file{border-style:solid}.bank-payments .slip-upload input{position:absolute;inset:0;opacity:0;cursor:pointer;height:100%;padding:0}.slip-upload.is-busy,.slip-upload.is-busy input{cursor:wait}
.upload-icon{color:var(--brand);display:flex;flex-shrink:0}.upload-copy{display:flex;flex-direction:column;gap:5px;min-width:0}.upload-copy strong{font-size:14px;overflow-wrap:anywhere}.upload-copy>span{font-size:13px;color:var(--payment-muted);line-height:1.5}.upload-action{margin-left:auto;white-space:nowrap;color:var(--brand);font-weight:700;font-size:13px}.upload-help{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:10px}.remove-file{display:inline-flex;gap:4px;align-items:center;min-height:44px;font-size:12px;text-decoration:underline;text-underline-offset:3px;white-space:nowrap}
.submit-area{margin-top:26px;padding-top:24px;border-top:1px solid var(--payment-line)}.bank-payments .submit-slip{min-height:50px;padding:12px 22px;font-weight:700;gap:20px}.bank-payments .submit-area p{max-width:55ch;font-size:13px;color:var(--payment-muted);line-height:1.6;margin-top:12px}
.transfer-summary{background:var(--payment-soft);border-radius:12px;padding:26px;min-width:0}.amount-summary{display:grid;gap:8px;padding-bottom:24px;border-bottom:1px solid var(--payment-line)}.amount-summary>span{font-size:14px;color:var(--payment-muted)}.amount-summary strong{font-size:30px;line-height:1.2;font-variant-numeric:tabular-nums;letter-spacing:-.025em}.amount-summary small{font-size:12px;line-height:1.5;color:var(--payment-muted)}
.bank-information{padding:24px 0}.bank-information h3{display:flex;align-items:center;gap:10px;margin-bottom:20px}.recipient-label{display:block;font-size:12px;color:var(--payment-muted);margin-bottom:5px}.bank-recipient{font-size:16px;display:block;overflow-wrap:anywhere}.bank-payments .bank-instructions{font:inherit;font-size:14px;line-height:1.75;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--ink,#29283c);margin:12px 0 18px}.copy-bank{background:var(--surface,#fff);border:1px solid var(--payment-line)}
.review-explanation{display:flex;align-items:flex-start;gap:10px;padding-top:20px;border-top:1px solid var(--payment-line)}.review-explanation svg{flex-shrink:0;margin-top:2px;color:var(--brand)}.bank-payments .review-explanation p,.bank-payments .bank-reminder{font-size:13px;line-height:1.7;color:var(--payment-muted)}.bank-payments .bank-reminder{margin-top:14px}
.submission-history{border-top:1px solid var(--payment-line);margin-top:36px;padding-top:28px}.history-heading p{margin-top:5px;color:var(--payment-muted);font-size:14px;line-height:1.6}.payment-tabs{display:flex;flex-wrap:wrap;gap:6px;margin:20px 0}.bank-payments .payment-tabs button{display:flex;align-items:center;gap:8px;min-height:44px;padding:10px 14px;color:var(--payment-muted);font-size:14px;border-radius:8px}.bank-payments .payment-tabs button.selected{background:var(--violet,#f0edfb);color:var(--ink,#29283c);font-weight:700}.submission-count{font-size:12px;font-variant-numeric:tabular-nums;min-width:20px;text-align:center;background:var(--surface,#fff);border-radius:4px;padding:1px 4px}
.review-table{overflow:auto}.review-table th{font-size:12px;color:var(--payment-muted);text-align:start;padding:14px 16px;background:var(--payment-soft)}.review-table td{padding:18px 16px;font-size:14px;color:var(--ink,#29283c);vertical-align:top;overflow-wrap:anywhere;max-width:320px}.review-table small{white-space:normal;overflow:visible;max-width:none;overflow-wrap:anywhere;display:block;font-size:12px;margin-top:6px;line-height:1.5;color:var(--payment-muted)}.review-table .badge{font-size:12px;padding:5px 9px}.review-actions{display:flex;flex-wrap:wrap;gap:8px}.history-empty{text-align:center;padding:32px 16px;background:var(--payment-soft);border-radius:10px;color:var(--payment-muted)}.history-empty svg{margin-bottom:10px}.history-empty h4{font-size:15px;color:var(--ink,#29283c);margin-bottom:6px}.history-empty p{font-size:13px;line-height:1.6}
.settled-message{display:flex;gap:14px;padding:24px 0}.settled-message svg{color:#24543e;flex-shrink:0}.settled-message p{margin:6px 0 12px;line-height:1.6}.settled-message a{display:inline-flex;gap:8px;align-items:center;min-height:44px;font-weight:600;color:var(--brand)}.paid-invoice-summary{padding:20px 0}.paid-invoice-summary p{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-top:16px;line-height:1.6}.paid-invoice-summary strong{color:#24543e;white-space:nowrap}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(max-width:1100px){.bank-payments .transfer-layout{gap:24px;grid-template-columns:minmax(0,1.25fr) minmax(250px,1fr)}.slip-upload{flex-wrap:wrap}.upload-action{display:none}.transfer-summary{padding:22px}}
@media(max-width:850px){.bank-payments{padding:24px}.bank-payments .transfer-layout{grid-template-columns:1fr}.transfer-summary{grid-row:1}.amount-summary{padding-bottom:18px}.bank-information{padding:18px 0}.bank-information h3{margin-bottom:14px}.transfer-row{gap:16px}}
@media(max-width:600px){.bank-payments{padding:20px 16px}.payment-heading{gap:12px;margin-bottom:24px}.bank-payments h2{font-size:22px}.payment-heading p{font-size:14px}.bank-payments .refresh-button{padding:10px;min-width:44px;font-size:12px}.refresh-button svg{display:none}.transfer-row{grid-template-columns:1fr;gap:0}.bank-payments .submit-slip{width:100%;justify-content:space-between}.transfer-summary{padding:20px}.payment-tabs{gap:4px}.bank-payments .payment-tabs button{padding:9px 10px;font-size:13px}.paid-invoice-summary p{display:block}.paid-invoice-summary strong{display:block;margin-top:6px}}
@media(max-width:900px){.review-table table,.review-table tbody,.review-table tr,.review-table td{display:block;width:100%;max-width:none}.review-table thead{display:none}.review-table tr{border-bottom:1px solid var(--payment-line);padding:12px 0}.review-table td{display:grid;grid-template-columns:88px minmax(0,1fr);gap:6px 12px;padding:8px 0;border:0}.review-table td:before{content:attr(data-label);font-size:12px;color:var(--payment-muted);grid-column:1;grid-row:1 / span 4}.review-table td>*{grid-column:2}.review-table td small{margin:0}.review-table .badge{justify-self:start}}
@media(prefers-reduced-motion:reduce){.slip-upload{transition:none}}

/* Payment receipt dialog: readable groups and a contained scroll area. */
.payment-review-backdrop{padding:24px;z-index:600}
.bank-payments .bank-review{width:min(640px,100%);max-width:100%;max-height:calc(100dvh - 48px);padding:0;border:0;border-radius:16px;background:var(--surface,#fff);box-shadow:0 24px 80px rgb(31 20 50 / 22%);overflow-y:auto;overscroll-behavior:contain;color:var(--ink,#29283c);scrollbar-color:#c5bed5 transparent;scrollbar-width:thin}
.review-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:26px 28px 22px;border-bottom:1px solid var(--payment-line)}
.bank-payments .review-header h2{font-size:24px;line-height:1.3;letter-spacing:-.025em;margin:0 0 12px}
.review-status{display:inline-flex;align-items:center;font-size:12px;font-weight:600;line-height:1.5;padding:5px 10px;border-radius:6px;background:#f3eddf;color:#75521b}.review-status.status-approved{background:var(--mint,#e9f4ee);color:#24543e}.review-status.status-rejected{background:#fbeae9;color:#923a35}
.review-close{width:44px;height:44px;flex-shrink:0;display:flex;align-items:center;justify-content:center;border-radius:10px;background:var(--payment-soft);color:var(--payment-muted)}.review-close:hover{background:var(--violet,#f0edfb);color:var(--ink)}.review-close:focus-visible{outline:2px solid var(--brand);outline-offset:3px}
.review-body{padding:26px 28px;display:grid;gap:24px}.bank-payments .review-student h3{font-size:18px;margin:0 0 16px;overflow-wrap:anywhere}
.review-facts{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:22px 24px;margin:0}.review-facts>div{min-width:0}.review-facts dt,.review-class>span{font-size:12px;line-height:1.5;color:var(--payment-muted);margin-bottom:6px}.review-facts dd{font-size:15px;font-weight:500;line-height:1.5;margin:0;overflow-wrap:anywhere;color:var(--ink,#29283c);font-variant-numeric:tabular-nums}.review-facts dd small{display:block;font-size:12px;color:var(--payment-muted);font-weight:400;margin-top:4px}.review-payment{padding-top:24px;border-top:1px solid var(--payment-line)}.review-class{margin-bottom:24px}.review-class>span{display:block}.bank-payments .review-class h3{font-size:16px;font-weight:600;line-height:1.6;overflow-wrap:anywhere}.review-facts .review-amount{font-size:22px;font-weight:700;letter-spacing:-.02em;line-height:1.35}
.receipt-actions{display:flex;flex-wrap:wrap;gap:10px}.bank-payments .receipt-actions .button{min-height:48px;padding:12px 18px}.bank-payments .receipt-actions .primary{gap:10px}
.review-note{background:var(--payment-soft);padding:18px;border-radius:10px;display:grid;gap:10px}.bank-payments .review-note h3{font-size:14px}.bank-payments .review-note p{font-size:14px;line-height:1.7;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--payment-muted)}
.review-decision:empty{display:none}.review-decision{display:grid;gap:18px}.review-decision .tabs{margin:0}.review-decision label{display:grid;gap:8px;font-size:14px;line-height:1.5}.review-decision textarea{width:100%;min-height:104px;padding:12px 14px;border:1px solid #cfc8de;border-radius:10px;font:inherit;resize:vertical;background:var(--surface,#fff);color:var(--ink)}.review-decision .field-help{font-size:13px;line-height:1.6;color:var(--payment-muted)}
.review-footer{padding:20px 28px;border-top:1px solid var(--payment-line);background:var(--payment-soft)}.bank-payments .review-footer p{font-size:12px;line-height:1.8;color:var(--payment-muted)}
@media(max-width:600px){.payment-review-backdrop{padding:12px}.bank-payments .bank-review{max-height:calc(100dvh - 24px)}.review-header{padding:22px 20px 18px}.bank-payments .review-header h2{font-size:22px}.review-body{padding:22px 20px;gap:22px}.review-facts{gap:20px 16px}.review-footer{padding:18px 20px}.receipt-actions .button{width:100%}.review-close{margin-top:-4px;margin-right:-4px}.review-facts dd{font-size:14px}}
@media(max-width:380px){.review-facts{grid-template-columns:1fr}}
</style>
