<script setup>
import {ref,computed,onMounted,watch} from 'vue'
import {request} from './client'
const props=defineProps({purpose:String});const emit=defineEmits(['back'])
const data=ref({institutes:[],requests:[]}),selected=ref([]),busy=ref(false),loading=ref(true),message=ref(''),error=ref(''),query=ref(''),submitted=ref(false)
const current=computed(()=>new Set(data.value.requests.filter(r=>['Pending','Active'].includes(r.status)).map(r=>r.profile)))
const remaining=computed(()=>Math.max(0,5-current.value.size))
const options=computed(()=>data.value.institutes.filter(p=>!current.value.has(p.name)&&p.display_name.toLowerCase().includes(query.value.trim().toLowerCase())))
const label=r=>data.value.institutes.find(p=>p.name===r.profile)?.display_name||'Institute'
async function load(){loading.value=true;error.value='';try{data.value=await request('profiles','institute_join_options',{},'GET')}catch(e){error.value=e.message}finally{loading.value=false}}
async function submit(){if(busy.value||!selected.value.length)return;busy.value=true;error.value='';try{const r=await request('profiles','request_institutes',{profiles:selected.value,purpose:props.purpose});message.value=r.message;selected.value=[];submitted.value=true;await load()}catch(e){error.value=e.message}finally{busy.value=false}}
function another(){submitted.value=false;message.value='';emit('back')}
watch(()=>props.purpose,()=>{selected.value=[];query.value='';message.value='';submitted.value=false})
onMounted(load)
</script>
<template>
  <section class="join-picker" :aria-busy="busy||loading">
    <p v-if="loading" role="status">Loading your institute requests…</p>
    <div v-if="error" class="join-error" role="alert">
      {{error}} <button type="button" :disabled="busy||loading" @click="load">Refresh requests</button>
    </div>
    <div v-if="message" class="join-success" role="status">
      <strong>Request sent</strong>
      <p>{{message}}</p>
    </div>
    <template v-if="purpose&&!submitted">
      <button type="button" class="join-back sisu-back-link" :disabled="busy" @click="emit('back')">← Back to teaching options</button>
      <h2>{{purpose==='Existing teacher confirmation'?'Choose your institute':'Where would you like to teach?'}}</h2>
      <p class="join-picker-lead">Choose up to {{remaining}} {{remaining===1?'institute':'institutes'}}. Access starts after the institute approves your request.</p>
      <template v-if="!loading&&remaining">
        <label class="join-search">
          Find an institute
          <input v-model="query" type="search" placeholder="Search institute name" :disabled="busy">
        </label>
        <form class="join-picker-form" @submit.prevent="submit">
          <div class="join-options join-picker-list">
            <label v-for="p in options" :key="p.name" class="join-picker-item" :class="{chosen:selected.includes(p.name)}">
              <input type="checkbox" :value="p.name" v-model="selected" :disabled="busy||(!selected.includes(p.name)&&selected.length>=remaining)"/>
              <span><strong>{{p.display_name}}</strong><small>@{{p.username}}</small></span>
            </label>
          </div>
          <p v-if="!options.length" class="join-empty join-picker-empty">{{query?'No institutes match this search.':'No other verified institutes are available right now.'}}</p>
          <div class="join-submit">
            <span>{{selected.length}} selected · {{remaining}} available</span>
            <button type="submit" class="join-primary join-submit-pill" :disabled="busy||!selected.length">
              <span>{{busy?'Sending request…':'Request access'}}</span>
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </form>
      </template>
      <p v-else-if="!loading">You have reached the five-institute limit.</p>
    </template>
    <section v-if="data.requests.length" class="request-list join-requests-box">
      <header>
        <h2>Your institute requests</h2>
        <button type="button" :disabled="busy||loading" @click="load">{{loading?'Checking…':'Refresh status'}}</button>
      </header>
      <article v-for="r in data.requests" :key="r.name">
        <div>
          <strong>{{label(r)}}</strong>
          <small>{{r.request_purpose==='Existing teacher confirmation'?'Teaching access confirmation':'Teaching application'}}</small>
        </div>
        <span :class="['request-status',{approved:r.status==='Active'}]">{{r.status==='Pending'?'Waiting for confirmation':r.status==='Active'?'Approved':r.status}}</span>
      </article>
    </section>
    <button v-if="submitted&&remaining" type="button" class="join-primary join-submit-pill" @click="another">Apply to another institute</button>
  </section>
</template>
<style scoped>
.join-picker{margin-top:24px;padding:24px;border-radius:22px;background:#fcfcfe;border:1px solid #e9e8ef;color:#19182e;font-family:'Manrope',Inter,system-ui,sans-serif}
.join-picker h2{margin:0 0 8px;font-size:20px;font-weight:800;line-height:1.4;color:#19182e}
.join-picker p{font-size:14px;line-height:1.6;color:#787788}
.join-picker button{padding:11px 18px;border:1px solid #ded3eb;border-radius:27px;background:#fff;color:#56288d;font:600 13px 'Manrope',sans-serif;cursor:pointer}
.join-picker button:disabled{opacity:.5;cursor:not-allowed}
.join-picker .join-back{border:0;background:transparent;padding-left:0;margin-bottom:12px}
.join-search{display:grid;gap:10px;font-size:13px;font-weight:600;color:#19182e;margin:20px 0 16px}
.join-search input{width:100%;box-sizing:border-box;padding:13px 16px;border:1px solid #e9e8ef;border-radius:13px;font:inherit;background:#fff;color:inherit}
.join-options{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.join-options label{display:flex;align-items:center;gap:14px;padding:16px 18px;border:1px solid #e9e8ef;border-radius:14px;background:#fff;cursor:pointer}
.join-options label.chosen{border-color:#6c6aee;background:#f0efff}
.join-options input{width:18px;height:18px;accent-color:#56288d;flex-shrink:0}
.join-options strong{font-size:14px;color:#19182e}
.join-options small,.request-list small{display:block;margin-top:4px;color:#787788;font-size:12px}
.join-submit{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:20px 0 0}
.join-submit>span{font-size:12px;color:#787788}
.join-picker .join-primary{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:12px 22px;background:#56288d;border-color:#56288d;border-radius:27px;color:#fff;font-weight:700}
.join-success,.join-error{padding:16px 18px;border-radius:13px;line-height:1.6;margin-bottom:18px;font-size:13px}
.join-success{background:#eff8f2;border:1px solid #cddfd4;color:#24543b}
.join-success p{margin-bottom:0;color:#24543b}
.join-error{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}
.request-list{margin:24px 0 0;padding-top:16px;border-top:1px solid #e9e8ef}
.request-list header{display:flex;align-items:center;justify-content:space-between;gap:12px}
.request-list article{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 0;border-bottom:1px solid #e9e8ef}
.request-status{font-size:12px;font-weight:600;padding:6px 12px;border-radius:20px;background:#fff5df;color:#856421}
.request-status.approved{background:#eff8f2;color:#24543b}
.join-picker :is(button,input):focus-visible{outline:3px solid #bda6dc;outline-offset:3px}
@media(max-width:650px){.join-picker{padding:18px 16px;border-radius:20px}.join-options{grid-template-columns:1fr}.request-list article{align-items:flex-start;flex-direction:column}.join-submit{flex-wrap:wrap}}
</style>
