<script setup>
import BrandLogo from '../BrandLogo.vue'
import Icon from '../Icon.vue'
import {ownerSections,ownerSection} from './ownerNavigation.js'
import {notificationTime} from '../shared/notificationTime.js'
import ActionNotice from './ActionNotice.vue'
import OwnerProvisioning from './OwnerProvisioning.vue'
import {ref,onMounted,computed,nextTick} from 'vue'
import {request,csrf} from './client'
import {object} from './contracts'
import OwnerBilling from './OwnerBilling.vue'
import StudentCountAdmin from './StudentCountAdmin.vue'
import OwnerOverview from './OwnerOverview.vue'
import OwnerPeople from './OwnerPeople.vue'
import FinanceOperations from './FinanceOperations.vue'
import OwnerAccess from './OwnerAccess.vue'
import OwnerProfile from './OwnerProfile.vue'
import PlanEditor from './PlanEditor.vue'
import SitePolicies from './SitePolicies.vue'
const auditRows=ref([]),auditPage=ref(0),manifest=ref(null)
import './release.css'
const page=ref(0),spec=ref(null),monthlyPrice=ref(0),priceEnabled=ref(true),commercial=ref(null)
const tab=ref(ownerSection(window.location.hash)),data=ref(null),busy=ref(false),error=ref(''),note=ref(''),reason=ref(''),tenant=ref(''),domain=ref(''),override=ref('{"features":{},"limits":{},"support_tier":"standard"}'),state=ref('past_due'),grace=ref(''),days=ref(7),edit=ref(null),health=ref(null)
const navQuery=ref(''),navigationOpen=ref(false),operator=ref(null),ownerAccess=ref(null)
const currentSection=computed(()=>ownerSections.find(s=>s.name===tab.value)||ownerSections[0])
const navigationGroups=computed(()=>['Workspace','Finance','Platform','Help'].map(name=>({name,items:ownerSections.filter(s=>s.group===name&&(!s.managersOnly||ownerAccess.value?.can_manage)&&(s.name+' '+s.description).toLowerCase().includes(navQuery.value.trim().toLowerCase()))})).filter(g=>g.items.length))
const signingOut=ref(false)
const operatorName=computed(()=>operator.value?.name||operator.value?.email||'Your account')
const operatorInitials=computed(()=>operatorName.value.split(/\s+/).slice(0,2).map(s=>s[0]).join('').toUpperCase())
async function signOut(){if(signingOut.value)return;signingOut.value=true;try{const response=await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf()}});if(!response.ok)throw Error('Could not sign out. Please try again.');window.location.assign('/login?redirect-to=/campus')}catch(e){error.value=e.message;signingOut.value=false}}
async function loadOperator(){try{[operator.value,ownerAccess.value]=await Promise.all([request('admin_profile','current',{},'GET'),request('owner_access','access_list',{},'GET')])}catch{operator.value=null;ownerAccess.value=null}
  if(!ownerAccess.value?.can_manage&&ownerSections.find(s=>s.name===tab.value)?.managersOnly)tab.value='Overview'}
const emptyRegistration=()=>({title:'',code:'',site_hostname:'',admin_contact:'',plan:'Individual'})
const form=ref(emptyRegistration())
const commercialCatalog=ref(null)
const commercialPlanNames=computed(()=>Object.keys(commercialCatalog.value||{}))
const selectedCommercialPlan=ref('')
const selectedOrganization=computed(()=>data.value?.organizations.find(o=>o.name===tenant.value))
const monthlyLkr=computed({get:()=>monthlyPrice.value/100,set:value=>monthlyPrice.value=Math.round(Number(value)*100)})
const statusLabel=value=>({past_due:'Payment overdue',active:'Active',trial:'Trial',grace:'Grace period',suspended:'Suspended',cancelled:'Cancelled',expired:'Expired',registered:'Setup requested',pending:'Pending',ready:'Ready'}[value]||value||'Not set')
async function run(fn){if(busy.value)return;busy.value=true;error.value='';note.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}
async function load(){
 data.value=await request('release','control_room',{page:page.value},'GET')
 commercialCatalog.value=null
 try {
  const catalog=await request('plan_catalog','admin_get')
  if(!catalog?.plans || !['Individual','Silver','Gold','Platinum'].every(p=>Number.isFinite(Number(catalog.plans[p]?.monthly_lkr)) && Number(catalog.plans[p].monthly_lkr)>0)){
   throw new Error('Published commercial plan catalog is incomplete')
  }
  commercialCatalog.value=catalog.plans
 } catch(e) {
  console.error('Commercial plan catalog unavailable:',e)
 }
}
async function action(method,args){await run(async()=>{const result=await request('platform',method,args);if(method==='register'){form.value=emptyRegistration();page.value=0}manifest.value=null;note.value=method==='register'?'Institute setup request saved. Continue in Provisioning; the institute website is not active yet.':result.queued?'Invitation queued. Inbox delivery has not been confirmed.':result.requires_manifest_delivery?'Saved. Check Site policies for confirmation that the institute website received the update.':'Saved to the control plane.';await load()})}
async function choose(o){if(busy.value)return;resetRemoval();reason.value='';state.value='';grace.value='';days.value=7;manifest.value=null;commercial.value=null;tenant.value=o.name;selectedCommercialPlan.value=['Individual','Silver','Gold','Platinum'].includes(o.plan)?o.plan:'';domain.value=o.custom_domain||'';override.value=JSON.stringify(object(o.subscription?.overrides),null,2);await run(async()=>{commercial.value=await request('premium','summary',{tenant:o.name},'GET');monthlyPrice.value=commercial.value.offer?.amount_minor||0;priceEnabled.value=!!commercial.value.offer?.available});await nextTick();document.getElementById('organization-management')?.scrollIntoView({behavior:'smooth',block:'start'})}
async function openHostedSite(site){let org;await run(async()=>{org=await request('site_policies','organization_details',{tenant:site.name},'GET');const i=data.value.organizations.findIndex(o=>o.name===org.name);if(i>=0)data.value.organizations[i]=org;else data.value.organizations.unshift(org)});if(org){await selectTab('Organizations');await choose(org)}}
async function loadAudit(){auditRows.value=await request('owner_operations','audit',{page:auditPage.value},'GET')}
async function selectTab(name){if(!ownerSections.some(s=>s.name===name&&(!s.managersOnly||ownerAccess.value?.can_manage)))return;tab.value=name;navigationOpen.value=false;window.history.replaceState(null,'','#'+encodeURIComponent(name));if(name==='Audit log')await run(loadAudit);await nextTick();document.getElementById('owner-page-title')?.focus()}
async function saveCommercialPlan(){
 if(!selectedCommercialPlan.value)return
 await run(async()=>{
  await request('platform','update_commercial_plan',{
   tenant:tenant.value,
   plan:selectedCommercialPlan.value,
   reason:reason.value
  })
  await load()
  note.value='Commercial plan selection saved. No payment or entitlement activation occurred.'
 })
}
async function saveOverrides(){await run(async()=>{const values=JSON.parse(override.value);await request('platform','override',{tenant:tenant.value,values,reason:reason.value});manifest.value=null;await load();note.value='Overrides saved. Deliver a new signed policy to apply them on the institute site.'})}
async function saveOffer(){await run(async()=>{await request('premium','configure_offer',{tenant:tenant.value,amount_minor:monthlyPrice.value,enabled:priceEnabled.value,reason:reason.value});commercial.value=await request('premium','summary',{tenant:tenant.value},'GET');note.value='Monthly offer saved. Payments remain subject to the existing pause; no charge or activation occurred.'})}
async function exportManifest(){await run(async()=>{manifest.value=await request('platform','manifest',{tenant:tenant.value});note.value='Signed policy generated. Download and deliver it using the institute operator workflow; it has not been applied remotely.'})}
function downloadManifest(){const url=URL.createObjectURL(new Blob([JSON.stringify(manifest.value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='sisu-policy-'+tenant.value+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}

const removalPreview=ref(null)
const removalReason=ref('')
const removalCode=ref('')
const removalOpen=ref(false)

function resetRemoval(){
 removalPreview.value=null
 removalReason.value=''
 removalCode.value=''
 removalOpen.value=false
}



async function submitRemoval(){
 const preview=removalPreview.value
 if(!preview||preview.tenant_id!==tenant.value)return
 if(removalCode.value!==preview.code)return
 if(!window.confirm('Submit removal request for '+preview.title+'?'))return

 await run(async()=>{
  await request('tenant_retirement','request_removal',{
   tenant:preview.tenant_id,
   hostname:preview.hostname,
   code:removalCode.value,
   reason:removalReason.value
  })
  removalPreview.value.removal_status='Requested'
  removalPreview.value.removal_available=false
  note.value='Removal requested. The hosting worker will verify backups before retiring the website and dedicated database.'
 })
}

async function refreshRemoval(){
 if(!removalPreview.value)return
 await run(async()=>{const result=await request('tenant_retirement','removal_status',{tenant:removalPreview.value.tenant_id},'GET');removalPreview.value.removal_status=result.status;removalPreview.value.progress=result.progress;removalPreview.value.removal_available=result.status==='Failed';if(result.retired){note.value='Removal completed. The website and dedicated database are retired; private backups and audit history are retained.';await load()}})
}

async function reviewRemoval(){
 resetRemoval()
 const target=tenant.value
 removalOpen.value=true
 await run(async()=>{
  const result=await request(
   'tenant_retirement',
   'removal_preview',
   {tenant:target},
   'GET'
  )
  if(tenant.value===target)removalPreview.value=result
 })
}

onMounted(()=>{run(async()=>{await load();if(tab.value==='Audit log')await loadAudit()});loadOperator()})
</script>
<template><div class="owner-shell">
<a class="owner-skip" href="#owner-content">Skip to administration content</a>
<aside class="owner-sidebar">
  <div class="owner-brand"><BrandLogo/><span>Administration</span><button class="owner-menu" :aria-expanded="navigationOpen" aria-controls="owner-navigation" aria-label="Toggle administration navigation" @click="navigationOpen=!navigationOpen"><Icon :name="navigationOpen?'X':'Menu'"/></button></div>
  <div id="owner-navigation" class="owner-navigation" :class="{'is-open':navigationOpen}">
    <label class="owner-search"><Icon name="Search" :size="17"/><input v-model="navQuery" type="search" placeholder="Find a section" aria-label="Find an administration section"/></label>
    <nav class="owner-nav" aria-label="Platform sections"><section v-for="group in navigationGroups" :key="group.name"><h2>{{group.name}}</h2><button v-for="item in group.items" :key="item.name" :aria-current="tab===item.name?'page':undefined" :class="{selected:tab===item.name}" @click="selectTab(item.name)" :disabled="busy"><Icon :name="item.icon" :size="19"/><span>{{item.name}}</span></button></section></nav>
    <p v-if="!navigationGroups.length" class="owner-no-results">No matching sections. Try “billing” or “plans”.</p>
  </div>
  <footer class="owner-account">
    <div class="owner-account-person"><span class="owner-account-avatar" aria-hidden="true">{{operatorInitials}}</span><div><strong>{{operatorName}}</strong><span>{{({Primary:'Primary owner',Administrator:'Administrator',Admin:'Admin'})[ownerAccess?.my_level]||'Platform administrator'}}</span></div></div>
    <div class="owner-account-actions"><button type="button" :class="{selected:tab==='Profile'}" :aria-current="tab==='Profile'?'page':undefined" @click="selectTab('Profile')"><Icon name="UserRound" :size="17"/>Profile</button><button type="button" :disabled="signingOut" @click="signOut"><Icon name="LogOut" :size="17"/>{{signingOut?'Signing out…':'Sign out'}}</button></div>
  </footer>
</aside>
<main id="owner-content" class="release owner-web" tabindex="-1">
  <header class="owner-page-header"><div><p class="owner-breadcrumb">SISU / Administration</p><h1 id="owner-page-title" tabindex="-1">{{currentSection.name}}</h1><p class="owner-description">{{currentSection.description}}</p></div></header>
  <ActionNotice :message="error || note" :failure="!!error"/>
  <div class="owner-status" v-if="busy" role="status">Loading administration…</div><p v-if="error" role="alert" class="error">{{error}}</p><p v-if="note" role="status">{{note}}</p><button v-if="!data&&!busy" class="button subtle" @click="run(load)">Retry loading administration</button>
<section v-if="tab==='Platform guide'" class="panel"><h2>Your Platform owner guide</h2><ul><li><strong>Organizations:</strong> register and manage institutes that need their own hosted website. Institutes using the shared campus register there.</li><li><strong>Plans:</strong> publish prices, card text and included tools for Individual, Silver, Gold and Platinum.</li><li><strong>Site policies:</strong> check whether a separately hosted website received its settings. Waiting for delivery means it has not confirmed them yet.</li><li><strong>Provisioning:</strong> track the hosting operator’s work setting up those websites.</li><li><strong>Billing:</strong> view current campus provider accounts and invoices. Payment confirmation remains in the verified payment workflow.</li><li><strong>Commerce:</strong> read reports received from separately hosted websites. This is not a total of student bank transfers.</li><li><strong>Admin access:</strong> Administrators create admins by invitation (24-hour, single-use link) and decide who gets full authority. Admins do not see this section.</li><li><strong>Audit log:</strong> review saved administrative changes.</li><li><strong>Readiness:</strong> check local service health and outgoing email queue status.</li></ul><p>Plans can be edited here, but a paid subscription is activated only after payment verification. A queued email is not proof of inbox delivery.</p></section><OwnerOverview :can-manage="!!ownerAccess?.can_manage" v-if="tab==='Overview'" @navigate="selectTab"/><OwnerPeople v-else-if="tab==='People & connections'&&ownerAccess?.can_manage"/><OwnerAccess v-else-if="tab==='Admin access'&&ownerAccess?.can_manage"/><OwnerProfile v-else-if="tab==='Profile'" :profile="operator"/><FinanceOperations v-else-if="tab==='Commerce'" control/><OwnerBilling v-else-if="tab==='Billing'"/><StudentCountAdmin v-else-if="tab==='Student-count payments'&&ownerAccess?.can_manage"/>
<template v-else-if="data && !['Platform guide','Audit log'].includes(tab)"><button class="button subtle" :disabled="busy" @click="run(load)">Refresh</button>
<template v-if="tab==='Organizations'"><p>{{data.counts.registered}} registered · {{data.counts.enabled}} enabled · {{data.counts.disabled}} disabled</p><form class="panel" @submit.prevent="action('register',form)"><h2>Register a separately hosted institute</h2><p>This creates an organization record and a setup job. It does not create a public-campus institute or make its website available. Server setup is a separate step.</p><div class="grid"><label>Name<input v-model="form.title" required maxlength="120"></label><label>Institute code<input v-model="form.code" required minlength="2" maxlength="12" pattern="[A-Za-z][A-Za-z0-9]{1,11}" title="Use 2–12 letters or numbers, starting with a letter" placeholder="ABCS"><small>Start with a letter, then letters or numbers. For example: ABCS or A1234.</small></label><label>Dedicated website address<input v-model="form.site_hostname" required placeholder="academy.sisuacademylk.com"><small>Domain name only, without https:// or a path. You must control this domain.</small></label><label>Billing/admin email<input type="email" v-model="form.admin_contact" required></label><label>Subscription plan<select v-model="form.plan" required><option v-for="p in commercialPlanNames" :key="p" :value="p">{{p}} - LKR {{Number(commercialCatalog[p]?.monthly_lkr||0).toLocaleString()}}/month</option></select></label></div><button class="button primary" :disabled="busy||!commercialCatalog||!commercialPlanNames.includes(form.plan)">Create institute setup request</button></form>
<div class="scroll"><table><thead><tr><th>Organization</th><th>Host / code</th><th>Subscription</th><th>Provisioning</th><th>Manage</th></tr></thead><tbody><tr v-for="o in data.organizations" :key="o.name"><td>{{o.title}}<small>{{o.name}} · {{o.admin_contact}}</small></td><td>{{o.site_hostname}} · {{o.institute_code}}<p>{{o.custom_domain||'No custom domain'}}</p></td><td>{{o.plan}} · {{statusLabel(o.subscription?.state)}}<p>Ends {{o.subscription?.ends_at||'—'}}</p></td><td>{{statusLabel(o.provisioning_state)}} · {{o.enabled?'Enabled':'Suspended'}}</td><td><button class="button subtle" :disabled="busy" @click="choose(o)">Manage</button></td></tr></tbody></table></div><button v-if="page||data.organizations.length>=50" class="button subtle" :disabled="busy||!page" @click="page--;run(load)">Previous organizations</button><button v-if="page||data.organizations.length>=50" class="button subtle" :disabled="busy||data.organizations.length<50" @click="page++;run(load)">Next organizations</button><p v-if="!data.organizations.length">No organizations registered.</p>
<article v-if="tenant" id="organization-management" class="panel organization-management"><header class="manage-heading"><div><span class="eyebrow">MANAGE INSTITUTE</span><h2>{{selectedOrganization?.title||'Institute details'}}</h2><p>{{selectedOrganization?.site_hostname}} · {{selectedOrganization?.institute_code}}</p></div><button class="button subtle" :disabled="busy" @click="tenant='';manifest=null">Close details</button></header><div class="organization-summary"><div><small>Account</small><strong>{{selectedOrganization?.enabled?'Enabled':'Suspended'}}</strong></div><div><small>Subscription</small><strong>{{statusLabel(selectedOrganization?.subscription?.state)}}</strong></div><div><small>Website setup</small><strong>{{statusLabel(selectedOrganization?.provisioning_state)}}</strong></div></div><label class="action-reason">Reason for changes<input v-model="reason" maxlength="1000" placeholder="Briefly explain the change you are making"><small>Required for changes below. This note is saved in the activity history.</small></label><p v-if="error" class="error" role="alert">{{error}}</p><p v-if="note" role="status">{{note}}</p>
<section class="manage-section">
<h3>Commercial subscription plan</h3>
<p>Choose the published SISU package for this organization. This saves plan selection only; payment and access remain subject to separate verification.</p>
<p>Current selection: <strong>{{selectedOrganization?.plan==='STARTER'?'Legacy plan - not migrated':selectedOrganization?.plan}}</strong></p>
<label>Choose plan
<select v-model="selectedCommercialPlan">
<option disabled value="">Select a commercial plan</option>
<option v-for="p in commercialPlanNames" :key="p" :value="p">{{p}} - LKR {{Number(commercialCatalog[p]?.monthly_lkr||0).toLocaleString()}}/month</option>
</select>
</label>
<button class="button primary" type="button"
 :disabled="busy||!commercialCatalog||!commercialPlanNames.includes(selectedCommercialPlan)||reason.trim().length<10||selectedCommercialPlan===selectedOrganization?.plan"
 @click="saveCommercialPlan">Save commercial plan</button>
</section>
<section class="manage-section"><h3>Website & account access</h3><p>Save a custom domain or manage access to this institute. Domain setup and policy updates still need to be applied by the hosting operator.</p><label>Custom website domain<input v-model="domain" placeholder="learn.yourinstitute.com"><small>Optional. Enter the domain only, without https://.</small></label><div class="manage-actions"><button class="button primary" :disabled="busy||!reason.trim()" @click="action('update_organization',{tenant,enabled:!!selectedOrganization?.enabled,custom_domain:domain,reason})">Save domain</button><button v-if="!selectedOrganization?.enabled" class="button subtle" :disabled="busy||!reason.trim()" @click="action('update_organization',{tenant,enabled:true,reason})">Enable institute</button><button v-else class="button subtle" :disabled="busy||!reason.trim()" @click="action('update_organization',{tenant,enabled:false,reason})">Suspend institute</button></div><p>Billing contact: <strong>{{selectedOrganization?.admin_contact}}</strong></p><button class="button subtle" :disabled="busy" @click="action('invite_billing_contact',{tenant})">Send billing sign-in email</button></section>
<section class="manage-section"><h3>Subscription & trial</h3><p>Choose a status change, restore an eligible paid subscription, or grant a one-time trial. Paid activation still requires a verified payment.</p><label>Change subscription status<select v-model="state"><option disabled value="">Choose a new status</option><option v-for="s in ['grace','past_due','suspended','cancelled','expired']" :value="s">{{statusLabel(s)}}</option></select></label><label v-if="state==='grace'">Grace period ends<input v-model="grace" type="datetime-local"></label><div class="manage-actions"><button class="button primary" :disabled="busy||!reason.trim()||!state||(state==='grace'&&!grace)" @click="action('subscription_state',{tenant,state,reason,grace_until:grace||null})">Save status</button><button class="button subtle" :disabled="busy||!reason.trim()" @click="action('reactivate',{tenant,reason})">Restore paid subscription</button></div><label>Trial length (days)<input type="number" min="1" max="30" v-model.number="days"></label><small>1–30 days. The system checks whether this institute is eligible.</small><button class="button subtle" :disabled="busy||!reason.trim()||days<1||days>30" @click="action('trial',{tenant,days,reason})">Grant trial</button></section>
<section class="manage-section" v-if="commercial"><h3>Hosted-site monthly offer</h3><p>This is a separate hosted-site contract. Current Individual, Silver, Gold and Platinum packages are managed in Plans.</p><p>{{commercial.offer.available?'A monthly offer is configured for this institute.':commercial.offer.message}}</p><form @submit.prevent="saveOffer"><label>Monthly price (LKR)<input type="number" min="0.01" step="0.01" v-model.number="monthlyLkr" required></label><label class="check"><input type="checkbox" v-model="priceEnabled"> Make this offer available</label><button class="button primary" :disabled="busy||reason.trim().length<3">Save monthly offer</button></form><p>Saving an offer does not charge the institute or activate a subscription.</p><h4>Payment receipts</h4><p v-if="!commercial.receipts.length">No completed payments yet.</p><p v-for="receipt in commercial.receipts" :key="receipt.name">{{receipt.currency}} {{(receipt.amount_minor/100).toFixed(2)}} · {{receipt.paid_at}}<small>Receipt {{receipt.name}}</small></p></section>

<section v-if="ownerAccess?.can_manage" class="manage-section removal-section">
 <h3>Remove institute</h3>
 <p>Review institute removal, financial dependencies and hosting requirements. Shared accounts and financial history must be preserved.</p>

 <button type="button" class="button removal-button"
  :disabled="busy||!selectedOrganization"
  @click="reviewRemoval">
  Review institute removal
 </button>

 <div v-if="removalOpen" class="removal-review">
  <template v-if="removalPreview">
   <h3>{{removalPreview.title}}</h3>
   <p><strong>Institute code:</strong> {{removalPreview.code}}</p>
   <p><strong>Website:</strong> {{removalPreview.hostname}}</p>
   <p><strong>Billing contact:</strong> {{removalPreview.admin_contact}}</p>

   <h4>Removal checks</h4>
   <p v-if="removalPreview.removal_status">
    <strong>Removal status:</strong> {{removalPreview.removal_status}} <span v-if="removalPreview.progress">· {{removalPreview.progress}}</span>
    <button type="button" class="button subtle" :disabled="busy" @click="refreshRemoval">Refresh removal status</button>
   </p>
   <p>Pending payments: {{removalPreview.pending_payments}}</p>
   <p>Financial records to retain: {{removalPreview.financial_records}}</p>

   <div v-if="removalPreview.blockers.length" class="error">
    <strong>Removal requirements</strong>
    <ul>
     <li v-for="item in removalPreview.blockers" :key="item">{{item}}</li>
    </ul>
   </div>

   <p v-else>Control-plane preliminary checks passed.</p>
   <p>Website identity, dependencies and backups require hosting verification.</p>

   <label>Reason for removal
    <textarea v-model="removalReason" rows="3" maxlength="500"
     placeholder="Explain why this institute is being removed"/>
   </label>

   <label>Type {{removalPreview.code}} to confirm
    <input v-model="removalCode" autocomplete="off"/>
   </label>

   <div class="manage-actions">
    <button type="button" class="button removal-button"
    :disabled="busy||!removalPreview.removal_available||removalCode!==removalPreview.code||removalReason.trim().length<10"
    @click="submitRemoval">
     {{removalPreview.removal_status==='Failed'?'Retry removal':'Request institute removal'}}
    </button>
    <button type="button" class="button subtle" @click="resetRemoval">
     Cancel
    </button>
   </div>

   <small>Removal is completed only after hosting and backup verification.</small>
  </template>
  <p v-else>Review information is not available yet.</p>
 </div>
</section>
<details class="manage-section"><summary>Advanced settings & website updates</summary><p>These settings are for the hosting operator. Changes saved here must be delivered to the institute website before they take effect.</p><p>Institute reference: {{tenant}}</p><h4>Custom subscription settings</h4><p>Use features, limits and support_tier. Empty objects use the subscription defaults.</p><label>Settings JSON<textarea v-model="override" rows="8" spellcheck="false"/></label><button class="button subtle" :disabled="busy||!reason.trim()" @click="saveOverrides">Save custom settings</button><h4>Website policy update</h4><p>Delivery status: {{commercial?.policy_delivery?.status||'No delivery recorded'}} · revision {{commercial?.policy_delivery?.revision||'—'}}</p><p>A signing key must be configured by the operator. Downloading an update does not apply it to the website.</p><div class="manage-actions"><button class="button subtle" :disabled="busy" @click="exportManifest">Prepare website policy update</button><button v-if="manifest" class="button subtle" @click="downloadManifest">Download signed update</button></div></details></article></template>
<template v-else-if="tab==='Plans'"><h2>Provider packages</h2><p>Individual, Silver, Gold and Platinum. Publish one shared catalogue for the main website and provider dashboards.</p><PlanEditor/></template><template v-else-if="tab==='Site policies'"><SitePolicies @plans="selectTab('Plans')" @manage="openHostedSite"/></template>
<template v-else-if="tab==='Provisioning'"><OwnerProvisioning :jobs="data.jobs" @updated="run(load)"/></template>
<template v-else-if="tab==='Readiness'"><button class="button primary" :disabled="busy" @click="run(async()=>health=await request('owner_operations','readiness',{},'GET'))">Check local readiness</button><section v-if="health" class="panel"><h2>{{health.ready?'Local checks passed':'Local checks need attention'}}</h2><p v-for="(ok,name) in health.checks" :key="name">{{ok?'Pass':'Needs attention'}} · {{({scheduled_worker_recent:'Recent background-worker heartbeat',database:'Database',cache:'Cache',https:'Secure HTTPS',site_identity:'Website identity',run1_schema:'Subscription data structure',run2_schema:'Learning data structure',run3_contract_schema:'Billing data structure'})[name]||name}}</p><p v-if="!health.checks.scheduled_worker_recent">No recent scheduled heartbeat was recorded. This may be a scheduler, queue or monitoring issue; it does not prove every worker is stopped. Check the server diagnosis before changing settings.</p><h3>Optional integrations on this owner website</h3><p>These checks apply only to the Platform owner website. Campus integrations are configured separately. A missing optional connection does not mean the whole LMS is broken.</p><p v-for="(ok,name) in health.provider_configured" :key="name">{{name}} · {{ok?'Configured; delivery still needs testing':'Not connected on this website'}}</p><h3>Outgoing email</h3><p>These are queue counts for this owner website. “Sent” means handed to the mail server, not confirmed in the recipient’s inbox.</p><p v-for="(count,status) in health.mail" :key="status">{{status}}: {{count}}</p><p v-if="health.mail?.Error">Some messages failed. The hosting operator should inspect Email Queue errors and sender configuration.</p><h3>Connected campus reports</h3><p>{{health.reporting_sites?.join(', ')||'Not connected'}}</p><p>{{health.payment_note}}</p><p>{{health.note}}</p></section><p>Provider configuration is not provider acceptance. Complete the staging checklist before release.</p></template></template><section v-if="tab==='Audit log'"><h2>Control-plane audit history</h2><button class="button subtle" :disabled="busy" @click="run(loadAudit)">Refresh audit history</button><article v-for="row in auditRows" :key="row.name" class="panel"><h3>{{row.action}}</h3><p>{{notificationTime(row.creation)}} · {{row.actor}} · {{row.reference}}</p><p>{{row.details}}</p></article><p v-if="!busy&&!auditRows.length">No audit entries on this page.</p><button v-if="auditPage||auditRows.length>=50" class="button subtle" :disabled="busy||!auditPage" @click="auditPage--;run(loadAudit)">Previous audit entries</button><button v-if="auditPage||auditRows.length>=50" class="button subtle" :disabled="busy||auditRows.length<50" @click="auditPage++;run(loadAudit)">Next audit entries</button></section></main></div></template>

<style scoped>.panel>.button{margin:8px 8px 8px 0}textarea{display:block;width:100%;max-width:100%;box-sizing:border-box}pre{overflow:auto;max-width:100%}.scroll{overflow:auto}label{display:block;margin:12px 0}input,select{max-width:100%;box-sizing:border-box}nav{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}nav .button{width:auto}nav button[aria-pressed="true"]{background:#54218a;color:white}.release{max-width:1200px;margin:auto;padding:32px 24px}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.grid label{display:flex;flex-direction:column;gap:8px}.grid input{width:100%;padding:12px}small{display:block;line-height:1.5;color:#645a75}.release>h1{margin-bottom:12px}@media(max-width:700px){.grid{grid-template-columns:1fr}} </style>

<style scoped>.organization-management{scroll-margin-top:20px;padding:28px}.manage-heading{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.manage-heading h2{margin:8px 0}.organization-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0;padding:20px;background:var(--surface-alt,#f7f5fc);border-radius:12px}.organization-summary strong{display:block;margin-top:8px}.action-reason{padding:18px;border:1px solid #ded7ed;border-radius:12px}.manage-section{padding:24px 0;border-top:1px solid #e8e2ef;margin-top:24px}.manage-section h3{font-size:19px;margin:0 0 12px}.manage-section p{line-height:1.7;color:var(--muted,#645a75)}.organization-management label{display:grid;gap:8px;max-width:640px}.organization-management input,.organization-management select,.organization-management textarea{width:100%;padding:12px;border:1px solid #ded7ed;border-radius:8px;font:inherit;background:var(--surface,#fff);color:inherit}.organization-management .check{display:flex;align-items:center}.check input{width:auto}.manage-actions{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}.manage-section summary{cursor:pointer;font-weight:700}.manage-section>button{margin-top:14px}@media(max-width:650px){.manage-heading{flex-direction:column}.organization-summary{grid-template-columns:1fr}.organization-management{padding:18px}}</style>
<style scoped>
.release{font:15px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink,#30243c)}.release h1{font-size:30px}.release :deep(h2){font-size:23px;line-height:1.35}.release :deep(h3){font-size:18px}.release :deep(.panel){border:1px solid #e3dceb;border-radius:14px;margin:18px 0;background:var(--surface,#fff)}.release :deep(.button){font:inherit;border:1px solid #ded4e9;border-radius:9px;padding:10px 15px;cursor:pointer;background:var(--surface-alt,#f4effa);color:var(--ink,#4e2479);line-height:1.4}.release :deep(.button.primary){background:#55258b;color:#fff}.release :deep(.button:disabled){opacity:.48;cursor:not-allowed}.release :deep(.button:focus-visible){outline:3px solid #a77acf;outline-offset:3px}.release :deep(input),.release :deep(select),.release :deep(textarea){font:inherit}.release :deep(table){width:100%;border-collapse:collapse}.release :deep(th),.release :deep(td){padding:12px;text-align:left;vertical-align:top}.release :deep(th){background:var(--surface-alt,#f7f4fb);font-size:13px}.release :deep(tr){border-bottom:1px solid #eee8f3}.release>nav button[aria-pressed="true"]{background:#55258b;color:white}.release :deep(.error){padding:14px;border:1px solid #efbdc4;border-radius:8px;color:#8b2537}.release>form.panel{padding:24px}@media(max-width:600px){.release{padding:20px 16px}.release h1{font-size:26px}.release :deep(.button){padding:10px 12px}}
</style>

<style scoped>.release > nav[aria-label="Platform sections"]{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:10px;align-items:stretch}.release > nav[aria-label="Platform sections"] > button{width:100%;min-width:0}.grid select{width:100%;padding:12px;box-sizing:border-box}</style>

<style scoped>
.owner-shell{--owner-purple:#592c91;--ink:#292334;--muted:#6c617b;--surface:#fff;--surface-alt:#f6f3fa;--line:#e6e0ed;display:grid;grid-template-columns:244px minmax(0,1fr);min-height:100dvh;background:#f8f7fa;color:var(--ink);font:14px/1.55 "Manrope Variable",system-ui,sans-serif}
.owner-shell *{box-sizing:border-box}.owner-shell ::selection{background:#e6d8f8;color:#352047}.owner-skip{position:fixed;top:8px;left:260px;z-index:900;padding:12px;background:white;transform:translateY(-160%)}.owner-skip:focus{transform:none}.owner-sidebar{position:sticky;top:0;height:100dvh;display:flex;flex-direction:column;background:#fff;border-right:1px solid var(--line);padding:28px 18px 18px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:#d0c6dc transparent}.owner-brand{padding:0 12px 24px;display:flex;flex-direction:column;align-items:flex-start;gap:8px}.owner-brand :deep(.sisu-original-logo){width:112px}.owner-brand>span{font-size:12px;color:var(--muted)}.owner-navigation{display:flex;flex-direction:column;flex:1}.owner-search{display:flex!important;flex-direction:row!important;align-items:center;gap:8px;margin:0 0 25px!important;padding:10px 11px;border:1px solid var(--line);border-radius:8px;color:var(--muted)}.owner-search:focus-within{outline:2px solid var(--owner-purple);outline-offset:2px}.owner-search input{width:100%;min-width:0;border:0;outline:0;font:inherit;font-size:13px;background:none;color:var(--ink)}.owner-search input::placeholder{color:var(--muted)}
.owner-nav{display:block;margin:0}.owner-nav section{margin:0 0 22px}.owner-nav h2{margin:0 12px 7px;font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.04em}.owner-nav button{border:0;background:none;width:100%;display:flex;align-items:center;gap:11px;min-height:44px;padding:11px 12px;margin:3px 0;text-align:left;font:inherit;font-size:13px;color:#51465f;border-radius:8px;cursor:pointer}.owner-nav button:hover{background:#f7f4fb}.owner-nav button.selected{background:#eee6f7;color:#4f247e;font-weight:700}.owner-nav button:focus-visible,.owner-sidebar a:focus-visible,.owner-menu:focus-visible{outline:2px solid var(--owner-purple);outline-offset:2px}.owner-nav button:disabled{opacity:.5;cursor:wait}.owner-no-results{font-size:13px;padding:0 10px;color:var(--muted)}
.owner-sidebar-footer{display:flex;align-items:center;gap:10px;margin-top:auto;padding:18px 4px 0;border-top:1px solid var(--line);color:var(--owner-purple)}.owner-sidebar-footer div{min-width:0;flex:1}.owner-sidebar-footer strong{display:block;font-size:11px;color:var(--ink)}.owner-sidebar-footer span{display:block;font-size:10px;overflow-wrap:anywhere;color:var(--muted);margin-top:4px}.owner-sidebar-footer a{color:var(--muted);padding:10px;display:flex}.owner-menu{display:none}
.owner-web.release{min-width:0;max-width:none;width:100%;margin:0;padding:36px 40px;font:inherit}.owner-page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;padding-bottom:26px;margin-bottom:8px;border-bottom:1px solid var(--line)}.owner-web .owner-breadcrumb{font-size:12px;color:var(--muted);margin:0 0 15px}.owner-web .owner-page-header h1{font-size:28px;line-height:1.25;letter-spacing:-.025em;font-weight:750;margin:0 0 10px;outline:none}.owner-web .owner-description{margin:0;color:var(--muted);font-size:14px;max-width:64ch;line-height:1.65}.owner-environment{display:flex;align-items:center;gap:7px;white-space:nowrap;padding:6px 10px;border-radius:6px;background:#eeebf4;color:#5d4874;font-size:11px}.owner-environment>span{width:6px;height:6px;background:#765498;border-radius:50%}.owner-status{padding:14px 0;color:var(--muted)}.owner-web :deep(.button){min-height:42px;font-size:13px;text-decoration:none}.owner-web :deep(input),.owner-web :deep(select),.owner-web :deep(textarea){min-height:44px}.owner-web :deep(input[type=checkbox]){min-height:0}.owner-web :deep(h2){font-size:20px;font-weight:700}.owner-web :deep(h3){font-size:16px}.owner-web :deep(.panel){border-color:var(--line);box-shadow:none}.owner-web :deep(.release){max-width:100%;padding:0}.owner-web :deep(td),.owner-web :deep(th){overflow-wrap:anywhere}.owner-web :deep(.scroll){max-width:100%;overflow:auto}
@media(min-width:1600px){.owner-web.release{padding:42px 64px}}
@media(max-width:1100px){.owner-shell{grid-template-columns:218px minmax(0,1fr)}.owner-web.release{padding:28px 24px}.owner-sidebar{padding:24px 12px 16px}.owner-page-header{flex-wrap:wrap}.owner-environment{margin-left:auto}}
@media(max-width:760px){.owner-shell{display:block}.owner-sidebar{position:static;height:auto;padding:16px;border-right:0;border-bottom:1px solid var(--line);overflow:visible}.owner-brand{flex-direction:row;align-items:center;padding:0;gap:14px}.owner-brand :deep(.sisu-original-logo){width:96px}.owner-brand>span{font-size:11px}.owner-menu{display:flex;align-items:center;justify-content:center;width:44px;height:44px;margin-left:auto;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--owner-purple);cursor:pointer}.owner-navigation{display:none}.owner-navigation.is-open{display:flex;padding-top:22px}.owner-nav section{margin-bottom:14px}.owner-web.release{padding:24px 16px}.owner-page-header{gap:12px;padding-bottom:20px}.owner-web .owner-page-header h1{font-size:25px}.owner-environment{margin-left:0}.owner-sidebar-footer{margin-top:12px}.owner-skip{left:16px}.owner-web :deep(table){font-size:12px}}
</style>

<style scoped>
.owner-sidebar{overflow:hidden}.owner-brand{flex-shrink:0}.owner-navigation{min-height:0;overflow-y:auto;flex:1;padding-right:4px;scrollbar-width:thin;scrollbar-color:#d0c6dc transparent}.owner-account{flex-shrink:0;border-top:1px solid var(--line);padding-top:16px;margin-top:12px;background:#fff}.owner-account-person{display:flex;align-items:center;gap:10px;padding:0 4px 14px}.owner-account-person>div{min-width:0}.owner-account-person strong{display:block;font-size:13px;line-height:1.45;overflow-wrap:anywhere}.owner-account-person>div>span{display:block;font-size:11px;color:var(--muted);margin-top:3px}.owner-account-avatar{width:36px;height:36px;border-radius:9px;display:grid;place-items:center;background:#eee6f7;color:#54258a;font-size:12px;font-weight:700;flex-shrink:0}.owner-account-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.owner-account-actions button{display:flex;align-items:center;justify-content:center;gap:6px;border:1px solid var(--line);background:#fff;border-radius:8px;min-height:42px;padding:8px 4px;font:inherit;font-size:12px;color:#51465f;cursor:pointer}.owner-account-actions button:hover,.owner-account-actions button.selected{background:#eee6f7;color:#54258a}.owner-account-actions button:focus-visible{outline:2px solid #592c91;outline-offset:2px}.owner-account-actions button:disabled{opacity:.6;cursor:wait}@media(max-width:760px){.owner-sidebar{overflow:visible}.owner-navigation{overflow:visible}.owner-account{display:flex;align-items:center;justify-content:space-between;gap:16px}.owner-account-person{padding:0;flex:1;min-width:0}.owner-account-actions{flex-shrink:0}.owner-account-actions button{padding:9px}.owner-account-avatar{display:none}}@media(max-width:380px){.owner-account{align-items:flex-start;flex-direction:column;gap:12px}.owner-account-actions{width:100%}}
</style>


<style scoped>
.removal-section h3{color:#8b2537}
.removal-section .removal-button{
 color:#8b2537;
 background:#fff;
 border:1px solid #d8a6ae;
}
.removal-section .removal-button:hover:not(:disabled){
 background:#fff3f5;
}
.removal-review{
 margin-top:18px;
 padding:20px;
 background:var(--surface-alt,#f6f3fa);
 border:1px solid var(--line,#e6e0ed);
 border-radius:12px;
 overflow-wrap:anywhere;
}
</style>
