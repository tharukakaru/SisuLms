<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
const data=ref(null),error=ref(''),busy=ref(false),notice=ref('')
async function load(){try{data.value=await request('usage_billing','status')}catch(e){error.value=e.message}}
async function activate(name){busy.value=true;try{await request('usage_billing','request_activation',{invoice:name});notice.value='Activation requested. This does not verify payment. Super Admin will review settlement.';await load()}catch(e){error.value=e.message}finally{busy.value=false}}
async function download(name){try{const r=await request('usage_billing','document',{invoice:name});const url=URL.createObjectURL(new Blob([r.html],{type:'text/html'}));const a=document.createElement('a');a.href=url;a.download=name+'.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch(e){error.value=e.message}}
onMounted(load)
</script>
<template><section v-if="data?.enabled || error" class="billing-section"><h2>Active-student invoices</h2><p v-if="error" role="alert">{{error}}</p><p v-if="notice" role="status">{{notice}}</p><p v-if="data?.blocked">Settle your outstanding usage bill and request activation. Super Admin must verify payment before restoring access.</p><p>Estimates appear five days before the paid period ends. Final invoices are due ten days after period end. Online payments remain unavailable.</p><article v-for="bill in data?.invoices" :key="bill.name"><h3>{{bill.name}} · {{bill.status}}</h3><p>{{bill.quantity}} active students × LKR {{bill.unit_rate}} = LKR {{bill.amount_lkr}} · Due {{bill.due_at}}</p><button @click="download(bill.name)">Download invoice</button><button v-if="bill.status!=='Estimate'" :disabled="busy||bill.activation_requested" @click="activate(bill.name)">{{bill.activation_requested?'Review requested':'Request payment review / activation'}}</button></article><p v-if="data?.invoices?.length===0">No usage invoices yet. Trial attendance is excluded.</p></section></template>
