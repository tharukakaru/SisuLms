<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
import BankPayments from './BankPayments.vue'
const props=defineProps({member:Object,rooms:Array})
const data=ref(null),error=ref(''),busy=ref(false)
const roomTitle=id=>props.rooms?.find(r=>r.name===id)?.title||id
async function load(){busy.value=true;error.value='';try{data.value=await request('student_billing','status')}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(load)
</script>
<template><section><header class="page-heading"><div><span class="eyebrow">YOUR LEARNING & PAYMENTS</span><h1>Your providers & class invoices</h1><p>Your teacher or institute pays for its SISU plan. You pay only your applicable class fees.</p></div><button class="button subtle" :disabled="busy" @click="load">Refresh</button></header><p v-if="error" role="alert">{{error}}</p><template v-if="data"><section class="panel student-billing-panel"><h2>Your providers’ plans</h2><article v-for="p in data.providers" :key="p.kind+p.name"><h3>{{p.name}}</h3><p>{{p.kind}} · {{p.plan}}</p></article><p v-if="!data.providers.length">Provider plans appear after you enrol in a classroom.</p></section><section class="panel student-billing-panel"><h2>Your class invoices</h2><p>Invoices are issued for class fees. Uploaded bank slips appear below with their review status.</p><article v-for="i in data.invoices" :key="i.name"><h3>{{roomTitle(i.classroom)}}</h3><p>{{i.name}} · LKR {{i.amount}} · {{i.status}}</p><small>Due {{i.due_date}}</small></article><p v-if="!data.invoices.length">No class invoices have been issued to you yet.</p></section><BankPayments :member="member" :rooms="rooms" :invoices="data.invoices" @changed="load"/></template></section></template>
<style scoped>.student-billing-panel{padding:24px;margin-bottom:20px}.student-billing-panel article{padding:16px 0;border-bottom:1px solid var(--student-border)}.student-billing-panel p{line-height:1.7;margin:10px 0}</style>
