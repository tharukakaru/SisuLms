<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
const props=defineProps({purpose:String});const emit=defineEmits(['back'])
const data=ref({institutes:[],requests:[]}),selected=ref([]),busy=ref(false),message=ref(''),error=ref('')
async function load(){data.value=await request('profiles','institute_join_options',{},'GET')}
async function submit(){busy.value=true;error.value='';try{const r=await request('profiles','request_institutes',{profiles:selected.value,purpose:props.purpose});message.value=r.message;selected.value=[];await load()}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(async()=>{try{await load()}catch(e){error.value=e.message}})
</script>
<template><section class="join-picker"><button @click="emit('back')">← Back to individual plan</button><h2>{{purpose==='Existing teacher confirmation'?'Confirm your existing institute registration':'Apply to an institute'}}</h2><p>Choose up to five institutes. Each institute must review your request before granting access.</p><p v-if="error" role="alert">{{error}}</p><p v-if="message" role="status">{{message}}</p><form @submit.prevent="submit"><label v-for="p in data.institutes" :key="p.name"><input type="checkbox" :value="p.name" v-model="selected" :disabled="busy||(!selected.includes(p.name)&&selected.length>=5)"/>{{p.display_name}} · @{{p.username}}</label><p v-if="!data.institutes.length">No verified institutes are available in this workspace directory yet.</p><button :disabled="busy||!selected.length">Submit request</button></form><h3 v-if="data.requests.length">Your requests</h3><p v-for="r in data.requests" :key="r.name">{{data.institutes.find(p=>p.name===r.profile)?.display_name||'Institute'}} · {{r.request_purpose}} · {{r.status==='Pending'?'Waiting for institute confirmation':r.status}}</p></section></template>
<style scoped>.join-picker{padding:20px}.join-picker label{display:flex;gap:12px;padding:16px;border-bottom:1px solid #e4dfed}.join-picker button{padding:12px 18px;border:1px solid #6942a1;border-radius:9px;margin:12px 0;background:#f5f0fc;color:#462571}.join-picker button:disabled{opacity:.5}</style>
