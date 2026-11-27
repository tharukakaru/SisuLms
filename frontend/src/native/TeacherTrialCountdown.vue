<script setup>
import {computed,ref,onMounted,onBeforeUnmount,watch} from 'vue'
import {Clock3,Building2,CheckCircle2} from 'lucide-vue-next'
import {request} from './client'
import {trialCountdown} from '../shared/trialCountdown.js'

const props=defineProps({context:Object})
const active=ref(false),remaining=ref(0)
const parts=computed(()=>trialCountdown(remaining.value))
const label=computed(()=>parts.value.expired?'Trial ended':parts.value.urgent?'Trial ends soon':'Personal trial')
const accessible=computed(()=>`${label.value}: ${parts.value.days} days, ${parts.value.hours} hours, ${parts.value.minutes} minutes remaining`)
let deadline=0,tickTimer,syncTimer,inflight=false,disposed=false
function applyContext(value){if(!value)return;active.value=value.state==='Trial'&&value.kind==='Personal';deadline=performance.now()+Math.max(0,value.remaining_ms||0);tick()}
watch(()=>props.context,applyContext)
function tick(){remaining.value=Math.max(0,deadline-performance.now())}
async function sync(){
  if(props.context)return
  if(inflight||disposed||document.visibilityState==='hidden')return
  inflight=true
  try{
    const result=await request('account_billing','teacher_trial',{},'GET')
    if(disposed)return
    active.value=result.active===true&&Number.isFinite(result.remaining_ms)
    deadline=performance.now()+Math.max(0,result.remaining_ms||0)
    tick()
  }catch{active.value=false}finally{inflight=false}
}
function visible(){if(document.visibilityState==='visible')sync()}
onMounted(()=>{
  if(props.context)applyContext(props.context);else sync();tickTimer=setInterval(tick,1000);if(!props.context)syncTimer=setInterval(sync,60000)
  document.addEventListener('visibilitychange',visible)
})
onBeforeUnmount(()=>{disposed=true;clearInterval(tickTimer);clearInterval(syncTimer);document.removeEventListener('visibilitychange',visible)})
</script>

<template>
  <div v-if="context?.kind==='Institute'" class="teacher-trial teacher-plan" :class="{'teacher-trial--urgent':!context.available}" :title="`${context.title} · ${context.state}`"><Building2 :size="17" aria-hidden="true"/><div><span>{{context.available?'Institute plan':'Institute plan · Inactive'}}</span><strong>{{context.plan?`SISU ${context.plan}`:'No plan selected'}}</strong></div></div>
  <div v-else-if="active" class="teacher-trial" :class="{'teacher-trial--urgent':parts.urgent}" role="timer" :aria-label="accessible" aria-live="off">
    <Clock3 :size="17" aria-hidden="true"/>
    <div><span>{{label}}</span><strong>{{parts.days}}<small>d</small> {{String(parts.hours).padStart(2,'0')}}<small>h</small> {{String(parts.minutes).padStart(2,'0')}}<small>m</small></strong></div>
  </div>
  <div v-else-if="context" class="teacher-trial teacher-plan" :class="{'teacher-trial--urgent':!context.available}"><CheckCircle2 v-if="context.available" :size="17" aria-hidden="true"/><Clock3 v-else :size="17" aria-hidden="true"/><div><span>{{context.available?'Personal plan':'Personal workspace'}}</span><strong>{{context.available?`SISU ${context.plan}`:'Subscription required'}}</strong></div></div>
</template>

<style scoped>
.teacher-trial{display:flex;align-items:center;gap:9px;padding:8px 12px;border-radius:10px;background:#f3edf9;color:#562b90;flex:none;white-space:nowrap}
.teacher-trial>div{display:grid;gap:3px}.teacher-trial span{font-size:11px;font-weight:550;line-height:1.2}.teacher-trial strong{font-size:14px;line-height:1.2;font-weight:750;font-variant-numeric:tabular-nums}.teacher-trial small{font-size:11px;font-weight:550;margin-left:2px}.teacher-trial--urgent{background:#fff0f0;color:#a51d32}
.teacher-plan strong{max-width:210px;overflow:hidden;text-overflow:ellipsis}.teacher-plan strong{font-size:13px}
@media(max-width:600px){.teacher-trial{gap:0;padding:7px 8px}.teacher-trial>svg{display:none}.teacher-trial strong{font-size:12px}.teacher-trial span{font-size:10px}.teacher-trial small{font-size:10px}}
@media(max-width:600px){.teacher-plan strong{max-width:110px}}
</style>
