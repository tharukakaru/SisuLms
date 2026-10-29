<script setup>

import {ref,watch,onMounted,computed} from 'vue'

import {request} from './client'

import {hostedCheckout,requestIdentity} from './contracts'

import LiveRoom from './LiveRoom.vue'

import FinanceOperations from './FinanceOperations.vue'

import {receiptHtml,downloadHtml} from './receipt'

import './release.css'

const props=defineProps({section:String,member:Object,rooms:Array,classroom:String,sessions:{type:Array,default:()=>[]},view:String,embedded:Boolean})

const rows=ref([]),data=ref(null),error=ref(''),busy=ref(false),notice=ref(''),grant=ref(null),video=ref(null),job=ref(null),paper=ref(null),sources=ref([])

const form=ref({classroom:props.classroom||'',title:'',description:'',includes:'',media_key:'',price_minor:0,status:'Draft',access_days:0}),topic=ref('Create a course revision paper'),count=ref(10),duration=ref(120),document=ref(''),mode=ref('Individual'),allocations=ref({}),reason=ref(''),session=ref('')

const search=ref(''),filterRole=ref(''),creditPage=ref(0),blueprint=ref([{kind:'MCQ',count:10,marks:1}]),templateHeading=ref(''),templateInstructions=ref('')

let generationIdentity=null

const visibleRows=computed(()=>rows.value.filter(r=>(!props.classroom||r.classroom===props.classroom)&&(props.section!=='liveclasses'||!props.embedded||(props.view==='recordings'?r.recording_status!=='None':(r.status!=='Ended'||r.can_control)))))
const titles={lessons:'Lesson Store',library:'Lecture Library',purchases:'My Purchases',liveclasses:'Live Classes',papergen:'Paper Generator',credits:'AI Credit Management',aiusage:'AI Usage',storage:'Usage & Storage'}

async function run(fn){busy.value=true;error.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}

async function load(){rows.value=[];data.value=null;grant.value=null;await run(async()=>{if(['lessons','library','purchases'].includes(props.section)){rows.value=await request('lectures','listing',{library:props.section==='library',purchases:props.section==='purchases',classroom:props.classroom||undefined});if(props.section==='purchases')data.value=await request('lectures','history',{classroom:props.classroom||undefined},'GET')}else if(props.section==='liveclasses')rows.value=await request('live_classes','listing',{classroom:props.classroom||undefined},'GET');else if(props.section==='credits'){data.value=await request('ai_credits','management',{search:search.value,role:filterRole.value,page:creditPage.value},'GET');mode.value=data.value.mode;allocations.value=Object.fromEntries(data.value.users.map(u=>[u.user,u.allocated]))}else if(props.section==='aiusage')data.value=await request('ai_credits','status',{},'GET');else if(props.section==='storage')data.value=await request('release','workspace',{},'GET')})}

async function chooseSources(){await run(async()=>sources.value=await request('release','learning_sources',{classroom:form.value.classroom}))}

async function purchase(row){await run(async()=>{const r=await request('lectures','checkout',{product:row.name});if(r.preview){notice.value=r.message;await load()}else if(r.owned){notice.value='Already purchased';await load()}else location.assign(hostedCheckout(r.redirect_url))})}

async function play(row){await run(async()=>{const r=await request('lectures','playback',{product:row.name});if(r.preview)notice.value=r.message;else video.value=r})}

async function recording(row){await run(async()=>{const r=await request('live_classes','recording',{name:row.name});if(r.preview)notice.value='PREVIEW ONLY — no media request';else video.value=r})}

async function saveLesson(){await run(async()=>{await request('lectures','save',{data:form.value});notice.value='Lesson saved';await load()})}

async function uploadMedia(event){const file=event.target.files?.[0];if(!file)return;await run(async()=>{

 if(!form.value.classroom)throw Error('Choose a classroom first');

 const grant=await request('private_media','begin',{classroom:form.value.classroom,size:file.size,content_type:file.type});

 if(grant.preview){notice.value='PREVIEW ONLY — fictional upload ready. No file was uploaded.';form.value.media_key='preview-private-object';return}

 const url=new URL(grant.upload.url);if(url.protocol!=='https:'||url.username||url.password)throw Error('Invalid private upload destination');

 let body=file;const method=grant.upload.method==='PUT'?'PUT':'POST';
 if(method==='POST'){body=new FormData();for(const [key,value] of Object.entries(grant.upload.fields))body.append(key,value);body.append('file',file)}

 const response=await fetch(url.href,{method,body,headers:grant.upload.headers||{},credentials:'omit'});if(!response.ok)throw Error('Upload failed. Reserved storage needs reconciliation before retry.');

 const result=await request('private_media','complete',{name:grant.object});form.value.media_key=result.media_key;notice.value='Private upload verified. Review and save the lesson.';

})}

async function saveCredits(){await run(async()=>data.value=await request('ai_credits','configure',{mode:mode.value,allocations:allocations.value,reason:reason.value}))}

async function generate(){await run(async()=>{const payload={classroom:form.value.classroom,document:document.value,topic:topic.value,count:blueprint.value.reduce((n,q)=>n+Number(q.count),0),blueprint:blueprint.value,template_metadata:{heading:templateHeading.value,instructions:templateInstructions.value,show_marks:true},duration_minutes:duration.value};generationIdentity=requestIdentity(generationIdentity,payload);job.value=await request('paper_generator','create',{...payload,request_id:generationIdentity.id});notice.value='Draft generation queued. No paper is published.'})}

async function jobStatus(){await run(async()=>{job.value=await request('paper_generator','status',{name:job.value.name});if(job.value.paper)paper.value=await request('papers','detail',{name:job.value.paper})})}

async function publish(){await run(async()=>{if(!window.confirm('Have you reviewed every question and the answer key?'))return;await request('papers','draft',{data:paper.value});await request('papers','publish',{name:job.value.paper,reviewed:true});notice.value='Paper published after explicit review';await jobStatus()})}

async function exportPaper(){await run(async()=>{const r=await request('paper_generator','export',{paper:job.value.paper});const url=URL.createObjectURL(new Blob([JSON.stringify(r,null,2)],{type:'application/json'}));const a=Object.assign(documentGlobal.createElement('a'),{href:url,download:'teacher-paper.json'});a.click();URL.revokeObjectURL(url)})}

const documentGlobal=globalThis.document

onMounted(load);watch(()=>[props.section,props.classroom,props.view],load)

</script>

<template><section class="release"><h2 v-if="embedded">{{section==='liveclasses'?(view==='recordings'?'Recorded SISU sessions':'Live inside SISU'):'Recorded lessons'}}</h2><h1 v-else>{{titles[section]}}</h1><p v-if="busy" role="status">Loading…</p><p v-if="error" role="alert" class="error">{{error}}</p><p v-if="notice" role="status">{{notice}}</p><button class="button subtle" @click="load" :disabled="busy">Refresh</button>

<LiveRoom v-if="grant" :grant="grant" @leave="grant=null"/><video v-if="video" :src="video.url" controls playsinline style="max-width:100%"/>

<form v-if="section==='library'" class="panel" @submit.prevent="saveLesson"><h2>{{form.name?'Edit lecture':'Create lecture draft'}}</h2><label>Classroom<select v-model="form.classroom" required><option value="">Choose classroom</option><option v-for="r in rooms" :value="r.name">{{r.title}}</option></select></label><label>Title<input v-model="form.title" required maxlength="120"></label><label>Description<textarea v-model="form.description"/></label><label>What you will learn<textarea v-model="form.includes"/></label><label>Upload private video<input type="file" accept="video/mp4,video/webm" @change="uploadMedia" :disabled="busy||!form.classroom"></label><label>Private media reference<input v-model="form.media_key" required><small>Use the protected upload/storage workflow configured by your institute. Public video URLs cannot be sold.</small></label><label>Price (LKR minor units; zero is free)<input type="number" min="0" v-model.number="form.price_minor"></label><label>Access days (zero: no expiry)<input type="number" min="0" v-model.number="form.access_days"></label><label>Publication<select v-model="form.status"><option>Draft</option><option>Published</option><option>Unlisted</option><option>Archived</option></select></label><button class="button primary" :disabled="busy">Save lecture</button><p>Sold media is preserved. Archive to stop new sales without removing existing access.</p></form>

<div class="product-grid"><article v-for="row in visibleRows" :key="row.name" class="panel"><span class="badge">{{row.status}} {{row.recording_status? '· Recording '+row.recording_status:''}}</span><h2>{{row.title}}</h2><p>{{row.description}}</p><p v-if="row.teacher">{{row.teacher}} · {{row.classroom}}</p><template v-if="['lessons','library','purchases'].includes(section)"><p>{{row.price_minor?`${row.currency} ${(row.price_minor/100).toFixed(2)}`:'Free'}} · {{row.owned?'Purchased':row.locked?'Locked':'Available'}}</p><button v-if="section!=='library'&&!row.locked" class="button primary" @click="play(row)">Open lesson</button><button v-if="section!=='library'&&row.locked" class="button primary" @click="purchase(row)">Purchase lesson</button><button v-if="section==='library'" class="button subtle" @click="run(async()=>form=await request('lectures','detail',{name:row.name}))">Edit / archive</button></template><template v-else-if="section==='liveclasses'"><p>{{row.starts_at}}</p><p v-if="row.status==='Ended'&&row.can_control">This live lesson has ended. Create a new classroom session, then schedule it here to teach again.</p><button v-if="row.recording_status==='Ready'" class="button primary" @click="recording(row)">Watch recording</button><button v-if="row.can_control&&['Processing','Failed'].includes(row.recording_status)" class="button subtle" @click="run(async()=>{await request('live_classes','reconcile',{name:row.name});await load()})">Reconcile recording</button><button v-if="row.can_control&&row.recording_status==='Failed'" class="button subtle" @click="run(async()=>{const reason=prompt('Remove failed recording objects permanently? Enter an audit reason (10+ characters).');if(!reason)return;await request('live_classes','cleanup_failed',{name:row.name,reason});await load()})">Remove failed recording</button><button v-if="row.can_control&&row.recording_status==='Ready'&&!row.recording_published" class="button subtle" @click="run(async()=>{if(!confirm('Reviewed this recording for classroom publication?'))return;await request('live_classes','publish_recording',{name:row.name,reviewed:true});await load()})">Reviewed — publish recording</button><button v-if="row.recording_status==='Ready'&&row.can_control" class="button subtle" @click="run(async()=>{await request('live_classes','lecture_draft',{name:row.name});notice='Recording saved as a lecture draft. Review in Lecture Library.'})">Create lecture draft</button><button v-if="row.status==='Live'" class="button primary" @click="run(async()=>grant=await request('live_classes','join',{name:row.name}))">Join inside SISU</button><button v-if="row.can_control&&row.status==='Upcoming'" class="button primary" @click="run(async()=>{await request('live_classes','control',{name:row.name,action:'start'});await load()})">Start Live</button><button v-if="row.can_control&&row.status==='Live'" class="button subtle" @click="run(async()=>{await request('live_classes','control',{name:row.name,action:'end'});await load()})">End lesson</button></template></article></div><p v-if="!busy&&!error&&!visibleRows.length&&['lessons','library','purchases','liveclasses'].includes(section)">No items available in this view.</p>

<form v-if="section==='liveclasses'&&view!=='recordings'&&member.role==='Teacher'" class="panel" @submit.prevent="run(async()=>{await request('live_classes','schedule',{session});await load()})"><h2>Enable a scheduled classroom session for live teaching</h2><label>{{classroom?'Class session':'Existing session reference'}}<select v-if="classroom" v-model="session" required><option disabled value="">Choose a scheduled session</option><option v-for="s in sessions.filter(s=>s.classroom===classroom&&s.mode==='Online'&&s.status!=='Cancelled'&&s.status!=='Completed'&&!rows.some(r=>r.session===s.name))" :key="s.name" :value="s.name">{{s.title}} · {{s.starts_at}}</option></select><input v-else v-model="session" required></label><button class="button primary">Schedule Live</button></form>

<template v-if="section==='credits'&&data"><article class="panel"><h2>Monthly organization pool</h2><p>{{data.organization_used}} used · {{data.organization_remaining}} remaining of {{data.organization_limit}} · resets {{data.reset_at}}</p><p>{{data.total_allocated}} allocated · {{data.unallocated}} unallocated</p><label>Search members<input v-model="search" @change="creditPage=0;load()"></label><label>Role<select v-model="filterRole" @change="creditPage=0;load()"><option value="">All</option><option>Student</option><option>Teacher</option><option>Admin</option></select></label><label>Credit mode<select v-model="mode"><option value="Individual">Individual Allocation</option><option value="Shared">Shared Pool</option></select></label><p>Shared mode retains saved allocations but pauses individual limits. History is preserved. Unallocated Individual credits stay unused.</p><div class="scroll"><table><thead><tr><th>User</th><th>Role</th><th>Allocated</th><th>Used</th><th>Remaining</th></tr></thead><tbody><tr v-for="u in data.users"><td>{{u.full_name}}</td><td>{{u.role}}</td><td><input :aria-label="'Credits for '+u.full_name" type="number" min="0" v-model.number="allocations[u.user]"></td><td>{{u.used}}</td><td>{{u.remaining}}</td></tr></tbody></table></div><button class="button subtle" :disabled="creditPage===0" @click="creditPage--;load()">Previous</button><button class="button subtle" :disabled="!data.has_more" @click="creditPage++;load()">Next</button><details><summary>Allocation history</summary><p v-for="h in data.history">{{h.creation}} · {{h.action}} · {{h.details}}</p></details><label>Reason<input v-model="reason" required minlength="3"></label><button class="button primary" @click="saveCredits" :disabled="busy||reason.length<3">Save allocation policy</button></article></template>

<article v-if="section==='aiusage'&&data" class="panel"><h2>Your AI usage</h2><p>{{data.mode==='Individual'?'Individual Allocation':'Shared Pool'}} · {{data.used}} credits used</p><p v-if="data.mode==='Individual'">{{data.allocated}} allocated · {{data.remaining}} remaining</p><p v-else>Shared institute pool: {{data.organization_remaining}} remaining of {{data.organization_limit}}. Other users’ activity is private.</p><p>Resets {{data.reset_at}}</p><p v-if="data.organization_remaining===0||data.mode==='Individual'&&data.remaining===0" role="status">AI credits exhausted or not allocated. Contact your Institute Admin.</p></article>

<article v-if="section==='storage'&&data" class="panel"><h2>Storage</h2><p>{{(data.storage.used/1048576).toFixed(1)}} MB used / {{(data.storage.limit/1048576).toFixed(1)}} MB allowed</p><p>Storage service: {{data.storage_backend}}. Uploads remain server-authorized.</p></article>

<template v-if="section==='papergen'"><form class="panel" @submit.prevent="generate"><h2>Generate a draft from authorized material</h2><label>Classroom<select v-model="form.classroom" @change="chooseSources" required><option value="">Select</option><option v-for="r in rooms" :value="r.name">{{r.title}}</option></select></label><label>Source<select v-model="document" required><option value="">Select indexed source</option><option v-for="s in sources" :value="s.name">{{s.title}} · v{{s.version}}</option></select></label><label>Instructions<textarea v-model="topic" required/></label><fieldset><legend>Question blueprint (1–100 total)</legend><div v-for="(q,i) in blueprint"><label>Type<select v-model="q.kind"><option>MCQ</option><option>True/False</option><option>Written</option></select></label><label>Count<input type="number" min="1" max="100" v-model.number="q.count"></label><label>Marks each<input type="number" min="1" max="100" v-model.number="q.marks"></label><button v-if="blueprint.length>1" type="button" @click="blueprint.splice(i,1)">Remove group</button></div><button type="button" :disabled="blueprint.length>=3" @click="blueprint.push({kind:blueprint.length===1?'True/False':'Written',count:5,marks:1})">Add question type</button></fieldset><label>Print heading<input v-model="templateHeading" maxlength="1000"></label><label>Print instructions<textarea v-model="templateInstructions" maxlength="1000"/></label><label>Minutes<input type="number" min="1" max="360" v-model.number="duration"></label><p>Up to 20 per batch. Larger papers run in the background. Approved text transcripts are supported; automatic video transcription is unavailable.</p><button class="button primary" :disabled="busy">Generate draft</button></form><article v-if="job" class="panel"><h2>{{job.status}}</h2><p>{{job.progress||0}} / {{job.count||count}} questions · {{job.error_code}}</p><button v-if="job.status==='Review'" class="button subtle" @click="run(async()=>{await request('paper_generator','resume',{name:job.name});await jobStatus()})">Resume saved batches</button><button class="button subtle" @click="jobStatus">Refresh generation</button><template v-if="paper"><h3>{{paper.title}} · {{paper.status}}</h3><article v-for="q in paper.questions||[]"><label>Prompt<textarea v-model="q.prompt" :disabled="paper.status!=='Draft'"/></label><label>Marks<input type="number" min="1" v-model.number="q.marks" :disabled="paper.status!=='Draft'"></label><ol><li v-for="(option,i) in q.options"><input v-model="q.options[i]" :disabled="paper.status!=='Draft'||q.kind==='True/False'" aria-label="Answer option"></li></ol><label v-if="q.kind!=='Written'">Correct option (zero-based)<input type="number" min="0" :max="q.options.length-1" v-model.number="q.answer" :disabled="paper.status!=='Draft'"></label></article><button class="button subtle" :disabled="paper.status!=='Draft'" @click="run(async()=>{await request('papers','draft',{data:paper});notice='Draft saved'})">Save draft edits</button><button class="button subtle" @click="run(async()=>{const r=await request('paper_generator','printable',{paper:job.paper});downloadHtml(r.html,'paper.html')})">Download printable paper</button><button class="button subtle" @click="run(async()=>{await request('papers','archive',{name:job.paper});await jobStatus()})">Archive</button><button class="button primary" @click="publish" :disabled="paper.status!=='Draft'">Reviewed — publish</button><button class="button subtle" @click="exportPaper">Export teacher draft/answer key</button></template></article></template>

<article v-if="section==='purchases'&&data" class="panel"><h2>Purchase history & receipts</h2><p v-for="r in data">{{r.receipt_number||'Awaiting verified receipt'}} · {{r.status}} · {{r.currency}} {{(r.amount_minor/100).toFixed(2)}} <button v-if="['succeeded','refunded'].includes(r.status)" class="button subtle" @click="run(async()=>{const receipt=await request('lectures','receipt',{name:r.name});downloadHtml(receiptHtml(receipt),'lesson-receipt.html')})">Download receipt</button></p></article>

<FinanceOperations v-if="section==='storage'&&member.role==='Admin'"/></section></template>

<style scoped>.product-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:16px;margin-top:20px}.release input,.release select,.release textarea{max-width:100%}.release table input{width:90px}</style>

