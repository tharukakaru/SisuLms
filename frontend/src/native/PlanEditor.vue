<script setup>
import {ref,computed,onMounted} from 'vue'
import {request} from './client'
import ActionNotice from './ActionNotice.vue'
const data=ref(null),original=ref(null),busy=ref(false),error=ref(''),note=ref(''),reason=ref(''),expanded=ref(true),preview=ref(false),reviewed=ref(false)
const selected=ref('Individual')
const plan=computed(()=>data.value?.plans[selected.value])
const changes=computed(()=>{
 if(!data.value||!original.value)return []
 const rows=[]
 for(const [name,p] of Object.entries(data.value.plans)){
  const old=original.value[name]
  if(p.monthly_lkr!==old.monthly_lkr)rows.push(`${name}: monthly price LKR ${old.monthly_lkr.toLocaleString()} to LKR ${Number(p.monthly_lkr).toLocaleString()}`)
  for(const key of data.value.editable_features)if(p.features[key]!==old.features[key])rows.push(`${name}: ${data.value.feature_labels[key]} access ${p.features[key]?'enabled':'disabled'} for current subscribers`)
  if(p.description!==old.description||JSON.stringify(p.card_features)!==JSON.stringify(old.card_features))rows.push(`${name}: plan card text updated`)
 }
 return rows
})
const signature=computed(()=>JSON.stringify(data.value?.plans))
const reviewedSignature=ref('')
const ready=computed(()=>reviewed.value&&reviewedSignature.value===signature.value&&changes.value.length>0)
function accept(value){data.value=value;original.value=JSON.parse(JSON.stringify(value.plans));reviewed.value=false;preview.value=false}
async function load(){accept(await request('plan_catalog','admin_get'))}
async function run(fn){if(busy.value)return;busy.value=true;error.value='';note.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}
function move(items,index,direction){const to=index+direction;if(to<0||to>=items.length)return;[items[index],items[to]]=[items[to],items[index]]}
function review(){preview.value=true;reviewed.value=true;reviewedSignature.value=signature.value}
async function publish(){if(!ready.value)return;await run(async()=>{accept(await request('plan_catalog','publish',{plans:data.value.plans,revision:data.value.revision,reason:reason.value}));reason.value='';note.value='Plans published to the shared catalogue. Website and dashboard plan cards update on refresh. Existing invoices are unchanged.'})}
onMounted(()=>run(load))
</script>
<template>
<section class="catalog-editor">
 <ActionNotice :message="error||note" :failure="!!error"/>
 <header><div><h2>Subscription plans</h2><p>One published catalogue for your website and provider dashboards.</p></div><span v-if="data" class="revision">Published version {{data.revision}}</span></header>
 <p v-if="error" role="alert" class="error">{{error}}</p><p v-if="note" role="status">{{note}}</p>
 <p v-if="!data&&!error" role="status">Loading plans...</p><button v-if="!data&&error" class="button subtle" @click="run(load)">Try again</button>
 <form v-if="data" @submit.prevent="publish">
  <nav aria-label="Choose plan to edit"><button v-for="name in Object.keys(data.plans)" :key="name" type="button" :aria-pressed="selected===name" :disabled="busy" @click="selected=name">{{name}}</button></nav>
  <div class="editor-columns">
   <fieldset :disabled="busy" class="plan-fields"><legend>{{selected}} plan</legend>
    <label>Monthly price (LKR)<input type="number" v-model.number="plan.monthly_lkr" min="1" max="10000000" step="1" required></label>
    <label>Short description<textarea v-model="plan.description" maxlength="500" rows="3" placeholder="Who is this plan for?"></textarea></label>
    <h3>Features shown on the card</h3><p class="hint">Describe what customers receive. These words do not enable or disable tools.</p>
    <div v-for="(feature,i) in plan.card_features" :key="selected+'-'+i" class="feature-row"><input v-model="plan.card_features[i]" :aria-label="'Feature '+(i+1)" maxlength="160" required placeholder="Feature description"><div class="row-actions"><button type="button" :disabled="i===0" :aria-label="'Move feature '+(i+1)+' up'" @click="move(plan.card_features,i,-1)">Up</button><button type="button" :disabled="i===plan.card_features.length-1" :aria-label="'Move feature '+(i+1)+' down'" @click="move(plan.card_features,i,1)">Down</button><button type="button" :aria-label="'Remove feature '+(i+1)" @click="plan.card_features.splice(i,1)">Remove</button></div></div>
    <button type="button" class="button subtle" :disabled="plan.card_features.length>=40" @click="plan.card_features.push('')">+ Add feature</button>
    <details class="tool-access"><summary>Included tools & access</summary><p class="hint">These switches affect current subscribers after publication. Service setup is still required. Card text is edited separately above.</p><label v-for="key in data.editable_features" :key="key" class="toggle-row"><span>{{data.feature_labels[key]}}</span><input type="checkbox" v-model="plan.features[key]"></label></details>
   </fieldset>
   <aside class="preview-column"><span class="eyebrow">CARD PREVIEW</span><article class="preview-card"><h3>{{selected}}</h3><p>{{plan.description}}</p><div class="preview-price">LKR {{Number(plan.monthly_lkr||0).toLocaleString()}}<small>per month</small></div><ul><li v-for="(feature,i) in plan.card_features" :key="i"><span aria-hidden="true">&#10003;</span>{{feature||'Your feature description'}}</li></ul><span class="preview-cta">Choose plan</span></article><p class="hint">Preview only. Active-student usage fees and class tuition are separate. Student limits and usage rates are unchanged by this editor.</p></aside>
  </div>
  <section class="publish-panel"><h3>Review & publish</h3><p>New prices apply to future invoices. Existing invoices and paid periods keep their dates and amounts.</p><label>Reason for this update<textarea v-model="reason" minlength="10" maxlength="1000" required :disabled="busy" placeholder="Explain what you changed and why"></textarea></label>
   <button type="button" class="button subtle" :disabled="busy||!changes.length" @click="review">Review changes</button>
   <div v-if="preview" class="change-review"><h4>Changes to publish</h4><ul><li v-for="row in changes" :key="row">{{row}}</li></ul><p v-if="!changes.length">No changes to publish.</p><p v-if="!ready&&changes.length">Your edits changed. Review again before publishing.</p></div>
   <div class="publish-actions"><button class="button primary" :disabled="busy||!ready||reason.trim().length<10">{{busy?'Publishing...':'Publish plan changes'}}</button><button type="button" class="button subtle" :disabled="busy" @click="run(load)">Discard edits & reload</button></div>
  </section>
 </form>
</section>
</template>
<style scoped>
.catalog-editor .button{border:1px solid #ded5e9;border-radius:10px;padding:11px 17px;font:inherit;cursor:pointer;background:#f4effa;color:#4d2474}.catalog-editor .button.primary{background:#55258b;color:#fff;border-color:#55258b}.catalog-editor{font:15px/1.6 system-ui,sans-serif;color:var(--ink,#30243c)}header{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}h2{margin:0;font-size:28px}h3{margin:20px 0 8px}p{color:var(--muted,#71667d)}.revision,.eyebrow{font-size:12px;color:#765794}.revision{white-space:nowrap;padding:8px 12px;background:#f4effa;border-radius:20px}nav{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}button,input,textarea{font:inherit}nav button,.row-actions button{border:1px solid #ded5e9;background:var(--surface,#fff);color:inherit;border-radius:10px;padding:10px 16px;cursor:pointer}nav button[aria-pressed=true]{background:#55258b;color:#fff;border-color:#55258b}.editor-columns{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(260px,1fr);gap:28px}fieldset{min-width:0;border:1px solid #ded5e9;border-radius:18px;padding:24px}legend{font-weight:700;font-size:20px;padding:0 10px}label{display:grid;gap:8px;margin:0 0 20px}input:not([type=checkbox]),textarea{box-sizing:border-box;width:100%;padding:12px;border:1px solid #ded5e9;border-radius:10px;background:var(--surface,#fff);color:inherit}.hint{font-size:13px}.feature-row{margin:12px 0}.row-actions{display:flex;gap:6px;margin-top:6px;justify-content:flex-end}.row-actions button{font-size:12px;padding:6px 10px}.tool-access{border-top:1px solid #ded5e9;margin-top:24px;padding-top:20px}.tool-access summary{font-weight:700;cursor:pointer}.toggle-row{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-bottom:1px solid #eee;margin:0}.toggle-row input{width:20px;height:20px;accent-color:#55258b}.preview-card{padding:28px;border:1px solid #d9cae9;border-top:5px solid #6e3d9f;border-radius:18px;background:var(--surface,#fff);margin-top:12px;overflow-wrap:anywhere;box-shadow:0 8px 24px #3018440a}.preview-card h3{font-size:28px;margin:0}.preview-price{font-size:29px;font-weight:700;margin:24px 0}.preview-price small{display:block;font-size:13px;font-weight:400}.preview-card ul{list-style:none;padding:0;display:grid;gap:12px}.preview-card li{display:flex;gap:10px}.preview-card li span{color:#6e3d9f}.preview-cta{display:block;padding:12px;background:#55258b;color:white;text-align:center;border-radius:10px;margin-top:24px}.publish-panel{border:1px solid #ded5e9;padding:24px;border-radius:18px;margin-top:28px}.publish-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:20px}.change-review{padding:16px;background:#f7f3fc;border-radius:12px;margin-top:16px;color:#30243c}button:disabled{opacity:.45;cursor:default}button:focus-visible{outline:3px solid #9a70c1;outline-offset:3px}@media(max-width:800px){.editor-columns{grid-template-columns:1fr}header{flex-direction:column}.plan-fields,.publish-panel{padding:18px}}
</style>
