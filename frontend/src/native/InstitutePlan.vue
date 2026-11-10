<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
const data=ref(null),error=ref('')
const labels={integrations:'Connected teaching tools',news:'News publishing',expenses:'Expense register',custom_domain:'Custom domain',view_limits:'Video view controls',reviews:'Class reviews',watermark:'Video watermark',tute_delivery:'Tute delivery',white_label:'Institute branding'}
async function load(){error.value='';try{data.value=await request('classroom_handover','institute_plan',{},'GET')}catch(e){error.value=e.message}}
onMounted(load)
</script>
<template><section><div class="page-heading"><div><h1>Institute plan</h1><p>Your institute manages its subscription.</p></div></div><p v-if="error" class="error" role="alert">{{error}} <button class="text-button" @click="load">Try again</button></p><section v-else-if="data" class="panel" style="padding:28px"><h2>{{data.institute}}</h2><p>{{data.plan||'Plan details are not available yet'}} <span class="badge">{{data.state}}</span></p><p v-if="data.description">{{data.description}}</p><ul v-if="data.plan"><li v-for="(feature,i) in data.card_features" :key="i">{{feature}}</li></ul><p>Contact your institute administrator about plan access or changes.</p></section><p v-else role="status">Loading institute plan…</p></section></template>
