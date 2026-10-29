<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue'
import {request} from '../native/client'
import {daysUntil,localDate} from './dates'
import Icon from '../Icon.vue'
const data=ref({motto:'',event_title:'',event_date:'',hide_countdown:0}),form=ref({}),editing=ref(false),busy=ref(false),error=ref(''),ready=ref(false),today=ref(localDate())
const showCountdown=computed(()=>!Number(data.value.hide_countdown)&&!!data.value.event_date)
const days=computed(()=>daysUntil(data.value.event_date,today.value))
const digits=computed(()=>String(Math.abs(days.value??0)).padStart(2,'0').split(''))
const targetDate=computed(()=>data.value.event_date?new Date(data.value.event_date+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'')
const dayCaption=computed(()=>days.value===0?'TODAY IS YOUR DAY':days.value<0?'DAYS SINCE YOUR MILESTONE':'DAYS LEFT')
let timer
onMounted(async()=>{timer=setInterval(()=>today.value=localDate(),60000);try{data.value=await request('learning_preferences','get_preferences');ready.value=true}catch(e){error.value=e.message}})
onBeforeUnmount(()=>clearInterval(timer))
function edit(addCountdown=false){form.value={...data.value,hide_countdown:data.value.event_date?(Number(data.value.hide_countdown)||0):1};if(addCountdown)form.value.hide_countdown=0;editing.value=true}
async function removeCountdown(){busy.value=true;error.value='';try{data.value=await request('learning_preferences','save_preferences',{data:{...data.value,hide_countdown:1}});editing.value=false}catch(e){error.value=e.message}finally{busy.value=false}}
async function save(){busy.value=true;error.value='';try{data.value=await request('learning_preferences','save_preferences',{data:form.value});editing.value=false}catch(e){error.value=e.message}finally{busy.value=false}}
</script>
<template>
<section class="learning-goals" :class="{'without-countdown':!showCountdown}">
  <div v-if="showCountdown" class="goal-countdown">
    <div class="countdown-heading"><span class="goal-symbol"><Icon name="CalendarDays" :size="22"/></span><div><span class="eyebrow">EXAM COUNTDOWN</span><h2>{{data.event_title}}</h2></div><button class="remove-countdown" aria-label="Remove exam countdown" title="Remove countdown from my overview" :disabled="busy" @click="removeCountdown"><Icon name="X" :size="17"/></button></div>
    <div class="countdown-body"><div class="countdown-numbers" role="img" :aria-label="Math.abs(days)+' '+dayCaption.toLowerCase()"><span v-for="(digit,index) in digits" :key="index" aria-hidden="true">{{digit}}</span></div><div class="countdown-caption"><strong>{{dayCaption}}</strong><small>{{targetDate}}</small></div></div>
    <div class="countdown-bottom"><span>{{days===0?'Take a breath. You are ready.':days<0?'Look how far you have come.':'A little closer, every day.'}}</span><Icon name="Sparkles" :size="18" aria-hidden="true"/></div>
  </div>
  <div class="goal-motto"><span class="eyebrow">MY MOTTO</span><p>{{data.motto||'A little progress, every day.'}}</p><div class="goal-actions"><button class="text-button" :disabled="!ready||busy" @click="edit(false)"><Icon name="Settings2" :size="14"/>Personalise my overview</button><button v-if="!showCountdown" class="button subtle small" :disabled="!ready||busy" @click="edit(true)"><Icon name="Plus" :size="14"/>Add exam countdown</button></div></div>
  <p v-if="error" role="alert" class="error">{{error}}</p>
  <form v-if="editing" class="goal-editor" @submit.prevent="save"><div class="goal-editor-heading"><h3>Make this space yours</h3><button type="button" class="text-button" aria-label="Close personalization" @click="editing=false"><Icon name="X" :size="18"/></button></div><label class="countdown-switch"><input type="checkbox" v-model="form.hide_countdown" :true-value="0" :false-value="1"><span><strong>Show my exam countdown</strong><small>Add it to your overview. Turn it off whenever you like.</small></span></label><label>My motto in one sentence<input v-model="form.motto" maxlength="180" placeholder="Small steps today, bigger possibilities tomorrow."></label><div v-if="!form.hide_countdown" class="form-row"><label>Exam or special occasion<input v-model="form.event_title" maxlength="80" placeholder="GCE A/L" required></label><label>My target date<input type="date" v-model="form.event_date" required></label></div><small v-if="!form.hide_countdown">Use your confirmed exam date. SISU does not supply official exam dates.</small><div class="inline"><button class="button primary" :disabled="busy">{{busy?'Saving…':'Save my overview'}}</button><button type="button" class="button subtle" @click="editing=false">Cancel</button></div></form>
</section>
</template>
<style scoped>
.learning-goals{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);border:1px solid #e5ddef;border-radius:18px;margin:22px 0 24px;background:var(--student-card,#fff);overflow:hidden}.learning-goals.without-countdown{grid-template-columns:1fr}
.goal-countdown{position:relative;padding:24px 26px;background:radial-gradient(ellipse at 100% 0,#e8dcf7,transparent 70%),#faf7fd;color:#48216d}
.countdown-heading{display:flex;align-items:center;gap:12px}.goal-symbol{display:grid;place-items:center;width:44px;height:44px;flex-shrink:0;border-radius:14px;background:#eee5f8;color:#552783;border:1px solid #e3d5f1}.countdown-heading>div{flex:1;min-width:0}.countdown-heading .eyebrow{font-size:9px;color:#7d5d9c;letter-spacing:1.3px}.learning-goals .countdown-heading h2{font-size:17px;line-height:1.35;margin:6px 0 0;color:#392049;overflow-wrap:anywhere}.remove-countdown{align-self:flex-start;display:grid;place-items:center;flex-shrink:0;background:transparent;color:#897297;border:0;border-radius:7px;padding:5px;cursor:pointer}.remove-countdown:hover{background:#eaddf4;color:#48216d}.remove-countdown:focus-visible{outline:2px solid #744a9c;outline-offset:2px}
.countdown-body{display:flex;align-items:center;gap:18px;margin:24px 0 20px}.countdown-numbers{display:flex;gap:6px;min-width:0}.countdown-numbers>span{display:grid;place-items:center;width:49px;height:66px;border:1px solid #e1d2ee;border-radius:10px;background:linear-gradient(#fff 49%,#f1e9f8 50%,#fdfbff 51%);font-family:'Manrope Variable',sans-serif;font-size:38px;font-weight:750;line-height:1;color:#552783;box-shadow:0 3px 0 #e9dff3}.countdown-caption{display:grid;gap:8px;min-width:0}.countdown-caption strong{font-size:10px;letter-spacing:1.3px;line-height:1.6;color:#674985}.countdown-caption small{font-size:11px;color:#8b749c;white-space:nowrap}.countdown-bottom{display:flex;align-items:center;justify-content:space-between;gap:10px;border-top:1px solid #e9dff2;padding-top:12px;color:#8663a5}.countdown-bottom>span{font-family:'Manrope Variable',sans-serif;font-weight:500;font-size:13px;line-height:1.6}
.goal-motto{padding:28px;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;border-left:1px solid #e8e0ef}.without-countdown .goal-motto{border-left:0}.goal-motto>p{font-family:'Manrope Variable',sans-serif;font-size:19px;line-height:1.55;font-weight:600;margin:13px 0 22px;color:var(--student-ink,#392049);overflow-wrap:anywhere;max-width:100%}.goal-actions{display:flex;align-items:center;flex-wrap:wrap;gap:16px}.goal-actions button{font-size:11px}
.goal-editor{grid-column:1/-1;padding:24px;border-top:1px solid #eee7f6;display:grid;gap:18px}.goal-editor-heading{display:flex;align-items:center;justify-content:space-between;gap:15px}.goal-editor-heading h3{font-size:17px}.goal-editor label{display:grid;gap:8px;font-size:12px}.goal-editor input:not([type=checkbox]){width:100%;padding:12px;border:1px solid #dcd3e8;border-radius:9px;background:var(--student-card,#fff);color:inherit}.goal-editor small{display:block;font-size:11px;line-height:1.5;color:var(--student-muted,#70657c)}.goal-editor .countdown-switch{display:flex;align-items:center;gap:12px;padding:15px;background:var(--student-bg,#faf7fd);border:1px solid #e5ddef;border-radius:12px}.countdown-switch input{width:18px;height:18px;accent-color:#552783;flex-shrink:0}.countdown-switch small{margin-top:4px}.learning-goals>.error{grid-column:1/-1;padding:15px}
@media(max-width:1150px){.countdown-body{flex-wrap:wrap}.countdown-caption{gap:5px}.countdown-numbers>span{width:43px;height:58px;font-size:33px}}
@media(max-width:650px){.learning-goals{grid-template-columns:1fr}.goal-countdown{padding:22px}.goal-motto{border-left:0;border-top:1px solid #e8e0ef;padding:22px}.without-countdown .goal-motto{border-top:0}.goal-motto>p{font-size:18px}.countdown-body{gap:14px;margin:20px 0}.countdown-numbers{gap:5px}.countdown-numbers>span{width:42px;height:57px;font-size:32px}.goal-editor .form-row{display:grid;grid-template-columns:1fr}.countdown-caption strong{font-size:9px}.goal-editor{padding:20px}}
/* A compact violet keepsake, with the same typography as the rest of SISU. */
.goal-countdown{isolation:isolate;background:linear-gradient(125deg,#361653 0%,#512383 58%,#6c3a9d 100%);color:#fff;padding:28px 30px}
.goal-countdown:before{content:'';position:absolute;z-index:-1;width:245px;height:245px;border:1px solid #ffffff18;border-radius:50%;right:-115px;top:-105px;box-shadow:0 0 0 30px #ffffff05,0 0 0 60px #ffffff05;pointer-events:none}
.goal-symbol{background:#ffffff13;border-color:#ffffff25;color:#e9d8ff;border-radius:13px}
.countdown-heading .eyebrow{color:#d7c0ef;letter-spacing:1.8px;font-size:9px}
.learning-goals .countdown-heading h2{color:#fff;font-size:19px;font-weight:700}
.remove-countdown{color:#decaef}.remove-countdown:hover{background:#ffffff18;color:white}
.countdown-body{margin:26px 0 22px;gap:20px}
.countdown-numbers{gap:8px}.countdown-numbers>span{width:52px;height:68px;border-color:#ffffff65;border-radius:11px;background:linear-gradient(#fff 49%,#e8dff2 50%,#f5f0fa 51%);font-size:39px;color:#49206f;box-shadow:0 4px 0 #24113540,0 6px 16px #20102f20}
.countdown-caption strong{color:#fff;font-size:10px;letter-spacing:1.7px}.countdown-caption small{color:#e0cdef;font-size:12px}
.countdown-bottom{border-color:#ffffff20;color:#e4d5f1;padding-top:15px}.countdown-bottom>span{font-size:12px;font-weight:500}.countdown-bottom svg{color:#d8b9f4}
.goal-motto{border-left:0;padding:30px}.goal-motto>p{font-size:18px;line-height:1.65}
@media(max-width:650px){.goal-countdown{padding:24px}.countdown-numbers>span{width:46px;height:61px;font-size:35px}.goal-motto{padding:24px}}
</style>
