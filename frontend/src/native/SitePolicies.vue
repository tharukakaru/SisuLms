<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
import ActionNotice from './ActionNotice.vue'
const emit=defineEmits(['plans','manage'])
const data=ref(null),page=ref(0),busy=ref(false),error=ref(''),note=ref(''),reasons=ref({})
async function load(){data.value=await request('site_policies','listing',{page:page.value},'GET')}
async function run(fn){if(busy.value)return;busy.value=true;error.value='';note.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}
async function retry(site){await run(async()=>{const result=await request('site_policies','retry',{tenant:site.name,reason:reasons.value[site.name]||''});await load();note.value=result.message;reasons.value[site.name]=''})}
onMounted(()=>run(load))
</script>
<template><section class="site-policies"><ActionNotice :message="error||note" :failure="!!error"/>
<header><div><h2>Hosted website policies</h2><p>Check delivery of technical settings to separately hosted institute websites.</p></div><button class="button subtle" :disabled="busy" @click="run(load)">Refresh status</button></header>
<section class="policy-explanation"><h3>Looking for subscription plans?</h3><p>Individual, Silver, Gold and Platinum prices, card descriptions and included tools are managed in Plans. They are shared across the website and provider dashboards.</p><button class="button primary" @click="emit('plans')">Manage subscription plans</button></section>
<p>This page tracks secure hosting-policy updates, including the hosted-site account status and infrastructure settings used by older sites. It does not change customer prices or provision a website.</p>
<p v-if="error" class="error" role="alert">{{error}}</p><p v-if="note" role="status">{{note}}</p><p v-if="busy" role="status">Checking...</p>
<template v-if="data"><p v-if="!data.sites.length" class="empty">No separately hosted institute websites registered.</p>
<article v-for="site in data.sites" :key="site.name" class="site-card"><header><div><h3>{{site.title}}</h3><p>{{site.website}}</p></div><span class="status" :class="{confirmed:site.status==='Delivery confirmed'}">{{site.status}}</span></header>
<dl><div><dt>Website setup</dt><dd>{{site.setup_ready?'Marked ready':'Setup pending'}}</dd></div><div><dt>Recorded account status</dt><dd>{{site.enabled?'Enabled':'Suspended'}}</dd></div><div><dt>Last confirmed update</dt><dd>{{site.last_confirmed||'Not confirmed'}}<small v-if="site.last_confirmed">UTC · revision {{site.revision}}</small></dd></div></dl>
<p class="hint">Confirmation means the website acknowledged an update. It does not guarantee that the website is online now or that subscription payments are complete.</p>
<div v-if="site.blockers.length" class="setup-needed"><strong>Hosting setup needed</strong><ul><li v-for="item in site.blockers" :key="item">{{item}}</li></ul></div>
<template v-else><label :for="'reason-'+site.name">Reason for retry<input :id="'reason-'+site.name" v-model="reasons[site.name]" maxlength="1000" placeholder="For example: Retry after hosting connection was corrected"></label><small>At least 10 characters. A retry sends the saved policy; it does not edit it.</small><button class="button primary" :disabled="busy||(reasons[site.name]||'').trim().length<10" @click="retry(site)">Retry policy delivery</button></template>
<button class="button subtle" :disabled="busy" @click="emit('manage',site)">Manage institute</button></article>
<nav v-if="page>0||data.has_next" aria-label="Hosted website pages"><button class="button subtle" :disabled="busy||page===0" @click="page--;run(load)">Previous</button><button class="button subtle" :disabled="busy||!data.has_next" @click="page++;run(load)">Next</button></nav></template>

</section></template>
<style scoped>
.site-policies{font:15px/1.6 system-ui,sans-serif;color:var(--ink,#30243c)}header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}h2{font-size:26px;margin:0}h3{margin:0;font-size:19px}p{color:var(--muted,#71667d)}.policy-explanation{border:1px solid #ded2ef;border-radius:16px;background:var(--surface-alt,#f8f4fd);padding:24px;margin:24px 0}.site-card{border:1px solid #dfd7e9;border-radius:16px;padding:24px;margin:20px 0}.site-card header p{margin:5px 0;overflow-wrap:anywhere}.status{font-size:12px;padding:7px 12px;background:#fff2d9;color:#7e5415;border-radius:20px}.status.confirmed{background:#e6f5ec;color:#24613c}dl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;margin:24px 0}dt{font-size:12px;color:var(--muted,#71667d)}dd{margin:6px 0 0;font-weight:600}small{display:block;font-size:12px;font-weight:400}.hint{font-size:12px}.setup-needed{padding:16px;background:var(--surface-alt,#faf6ef);border-radius:10px;margin-bottom:16px}.setup-needed ul{margin-bottom:0}.site-card label{display:grid;gap:8px;margin-top:20px}.site-card input{font:inherit;box-sizing:border-box;width:100%;padding:12px;border:1px solid #ded2ef;border-radius:10px;background:var(--surface,#fff);color:inherit}.site-policies .button{font:inherit;border:1px solid #ded2ef;border-radius:10px;padding:10px 16px;cursor:pointer;margin:12px 8px 0 0;background:#f4effa;color:#4d2474}.site-policies .button.primary{background:#55258b;color:white}.button:disabled{opacity:.45;cursor:default}.legacy-info{border-top:1px solid #ded2ef;padding-top:24px;margin-top:28px}summary{cursor:pointer;font-weight:600}@media(max-width:650px){header{flex-direction:column}dl{grid-template-columns:1fr}.site-card{padding:18px}}button:focus-visible{outline:3px solid #9a70c1;outline-offset:3px}
</style>
