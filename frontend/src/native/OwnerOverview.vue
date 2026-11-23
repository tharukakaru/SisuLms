<script setup>
import {ref,onMounted,computed,watch} from 'vue'
import {request} from './client'
import Icon from '../Icon.vue'
import {campusAdminUrl} from './ownerNavigation.js'
import ActionNotice from './ActionNotice.vue'
const props=defineProps({canManage:Boolean}),people=ref(null)
const population=computed(()=>['Student','Teacher','Institute'].map(kind=>({kind,total:people.value?.campuses.filter(c=>c.available).flatMap(c=>c.counts).filter(c=>c.kind===kind).reduce((n,c)=>n+Number(c.total),0)??0})))
async function loadPeople(){if(!props.canManage){people.value=null;return}try{people.value=await request('owner_people','overview',{},'GET')}catch{people.value=null}}
watch(()=>props.canManage,loadPeople)
const emit=defineEmits(['navigate']),data=ref(null),busy=ref(false),error=ref('')
const labels={student_memberships:'Student memberships',teachers:'Verified teachers',institutes:'Verified institutes',pending_profiles:'Provider reviews',pending_payouts:'Payout requests'}
const campuses=computed(()=>(data.value?.campuses||[]).map(c=>({...c,adminUrl:campusAdminUrl(c,window.location)})))
const reviews=computed(()=>campuses.value.filter(c=>c.available).reduce((sum,c)=>sum+Number(c.counts?.pending_profiles||0),0))
const shortcuts=[{name:'Plans',icon:'Package',text:'Subscription plans',detail:'Prices and included tools'},{name:'Billing',icon:'Receipt',text:'Provider billing',detail:'Accounts and invoices'},{name:'Admin access',icon:'ShieldCheck',text:'Administrator access',detail:'Owners and permissions'},{name:'Readiness',icon:'CircleCheck',text:'Service readiness',detail:'Connections and email delivery'}]
async function load(){if(busy.value)return;busy.value=true;error.value='';try{data.value=await request('owner_operations','overview',{},'GET')}catch(e){error.value=e.message;data.value=null}finally{busy.value=false}}
onMounted(()=>{load();loadPeople()})
</script>
<template>
<section class="overview" aria-label="Platform overview">
 <ActionNotice :message="error" :failure="true"/>
 <div class="overview-toolbar"><p>{{busy?'Refreshing campus records…':'Current records from your connected campuses.'}}</p><button class="button subtle" :disabled="busy" @click="load();loadPeople()">{{busy?'Refreshing…':'Refresh overview'}}</button></div>
 <p v-if="error" role="alert">{{error}}</p>
 <section v-if="canManage" class="population" aria-label="People and institutes"><header><h2>Your SISU community</h2><button class="button subtle" @click="emit('navigate','People & connections')">Explore people & connections <Icon name="ArrowRight" :size="16"/></button></header><dl v-if="people"><div v-for="item in population" :key="item.kind"><dt>{{item.kind==='Institute'?'Institutes':item.kind+'s'}}</dt><dd>{{item.total}}</dd></div></dl><p>{{people?.campuses.some(c=>!c.available)?'Partial totals: some campus reports are unavailable. ':''}}Accounts counted once per campus, including pending and disabled profiles. Open the directory to explore memberships and classes.</p></section>
 <template v-if="data">
  <dl class="overview-totals"><div><dt>Connected campuses</dt><dd>{{campuses.filter(c=>c.available).length}}<span>of {{campuses.length}} configured</span></dd></div><div><dt>Hosted institutes</dt><dd>{{data.hosted_institutes}}<button @click="emit('navigate','Organizations')">Manage institutes <Icon name="ArrowRight" :size="15"/></button></dd></div><div><dt>Provider reviews pending</dt><dd>{{reviews}}<span>Across available campuses</span></dd></div></dl>
  <div v-if="data.setup_pending" class="setup-attention"><Icon name="Clock3" :size="22"/><div><strong>{{data.setup_pending}} website {{data.setup_pending===1?'setup needs':'setups need'}} attention</strong><p>Review pending requests and the next hosting tasks.</p></div><button class="button subtle" @click="emit('navigate','Provisioning')">Review setup <Icon name="ArrowRight" :size="16"/></button></div>
  <div class="campus-heading"><h2>Connected campuses</h2><p>Open a campus to manage its providers, subscriptions and payouts.</p></div>
  <article v-for="campus in campuses" :key="campus.site" class="campus-record">
   <header><div class="campus-identity"><Icon name="Globe2" :size="22"/><div><h3>{{campus.site}}</h3><span class="campus-status" :class="campus.available?'is-connected':'is-unavailable'">{{campus.available?'Reporting connected':'Reporting unavailable'}}</span></div></div><a v-if="campus.available&&campus.adminUrl" class="button subtle" :href="campus.adminUrl" target="_blank" rel="noopener" :aria-label="`Open ${campus.site} administration in a new tab`">Open campus <Icon name="ArrowUpRight" :size="17"/></a></header>
   <p v-if="!campus.available" role="status">{{campus.message}}</p>
   <dl v-else class="campus-counts"><div v-for="(label,key) in labels" :key="key"><dt>{{label}}</dt><dd>{{campus.counts?.[key]??'—'}}</dd></div></dl>
   <p v-if="campus.available&&!campus.adminUrl" class="campus-unavailable">A local administration address is not configured for this campus.</p>
  </article>
  <p v-if="!campuses.length" class="empty-state">No campus reporting connections configured. Check Readiness to review platform connections.</p>
  <p class="overview-footnote">Membership totals are campus records, not unique people. Campus management requires an owner account authorized on that campus.</p>
 </template>
 <section class="overview-shortcuts" aria-labelledby="management-heading"><h2 id="management-heading">Management tools</h2><div><button v-for="item in shortcuts" :key="item.name" @click="emit('navigate',item.name)"><Icon :name="item.icon" :size="21"/><span><strong>{{item.text}}</strong><small>{{item.detail}}</small></span><Icon name="ArrowRight" :size="16"/></button></div></section>
</section>
</template>
<style scoped>
.population{padding:22px 24px;background:white;border:1px solid var(--line);border-radius:12px;margin-bottom:24px}.population header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}.population h2{font-size:18px;margin:0}.population .button{display:flex;align-items:center;gap:10px;margin:0}.population dl{display:flex;gap:40px;margin:24px 0}.population dl>div{flex:1}.population dt{color:var(--muted);font-size:13px}.population dd{font-size:30px;font-weight:700;margin:6px 0 0;font-variant-numeric:tabular-nums}.population p{font-size:12px;line-height:1.7;color:var(--muted);max-width:90ch}

.overview-toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px}.overview-toolbar p{margin:0;color:var(--muted)}.overview-toolbar .button{margin:0}.overview-totals{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));padding:24px 0;margin:0 0 24px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.overview-totals>div{padding:0 26px;border-right:1px solid var(--line)}.overview-totals>div:first-child{padding-left:0}.overview-totals>div:last-child{border:0}.overview-totals dt{font-size:13px;color:var(--muted)}.overview-totals dd{margin:10px 0 0;font-size:34px;font-weight:700;line-height:1.2;font-variant-numeric:tabular-nums}.overview-totals dd span,.overview-totals dd button{display:flex;align-items:center;gap:6px;margin:12px 0 0;font-size:12px;font-weight:400;line-height:1.5}.overview-totals dd span{color:var(--muted)}.overview-totals dd button{background:none;border:0;padding:0;color:var(--owner-purple);cursor:pointer;text-align:left}.setup-attention{display:flex;align-items:center;gap:16px;padding:18px 20px;background:#f1ebf8;border:1px solid #dfd2ef;border-radius:10px;color:#4e2a77;margin-bottom:32px}.setup-attention>div{flex:1}.setup-attention p{margin:4px 0 0;font-size:13px}.setup-attention .button{margin:0;display:flex;align-items:center;gap:10px;flex-shrink:0}.campus-heading h2,.overview-shortcuts h2{font-size:18px;margin:0}.campus-heading p{color:var(--muted);margin:7px 0 18px;font-size:13px}.campus-record{padding:22px 24px;background:white;border:1px solid var(--line);border-radius:12px;margin-bottom:14px}.campus-record header{display:flex;align-items:center;justify-content:space-between;gap:16px}.campus-identity{display:flex;gap:12px;align-items:center;min-width:0}.campus-identity>svg{color:var(--owner-purple);flex-shrink:0}.campus-record h3{font-size:15px;margin:0;overflow-wrap:anywhere}.campus-status{display:block;margin-top:3px;color:var(--muted);font-size:12px}.campus-record a{display:inline-flex;align-items:center;gap:10px;text-decoration:none;white-space:nowrap;margin:0}.campus-counts{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px;margin:22px 0 0;padding-top:20px;border-top:1px solid var(--line)}.campus-counts dt{color:var(--muted);font-size:12px}.campus-counts dd{font-size:24px;font-weight:650;margin:6px 0 0;font-variant-numeric:tabular-nums}.overview-footnote,.campus-unavailable{font-size:12px;color:var(--muted);line-height:1.7}.overview-shortcuts{margin-top:32px}.overview-shortcuts>div{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 28px;margin-top:10px}.overview-shortcuts button{display:flex;align-items:center;gap:14px;border:0;border-bottom:1px solid var(--line);background:transparent;padding:18px 0;color:var(--ink);text-align:left;cursor:pointer;font:inherit}.overview-shortcuts button>svg{color:var(--owner-purple);flex-shrink:0}.overview-shortcuts button>span{flex:1}.overview-shortcuts strong{display:block;font-size:13px;font-weight:650}.overview-shortcuts small{display:block;margin-top:3px;color:var(--muted);font-size:12px}.overview-shortcuts button:hover strong,.overview-totals button:hover{text-decoration:underline}.overview button:focus-visible,.overview a:focus-visible{outline:2px solid var(--owner-purple);outline-offset:4px}.empty-state{padding:24px;background:white;border:1px solid var(--line);border-radius:10px}
@media(max-width:1050px){.campus-counts{grid-template-columns:repeat(3,minmax(0,1fr))}.overview-totals>div{padding:0 16px}}
@media(max-width:600px){.overview-toolbar{align-items:flex-start}.overview-toolbar p{font-size:12px}.overview-totals{grid-template-columns:1fr;padding:0}.overview-totals>div,.overview-totals>div:first-child{padding:16px 0;border-right:0;border-bottom:1px solid var(--line)}.overview-totals dd{display:flex;align-items:center;gap:16px;font-size:28px}.overview-totals dd span,.overview-totals dd button{margin:0}.setup-attention{flex-wrap:wrap;gap:12px;padding:16px}.setup-attention>div{flex-basis:75%}.setup-attention .button{margin-left:34px}.campus-record{padding:18px}.campus-record header{align-items:flex-start;flex-direction:column;gap:14px}.campus-counts{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.overview-shortcuts>div{grid-template-columns:1fr}.campus-heading p{line-height:1.6}}
/* Reporting labels retain their text so state is not conveyed by colour alone. */
.campus-status{display:inline-flex;align-items:center;gap:6px;padding:3px 9px;margin-top:6px;border-radius:20px;font-weight:600;line-height:1.5}
.campus-status::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0}
.campus-status.is-connected{background:#eaf5ef;color:#286044}
.campus-status.is-unavailable{background:#fff3df;color:#805413}
.overview-shortcuts button{border-radius:8px;padding-inline:12px}
.overview-shortcuts button:hover{background:#eee6f7}
@media(max-width:600px){
 .overview-toolbar{flex-wrap:wrap}
 .population{padding:18px}
 .population dl{flex-wrap:wrap;gap:20px}
 .population dl>div{flex:1 1 100px;min-width:0}
 .population .button{white-space:normal;text-align:left}
 .overview-totals dd{flex-wrap:wrap}
}
</style>
