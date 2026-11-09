<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
const props=defineProps({purpose:String});const emit=defineEmits(['back'])
const data=ref({institutes:[],requests:[]}),selected=ref([]),busy=ref(false),message=ref(''),error=ref('')
async function load(){data.value=await request('profiles','institute_join_options',{},'GET')}
async function submit(){busy.value=true;error.value='';try{const r=await request('profiles','request_institutes',{profiles:selected.value,purpose:props.purpose});message.value=r.message;selected.value=[];await load()}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(async()=>{try{await load()}catch(e){error.value=e.message}})
</script>
<template>
  <section class="join-picker">
    <button type="button" class="sisu-back-link" @click="emit('back')">← Back to teaching options</button>
    <h2>{{purpose==='Existing teacher confirmation'?'Confirm your existing institute registration':'Apply to an institute'}}</h2>
    <p class="join-picker-lead">Choose up to five institutes. Each institute must review your request before granting access.</p>
    <p v-if="error" class="join-picker-error" role="alert">{{error}}</p>
    <p v-if="message" class="join-picker-notice" role="status">{{message}}</p>
    <form class="join-picker-form" @submit.prevent="submit">
      <div class="join-picker-list">
        <label v-for="p in data.institutes" :key="p.name" class="join-picker-item">
          <input type="checkbox" :value="p.name" v-model="selected" :disabled="busy||(!selected.includes(p.name)&&selected.length>=5)"/>
          <span><strong>{{p.display_name}}</strong> · @{{p.username}}</span>
        </label>
      </div>
      <p v-if="!data.institutes.length" class="join-picker-empty">No verified institutes are available in this workspace directory yet.</p>
      <button type="submit" class="join-submit-pill" :disabled="busy||!selected.length">
        <span>Submit request</span>
        <span aria-hidden="true">→</span>
      </button>
    </form>
    <div v-if="data.requests.length" class="join-requests-box">
      <h3>Your requests</h3>
      <p v-for="r in data.requests" :key="r.name">
        <strong>{{data.institutes.find(p=>p.name===r.profile)?.display_name||'Institute'}}</strong> · {{r.request_purpose}} · {{r.status==='Pending'?'Waiting for institute confirmation':r.status}}
      </p>
    </div>
  </section>
</template>
<style scoped>
.join-picker {
  padding: 24px;
  border-radius: 22px;
  background: #fcfcfe;
  border: 1px solid #e9e8ef;
  font-family: 'Manrope', Inter, system-ui, sans-serif;
}

.sisu-back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
  padding: 0;
  border: 0;
  background: none;
  color: #56288d;
  font: 500 13px 'Manrope', sans-serif;
  cursor: pointer;
}

.sisu-back-link:hover {
  text-decoration: underline;
}

.join-picker h2 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 800;
  color: #19182e;
}

.join-picker-lead {
  margin: 0 0 16px;
  font-size: 14px;
  color: #787788;
  line-height: 1.5;
}

.join-picker-list {
  display: grid;
  gap: 10px;
  margin-bottom: 16px;
}

.join-picker-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #e9e8ef;
  font-size: 14px;
  color: #19182e;
  cursor: pointer;
}

.join-picker-item input[type='checkbox'] {
  width: 16px;
  height: 16px;
  accent-color: #56288d;
}

.join-submit-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  min-height: 54px;
  padding: 12px 22px;
  border: 1px solid #56288d;
  border-radius: 27px;
  background: #56288d;
  color: #ffffff;
  font: 700 14px 'Manrope', sans-serif;
  cursor: pointer;
}

.join-submit-pill:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.join-picker-error {
  padding: 12px 16px;
  border-radius: 13px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 13px;
}

.join-picker-notice {
  padding: 12px 16px;
  border-radius: 13px;
  background: #eff8f2;
  border: 1px solid #cddfd4;
  color: #24543b;
  font-size: 13px;
}

.join-requests-box {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e9e8ef;
}

.join-requests-box h3 {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 800;
  color: #19182e;
}

.join-requests-box p {
  margin: 6px 0;
  font-size: 13px;
  color: #787788;
}

@media (max-width: 640px) {
  .join-picker {
    padding: 18px 16px;
    border-radius: 20px;
  }

  .join-picker h2 {
    font-size: 20px;
  }

  .join-picker-item {
    padding: 12px 14px;
    border-radius: 13px;
  }

  .join-submit-pill {
    min-height: 48px;
    padding: 12px 18px;
    border-radius: 27px;
  }
}
</style>
