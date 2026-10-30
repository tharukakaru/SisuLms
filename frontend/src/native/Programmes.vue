<script setup>
import {ref,onMounted,onBeforeUnmount,nextTick} from 'vue'
import {request} from './client'
import DurationFields from '../pricing/DurationFields.vue'
const props=defineProps({member:Object,rooms:Array}),emit=defineEmits(['refresh','room','navigate'])
const programmes=ref([]),selected=ref(null),editing=ref(false),error=ref(''),note=ref(''),busy=ref(false),form=ref({title:'',description:'',fee:0,access_duration_days:180,duration_months:6,modules:[]})
const eligible=ref([]),loading=ref(false)
async function load(){loading.value=true;try{programmes.value=await request('teaching','programmes');if(props.member.role==='Admin')eligible.value=await request('teaching','programme_classrooms')}catch(e){error.value=e.message}finally{loading.value=false}}
async function save(){busy.value=true;error.value='';try{await request('teaching','save_programme',{data:form.value});editing.value=false;form.value={title:'',description:'',fee:0,access_duration_days:180,duration_months:6,modules:[]};await load();emit('refresh')}catch(e){error.value=e.message}finally{busy.value=false}}
async function join(p){busy.value=true;error.value='';try{await request('teaching','enroll_programme',{programme:p.name});note.value='Programme enrollment created. One invoice covers every module. Review it in Class fees; no payment has been taken.';emit('refresh')}catch(e){error.value=e.message}finally{busy.value=false}}
const moduleDialog=ref(null),closeButton=ref(null)
let returnFocus=null,scrollStyles=null
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
  selected.value=programme
  await nextTick()
  if(selected.value===programme)closeButton.value?.focus()
}
function closeModules(){
  selected.value=null
  document.removeEventListener('keydown',dialogKeys,true)
  document.removeEventListener('focusin',keepFocus,true)
  if(scrollStyles){[document.body.style.overflow,document.documentElement.style.overflow]=scrollStyles;scrollStyles=null}
  if(returnFocus?.isConnected)returnFocus.focus()
  returnFocus=null
}
function openModule(module){
  const room=props.rooms.find(r=>r.name===module.classroom)
  if(!room)return
  closeModules()
  emit('room',room)
}
onBeforeUnmount(closeModules)
onMounted(load)
</script>
<template><section class="programme-page"><div class="page-heading"><div><span class="eyebrow">ONE JOURNEY. EVERY MODULE INCLUDED.</span><h2>Programmes · complete courses</h2><p>Complete programmes, guided by a team of teachers.</p></div><button v-if="member.role==='Admin'" class="button primary" @click="editing=!editing">Create programme</button></div><p v-if="error" class="error" role="alert">{{error}}</p><p v-if="note" class="form-note" role="status">{{note}} <button class="text-button" @click="emit('navigate','payments')">View class fees →</button></p>
<form v-if="editing" class="panel programme-form" @submit.prevent="save"><h2>Bring your modules together.</h2><p>Create institute classrooms first, then select a different classroom for each module. Existing enrollments cannot be moved into a bundle.</p><label>Programme name<input v-model="form.title" required maxlength="120"></label><label>Description<textarea v-model="form.description" maxlength="1500"></textarea></label><div class="form-row"><label>Total tuition · LKR<input v-model.number="form.fee" type="number" min="0" step="0.01" required></label></div><DurationFields v-model="form.access_duration_days"/><div v-for="(m,i) in form.modules" class="module-edit"><label>Module {{i+1}}<select v-model="m.classroom" required><option value="">Choose a classroom</option><option v-for="r in eligible" :value="r.name">{{r.title}} · {{r.teacher_name}}</option></select></label><label>Weeks<input v-model.number="m.duration_weeks" type="number" min="1" max="52"></label><button type="button" class="text-button" @click="form.modules.splice(i,1)">Remove</button></div><button type="button" class="button subtle" @click="form.modules.push({classroom:'',duration_weeks:2})">Add module</button> <button class="button primary" :disabled="busy||!form.modules.length">Save programme</button></form>
<div class="programme-grid"><article v-for="p in programmes" class="panel programme-card"><img v-if="p.cover_image" :src="p.cover_image" alt=""><div class="programme-copy"><span class="badge violet">{{p.access_duration_days||p.duration_months*30}} days · {{p.modules.length}} modules</span><h2>{{p.title}}</h2><p>{{p.description}}</p><div class="programme-price"><strong>LKR {{Number(p.fee).toLocaleString()}}</strong><span>one programme tuition payment</span></div><p class="field-help">Paid to the institute. All modules included; no separate teacher charges. Your SISU monthly subscription is separate.</p><button class="button subtle" @click="openModules(p,$event)" aria-haspopup="dialog">Explore the modules</button> <button v-if="member.role==='Student'" class="button primary" :disabled="busy" @click="join(p)">Enroll in programme</button></div></article></div>
<Teleport to="body"><div v-if="selected" class="modal-backdrop programme-module-backdrop" @click.self="closeModules"><section ref="moduleDialog" class="modal panel programme-syllabus programme-module-dialog" role="dialog" aria-modal="true" aria-labelledby="programme-module-title" tabindex="-1"><button ref="closeButton" type="button" class="icon-button programme-module-close" aria-label="Close module plan" @click="closeModules">?</button><span class="eyebrow">YOUR LEARNING JOURNEY</span><h2 id="programme-module-title">{{selected.title}} · module plan</h2><p v-if="error" class="error" role="alert">{{error}}</p><p v-if="loading" role="status">Loading?</p><p v-if="!selected.modules.length" class="empty-mini">No modules have been added to this programme yet.</p><article v-for="(m,i) in selected.modules"><span class="module-number">{{String(i+1).padStart(2,'0')}}</span><div><h3>{{m.title}}</h3><p>{{m.teacher_name||m.teacher}} · {{m.duration_weeks}} weeks</p></div><button v-if="rooms.some(r=>r.name===m.classroom)" class="text-button" @click="openModule(m)">Open classroom →</button></article></section></div></Teleport><p v-if="!programmes.length&&!editing" class="panel empty-mini">Programmes will appear here when your institute adds them.</p></section></template>
<style>.programme-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:25px}.programme-card{overflow:hidden}.programme-card>img{width:100%;aspect-ratio:3;object-fit:cover}.programme-copy{padding:30px}.programme-copy h2{font-size:27px;margin:18px 0}.programme-copy p{font-size:13px;line-height:1.9;margin:15px 0}.programme-price{display:flex;flex-direction:column;gap:8px;margin:26px 0}.programme-price strong{font-size:29px;color:var(--student-accent)}.programme-price span{font-size:11px}.programme-syllabus,.programme-form{padding:30px;margin:28px 0}.programme-syllabus h2{margin:18px 0}.programme-syllabus article{display:flex;align-items:center;gap:20px;padding:20px 0;border-bottom:1px solid var(--student-border)}.programme-syllabus article>div{flex:1}.programme-syllabus h3{font-size:15px}.programme-syllabus p{font-size:12px;margin-top:8px}.module-number{background:var(--student-soft);color:var(--student-accent);width:43px;height:43px;display:grid;place-items:center;border-radius:14px}.programme-form label{display:flex;flex-direction:column;gap:10px;margin:20px 0;font-size:12px}.programme-form :is(input,select,textarea){padding:13px;border:1px solid var(--student-border);border-radius:12px;background:var(--student-card);color:var(--student-ink)}.programme-form p{font-size:12px;line-height:1.8;margin:15px 0}.module-edit{display:grid;grid-template-columns:1fr 100px 70px;gap:15px;align-items:center}@media(max-width:850px){.programme-grid{grid-template-columns:1fr}.programme-syllabus article{flex-wrap:wrap}}</style>

<style>
.programme-module-dialog{position:relative;width:min(760px,100%);max-width:100%;max-height:calc(100dvh - 40px);overflow-y:auto;overscroll-behavior:contain;margin:0;padding:30px;overflow-wrap:anywhere}.programme-module-dialog h2{padding-right:36px}.programme-module-close{position:absolute;right:18px;top:18px}.programme-module-dialog .module-number{flex-shrink:0}.programme-module-dialog article>div{min-width:0}.programme-module-dialog :focus-visible{outline:2px solid var(--student-accent);outline-offset:3px}@media(max-width:600px){.programme-module-dialog{max-height:calc(100dvh - 20px);padding:24px 18px}.programme-module-dialog article{gap:12px;flex-wrap:wrap}}
</style>
