<script setup>
import {ref,onMounted,onBeforeUnmount,nextTick,watch} from 'vue'
import {request as directRequest,upload} from './client'
function request(module,method,args={},verb='POST'){return props.general?directRequest('public_student','action',{module,method,args}):directRequest(module,method,args,verb)}
import DurationFields from '../pricing/DurationFields.vue'
const props=defineProps({member:{type:Object,default:()=>({role:'Student'})},rooms:{type:Array,default:()=>[]},general:Boolean,profile:{type:String,default:''}}),emit=defineEmits(['refresh','room','navigate'])
const programmes=ref([]),selected=ref(null),editing=ref(false),error=ref(''),note=ref(''),busy=ref(false),form=ref({title:'',description:'',fee:0,access_duration_days:180,duration_months:6,modules:[]})
const enrollmentKey=ref(''),keyNotice=ref('')
async function redeemProgramme(){busy.value=true;error.value='';try{await request('class_keys','redeem',{classroom:selected.value.modules[0].classroom,key:enrollmentKey.value});await openModules(selected.value);keyNotice.value='Enrollment confirmed.';emit('refresh')}catch(e){error.value=e.message}finally{busy.value=false}}
async function copyBank(){try{await navigator.clipboard.writeText(bank.value.instructions);keyNotice.value='Bank details copied.'}catch{keyNotice.value='Select the bank details and copy them manually.'}}
const eligible=ref([]),loading=ref(false),progress=ref(null),bank=ref(null)
const draftKey='sisu-programme-draft:'+props.member.user+':'+props.member.institute
try{const saved=JSON.parse(localStorage.getItem(draftKey)||'null');if(saved){form.value=saved;note.value='Continue creating your programme — your draft is saved on this device.'}}catch{}
watch(form,value=>{try{localStorage.setItem(draftKey,JSON.stringify(value))}catch{}},{deep:true})
async function addModule(){busy.value=true;try{const code=await request('programme_courses','module_code');form.value.modules.push({module_code:code,title:'',teacher:'',duration_weeks:2,assessment_weight:90})}catch(e){error.value=e.message}finally{busy.value=false}}
function inviteTeacher(){emit('navigate','team')}
async function uploadAsset(event,kind){const file=event.target.files?.[0];if(!file)return;busy.value=true;try{const body=new FormData();body.append('file',file);body.append('kind',kind);const saved=await upload('programme_certificates','upload',body);form.value[kind]=saved.url||saved.file_id;note.value='File uploaded and saved in your programme draft.'}catch(e){error.value=e.message}finally{busy.value=false}}
function certificate(p){return '/api/method/institute_lms.'+(props.general?'public_student.programme_certificate':'programme_certificates.download')+'?'+new URLSearchParams({programme:p.name})}
function uploadSlip(){sessionStorage.setItem('sisu-payment-invoice',bank.value.invoice);closeModules();emit('navigate','payments')}
function moduleState(m){return progress.value?.modules?.find(row=>row.classroom===m.classroom)}
async function finish(m){busy.value=true;try{progress.value=await request('programme_learning','complete',{classroom:m.classroom})}catch(e){error.value=e.message}finally{busy.value=false}}

async function load(){loading.value=true;try{programmes.value=props.general?await directRequest('profiles','programmes',{profile:props.profile},'GET'):await request('teaching','programmes');if(props.member.role==='Admin'&&!props.general)eligible.value=await request('programme_courses','teachers');const resume=sessionStorage.getItem('sisu-open-programme');const target=programmes.value.find(p=>p.name===resume);if(target){sessionStorage.removeItem('sisu-open-programme');await openModules(target)}}catch(e){error.value=e.message}finally{loading.value=false}}
async function save(){busy.value=true;error.value='';try{await request('programme_courses','create',{data:form.value});editing.value=false;localStorage.removeItem(draftKey);form.value={title:'',description:'',fee:0,access_duration_days:180,duration_months:6,modules:[]};await load();emit('refresh')}catch(e){error.value=e.message}finally{busy.value=false}}
async function join(p){busy.value=true;error.value='';try{await request('teaching','enroll_programme',{programme:p.name});bank.value=await request('programme_courses','payment_details',{programme:p.name});note.value='One bank-transfer payment covers the whole programme. Upload the slip in Class fees for institute approval.';await openModules(p);emit('refresh')}catch(e){error.value=e.message}finally{busy.value=false}}
const moduleDialog=ref(null),closeButton=ref(null)
let returnFocus=null,scrollStyles=null,dialogRequest=0
function focusable(){return [...(moduleDialog.value?.querySelectorAll('button,a[href],input,select,textarea,[tabindex]')||[])].filter(el=>!el.disabled&&el.tabIndex>=0&&el.getClientRects().length)}
function keepFocus(event){if(selected.value&&moduleDialog.value&&!moduleDialog.value.contains(event.target))closeButton.value?.focus()}
function dialogKeys(event){
  if(!selected.value)return
  if(event.key==='Escape'){event.preventDefault();event.stopPropagation();closeModules();return}
  if(event.key!=='Tab')return
  const items=focusable(),first=items[0],last=items.at(-1)
  if(!first){event.preventDefault();moduleDialog.value?.focus();return}
  if(!moduleDialog.value?.contains(document.activeElement)){event.preventDefault();first.focus()}
  else if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
}
async function openModules(programme,event){
  if(!selected.value){
    returnFocus=event?.currentTarget||document.activeElement
    scrollStyles=[document.body.style.overflow,document.documentElement.style.overflow]
    document.body.style.overflow='hidden';document.documentElement.style.overflow='hidden'
    document.addEventListener('keydown',dialogKeys,true)
    document.addEventListener('focusin',keepFocus,true)
  }
  const requestId=++dialogRequest
  selected.value=programme
  progress.value=null
  if(bank.value?.programme!==programme.name)bank.value=null
  try{if(!programme.requires_registration){const result=await request('programme_learning','status',{programme:programme.name});if(requestId===dialogRequest)progress.value=result}}catch(e){if(requestId===dialogRequest)error.value=e.message}
  await nextTick()
  if(selected.value===programme)closeButton.value?.focus()
}
function closeModules(){
  dialogRequest++
  selected.value=null
  document.removeEventListener('keydown',dialogKeys,true)
  document.removeEventListener('focusin',keepFocus,true)
  if(scrollStyles){[document.body.style.overflow,document.documentElement.style.overflow]=scrollStyles;scrollStyles=null}
  if(returnFocus?.isConnected)returnFocus.focus()
  returnFocus=null
}
function openModule(module){
  const room=props.rooms.find(r=>r.name===module.classroom)||{name:module.classroom,title:module.title,institute:selected.value.institute}
  if(!room||props.member.role==='Student'&&!moduleState(module)?.allowed)return
  closeModules()
  emit('room',room)
}
onBeforeUnmount(closeModules)
watch(()=>props.profile,load);onMounted(load)
</script>
<template><section>
<header class="section-heading"><div><span class="eyebrow">ONE JOURNEY. EVERY MODULE INCLUDED.</span><h2>Programmes · complete courses</h2><p>Learn step by step with your institute's teaching team.</p></div><button v-if="member.role==='Admin'&&!general" class="button primary" @click="editing=!editing">{{form.title?'Continue creating your programme':'Create programme'}}</button></header>
<p v-if="error" class="error" role="alert">{{error}}</p><p v-if="note" role="status">{{note}}</p>
<form v-if="editing&&member.role==='Admin'" class="panel programme-form" @submit.prevent="save">
<h2>Create your programme</h2><p>Each module gets its own classroom and assigned institute teacher. Your draft stays here while you invite a teacher.</p>
<label>Programme name<input v-model="form.title" required maxlength="120"></label><label>Description<textarea v-model="form.description" maxlength="1500"/></label>
<label>One-time tuition · LKR<input v-model.number="form.fee" type="number" min="0" step="0.01" required></label>
<DurationFields v-model="form.access_duration_days"/>
<label>Programme cover photo<input type="file" accept="image/png,image/jpeg" :disabled="busy" @change="uploadAsset($event,'cover_image')"></label><img v-if="form.cover_image" :src="form.cover_image" alt="Programme cover preview" style="max-width:240px">
<label>Programme profile photo<input type="file" accept="image/png,image/jpeg" :disabled="busy" @change="uploadAsset($event,'profile_image')"></label><img v-if="form.profile_image" :src="form.profile_image" alt="Programme profile preview" style="max-width:100px">
<label>Certificate template<input type="file" accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.ppt,.pptx,.txt" :disabled="busy" @change="uploadAsset($event,'certificate_template')"></label>
<p v-if="form.certificate_template">Certificate uploaded. For Office or text templates, also upload a matching PDF to preserve your layout. Leave a blank space for the student's name.</p>
<label v-if="form.certificate_template">Matching PDF (for Office/text templates)<input type="file" accept="application/pdf" :disabled="busy" @change="uploadAsset($event,'certificate_preview')"></label>
<div v-if="form.certificate_template"><label>Name position from left (%)<input v-model.number="form.certificate_name_x" placeholder="50" type="number" min="0" max="100"></label><label>Name position from top (%)<input v-model.number="form.certificate_name_y" placeholder="50" type="number" min="0" max="100"></label></div>
<div v-for="(m,i) in form.modules" :key="m.module_code" class="module-edit">
<h3>Module {{i+1}}</h3><label>Module code<input :value="m.module_code" readonly></label><label>Module name<input v-model="m.title" required maxlength="120"></label>
<label>Teacher<select v-model="m.teacher" required><option value="">Choose an institute teacher</option><option v-for="t in eligible" :key="t.name" :value="t.name">{{t.full_name}}</option></select></label><button type="button" class="text-button" @click="inviteTeacher">Invite a teacher</button>
<label>Weeks<input v-model.number="m.duration_weeks" type="number" min="1" max="52" required></label>
<label>Assessment weight (%)<input v-model.number="m.assessment_weight" type="number" min="0" max="100" required></label><p>Attendance: {{100-Number(m.assessment_weight)}}%. Attendance and passing marks do not block progression.</p>
<button type="button" class="text-button" @click="form.modules.splice(i,1)">Remove module</button></div>
<button type="button" class="button subtle" :disabled="busy" @click="addModule">Add module</button> <button class="button primary" :disabled="busy||!form.modules.length">Save programme</button></form>
<div class="programme-grid"><article v-for="p in programmes" :key="p.name" class="panel programme-card"><img v-if="p.cover_image" :src="p.cover_image" alt=""><div class="programme-copy"><img v-if="p.profile_image" :src="p.profile_image" alt="Programme profile" class="programme-avatar"><span class="badge violet">{{p.modules.reduce((sum,m)=>sum+Number(m.duration_weeks),0)}} weeks · {{p.modules.length}} modules</span><h2>{{p.title}}</h2><p>{{p.description}}</p><div class="programme-price"><strong>LKR {{Number(p.fee).toLocaleString()}}</strong><span>one programme tuition payment</span></div><p>Access for {{p.access_duration_days||p.duration_months*30}} days. All modules included.</p><button class="button subtle" @click="openModules(p,$event)" aria-haspopup="dialog">View programme</button></div></article></div>
<Teleport to="body"><div v-if="selected" class="modal-backdrop programme-module-backdrop" @click.self="closeModules"><section ref="moduleDialog" class="modal panel programme-syllabus programme-module-dialog" role="dialog" aria-modal="true" aria-labelledby="programme-module-title" tabindex="-1"><button ref="closeButton" type="button" class="icon-button programme-module-close" aria-label="Close programme" @click="closeModules">×</button><span class="eyebrow">YOUR LEARNING JOURNEY</span><img v-if="selected.profile_image" :src="selected.profile_image" alt="Programme profile" class="programme-avatar"><h2 id="programme-module-title">{{selected.title}}</h2><p>{{selected.description}}</p><p>LKR {{Number(selected.fee).toLocaleString()}} · one-time tuition · {{selected.modules.reduce((sum,m)=>sum+Number(m.duration_weeks),0)}} weeks</p><p v-if="error" class="error" role="alert">{{error}}</p>
<form v-if="member.role==='Student'&&!selected.requires_registration&&!progress?.modules?.some(m=>m.allowed)" @submit.prevent="redeemProgramme" class="programme-key"><label>Enrollment key<input v-model="enrollmentKey" required maxlength="64" placeholder="Enter your enrollment key"></label><button class="button primary" :disabled="busy||!enrollmentKey.trim()">Enroll</button></form><p v-if="keyNotice" role="status">{{keyNotice}}</p><button v-if="member.role==='Student'&&!selected.requires_registration&&!progress?.modules?.some(m=>m.allowed)" class="button primary" :disabled="busy" @click="join(selected)">Enrol now · Pay by bank transfer</button>
<p v-if="selected.requires_registration">Register with this institute before enrolling in the programme.</p><button v-if="selected.requires_registration" class="button primary" @click="closeModules();emit('navigate','connections')">Register with institute</button><div v-if="bank&&bank.programme===selected.name" class="panel"><h3>Bank transfer details</h3><p>{{bank.recipient}} · {{bank.currency}} {{Number(bank.fee).toLocaleString()}}</p><p style="white-space:pre-wrap">{{bank.instructions||'Bank details have not been provided. Contact the institute before making a transfer.'}}</p><button v-if="bank.instructions" class="button subtle" @click="copyBank">Copy bank details</button><p v-if="bank.invoice">Payment reference: {{bank.invoice}}</p><p v-if="bank.invoice_status==='Paid'">This invoice is already paid. Enter your enrollment key above, or contact your institute if the access period has ended.</p><button v-if="bank.invoice&&bank.invoice_status!=='Paid'" class="button primary" @click="uploadSlip">Upload bank slip in Class fees</button></div>
<article v-for="(m,i) in selected.modules" :key="m.classroom" :class="{'module-locked':member.role==='Student'&&!moduleState(m)?.allowed}"><span class="module-number" :class="{'module-complete':moduleState(m)?.completed}">{{moduleState(m)?.completed?'✓':String(i+1).padStart(2,'0')}}</span><div><h3>{{m.title}}</h3><p>{{m.teacher_name||m.teacher}} · {{m.duration_weeks}} weeks</p><p v-if="moduleState(m)?.grade">Grade: {{moduleState(m).grade.score??'Not graded'}} / 100 <span v-if="moduleState(m).grade.provisional">· Provisional — awaiting marking</span></p><p v-if="member.role==='Student'&&!moduleState(m)?.allowed">{{moduleState(m)?.reason||'Enrol to access this module'}}</p></div>
<button v-if="(rooms.some(r=>r.name===m.classroom)||moduleState(m)?.allowed)&&(member.role!=='Student'||moduleState(m)?.allowed)" class="text-button" @click="openModule(m)">Open module →</button>
<button v-if="member.role==='Student'&&moduleState(m)?.allowed&&moduleState(m)?.grade?.can_complete&&!moduleState(m)?.completed" class="button primary" :disabled="busy" @click="finish(m)">Complete module</button></article>
<div v-if="progress?.completed"><p role="status">You have successfully completed this course.</p><a v-if="selected.has_certificate" class="button primary" :href="certificate(selected)" target="_blank" rel="noopener">Earn your certificate · View and download</a><p v-else>Your institute has not added a certificate yet.</p></div>
</section></div></Teleport><p v-if="!programmes.length&&!editing" class="panel empty-mini">Programmes will appear here when your institute adds them.</p></section></template>
<style>.programme-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:25px}.programme-card{overflow:hidden}.programme-card>img{width:100%;aspect-ratio:3;object-fit:cover}.programme-copy{padding:30px}.programme-copy h2{font-size:27px;margin:18px 0}.programme-copy p{font-size:13px;line-height:1.9;margin:15px 0}.programme-price{display:flex;flex-direction:column;gap:8px;margin:26px 0}.programme-price strong{font-size:29px;color:var(--student-accent)}.programme-price span{font-size:11px}.programme-syllabus,.programme-form{padding:30px;margin:28px 0}.programme-syllabus h2{margin:18px 0}.programme-syllabus article{display:flex;align-items:center;gap:20px;padding:20px 0;border-bottom:1px solid var(--student-border)}.programme-syllabus article>div{flex:1}.programme-syllabus h3{font-size:15px}.programme-syllabus p{font-size:12px;margin-top:8px}.module-number{background:var(--student-soft);color:var(--student-accent);width:43px;height:43px;display:grid;place-items:center;border-radius:14px}.programme-form label{display:flex;flex-direction:column;gap:10px;margin:20px 0;font-size:12px}.programme-form :is(input,select,textarea){padding:13px;border:1px solid var(--student-border);border-radius:12px;background:var(--student-card);color:var(--student-ink)}.programme-form p{font-size:12px;line-height:1.8;margin:15px 0}.module-edit{display:grid;grid-template-columns:1fr 100px 70px;gap:15px;align-items:center}@media(max-width:850px){.programme-grid{grid-template-columns:1fr}.programme-syllabus article{flex-wrap:wrap}}</style>

<style>
.programme-module-dialog{position:relative;width:min(760px,100%);max-width:100%;max-height:calc(100dvh - 40px);overflow-y:auto;overscroll-behavior:contain;margin:0;padding:30px;overflow-wrap:anywhere}.programme-module-dialog h2{padding-right:36px}.programme-module-close{position:absolute;right:18px;top:18px}.programme-module-dialog .module-number{flex-shrink:0}.programme-module-dialog article>div{min-width:0}.programme-module-dialog :focus-visible{outline:2px solid var(--student-accent);outline-offset:3px}@media(max-width:600px){.programme-module-dialog{max-height:calc(100dvh - 20px);padding:24px 18px}.programme-module-dialog article{gap:12px;flex-wrap:wrap}}
</style>

<style>.module-locked{opacity:.6}.module-number.module-complete{background:#d9f5df;color:#166534}.module-edit{grid-template-columns:repeat(2,minmax(0,1fr));border-bottom:1px solid var(--student-border);padding:20px 0}.module-edit h3{grid-column:1/-1}@media(max-width:600px){.module-edit{grid-template-columns:1fr}}</style>

<style>.module-edit input,.module-edit select{min-width:0;width:100%;box-sizing:border-box}.programme-form>img{border-radius:12px}</style>

<style>.programme-avatar{width:72px;height:72px;object-fit:cover;border-radius:50%;display:block;margin:0 0 14px}</style>

<style scoped>.programme-key{display:grid;gap:12px;margin:20px 0}.programme-key label{display:grid;gap:8px}.programme-key input{padding:12px;border:1px solid #ddd3e9;border-radius:9px;font:inherit}</style>