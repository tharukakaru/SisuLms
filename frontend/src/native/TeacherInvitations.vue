<script setup>
import {ref,computed,onMounted,onBeforeUnmount,nextTick,watch} from 'vue'
import {Mail,Building2,Check,ArrowRight,X,RefreshCw,Clock} from 'lucide-vue-next'
import {request} from './client'
const props=defineProps({active:Boolean,member:Object})
const emit=defineEmits(['changed'])
const rows=ref([]),loading=ref(false),busy=ref(''),error=ref(''),notice=ref(''),filter=ref('All'),selected=ref(null),dialog=ref(null)
const seen=new Set()
const pending=r=>r.status==='Pending'&&!r.expired
const label=r=>r.expired?'Expired':r.status==='Declined'?'Rejected':r.status==='Accepted'?(r.connected?'Connected':'Accepted · not connected'):r.status
const pendingCount=computed(()=>rows.value.filter(pending).length)
const filtered=computed(()=>rows.value.filter(r=>filter.value==='All'||(filter.value==='Pending'?pending(r):filter.value==='Connected'?r.connected:!pending(r)&&!r.connected)))
function date(value){if(!value)return '—';return new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(String(value).replace(' ','T')+'+05:30'))}
async function load(prompt=false){
 if(loading.value||busy.value)return
 loading.value=true;error.value=''
 try{rows.value=await request('invitations','list_invitations');if(prompt&&!selected.value){const invite=rows.value.find(r=>pending(r)&&!seen.has(r.name));if(invite)await review(invite)}}
 catch(e){error.value=e.message}finally{loading.value=false}
}
let restoreFocus,previousOverflow,timer
async function review(row){error.value='';selected.value=row;seen.add(row.name);restoreFocus=document.activeElement;previousOverflow=document.body.style.overflow;document.body.style.overflow='hidden';await nextTick();dialog.value?.showModal()}
function close(){if(busy.value)return;dialog.value?.close();selected.value=null;document.body.style.overflow=previousOverflow||'';restoreFocus?.focus?.()}
async function respond(decision){
 if(busy.value||!selected.value)return
 busy.value=decision;error.value=''
 try{const row=selected.value;await request('invitations','respond',{name:row.name,decision});notice.value=decision==='Accepted'?`You’re connected to ${row.institute_title}. Switch workspaces below or use the dropdown beside your profile.`:`Invitation from ${row.institute_title} rejected. The institute has been notified.`;busy.value='';close();await load();window.dispatchEvent(new Event('sisu-memberships'));emit('changed')}
 catch(e){error.value=e.message}finally{busy.value=''}
}
async function open(row){busy.value=row.name;error.value='';try{await request('campus_context','select',{institute:row.institute});location.assign('/campus')}catch(e){error.value=e.message;busy.value=''}}
function visible(){if(document.visibilityState==='visible')load(true)}
watch(()=>props.active,active=>{if(active)load()})
onMounted(()=>{load(true);timer=setInterval(()=>{if(document.visibilityState==='visible')load(true)},60000);document.addEventListener('visibilitychange',visible)})
onBeforeUnmount(()=>{clearInterval(timer);document.removeEventListener('visibilitychange',visible);if(selected.value)document.body.style.overflow=previousOverflow||''})
</script>

<template>
 <section v-if="active" class="teacher-invitations">
  <header class="invites-heading"><div><h1>Invitations <span>{{pendingCount}} pending</span></h1><p>Choose the institutes you want to teach with. Your personal workspace stays yours.</p></div><button class="invite-secondary" :disabled="loading||!!busy" @click="load()"><RefreshCw :size="16"/>Refresh</button></header>
  <p v-if="notice" class="invite-success" role="status"><Check :size="19"/>{{notice}}</p><p v-if="error&&!selected" class="invite-error" role="alert">{{error}}</p>
  <div class="invite-tabs" aria-label="Filter invitations"><button v-for="tab in ['All','Pending','Connected','History']" :key="tab" :aria-pressed="filter===tab" :class="{chosen:filter===tab}" @click="filter=tab">{{tab}}</button></div>
  <p v-if="loading&&!rows.length" role="status">Loading invitations…</p>
  <div v-else-if="!filtered.length" class="invite-empty"><Mail :size="32"/><h2>{{filter==='All'?'Your next connection starts here':'No '+filter.toLowerCase()+' invitations'}}</h2><p>Institutes can invite you using your SISU login email. Invitations will appear here.</p></div>
  <article v-for="row in filtered" :key="row.name" class="teacher-invite-row">
   <div class="invite-logo"><Building2 :size="25"/></div><div class="invite-detail"><span class="invite-status" :class="{connected:row.connected,pending:pending(row)}">{{label(row)}}</span><h2>{{row.institute_title}}</h2><p>Invited {{date(row.creation)}}</p><p v-if="pending(row)"><Clock :size="13"/> Respond by {{date(row.expires_at)}}</p><p v-else-if="row.responded_at">{{row.connected?'Connected':'Responded'}} {{date(row.responded_at)}}</p></div>
   <button v-if="pending(row)" class="invite-primary" :disabled="!!busy" @click="review(row)">Review invitation<ArrowRight :size="17"/></button><button v-else-if="row.connected" class="invite-secondary" :disabled="!!busy" @click="open(row)">Open workspace<ArrowRight :size="17"/></button>
  </article>
 </section>
 <Teleport to="body"><dialog ref="dialog" class="teacher-invite-dialog" aria-labelledby="teacher-invite-title" aria-describedby="teacher-invite-description" @cancel.prevent="close">
  <template v-if="selected"><button class="invite-close" aria-label="Close invitation" :disabled="!!busy" @click="close"><X :size="21"/></button><div class="invite-dialog-icon"><Mail :size="28"/></div><p>You’re invited to teach at</p><h2 id="teacher-invite-title">{{selected.institute_title}}</h2><p id="teacher-invite-description">Join this institute’s teaching team. Accept to connect its workspace to your SISU account.</p><div class="invite-dialog-info"><Building2 :size="21"/><div><strong>Your personal workspace stays separate</strong><p>The institute assigns your classes and manages its subscription. Your personal plan stays unchanged.</p></div></div><p class="invite-expiry"><Clock :size="15"/>Respond by {{date(selected.expires_at)}}</p><p v-if="error" class="invite-error" role="alert">{{error}}</p><div class="invite-dialog-actions"><button class="invite-secondary" :disabled="!!busy" @click="respond('Declined')">{{busy==='Declined'?'Rejecting…':'Reject invitation'}}</button><button class="invite-primary" :disabled="!!busy" @click="respond('Accepted')">{{busy==='Accepted'?'Connecting…':'Accept invitation'}}<Check :size="18"/></button></div><p class="invite-dialog-foot">The institute will be notified of your decision. You can close this popup and decide later in Invitations.</p></template>
 </dialog></Teleport>
</template>

<style>
.teacher-invitations{max-width:1120px;margin:0 auto;color:var(--student-ink,#292332)}.invites-heading{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:28px}.invite-eyebrow{display:block;font-size:11px;font-weight:700;letter-spacing:.09em;color:#795f99}.invites-heading h1{font-size:30px;margin:10px 0}.invites-heading h1 span{display:inline-block;font-size:12px;font-weight:600;background:#f0e9f8;color:#592c91;padding:7px 10px;border-radius:8px;vertical-align:middle}.invites-heading p,.teacher-invite-row p{color:#756b83;line-height:1.65;margin:6px 0;font-size:14px}.invite-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 20px}.invite-tabs button{padding:10px 17px;border:1px solid #e4dbee;background:white;color:#625071;border-radius:9px;cursor:pointer}.invite-tabs .chosen{background:#592c91;color:white;border-color:#592c91}.teacher-invite-row{display:flex;align-items:center;gap:20px;border:1px solid #e5dfee;border-radius:16px;padding:24px;margin-bottom:14px;background:white}.invite-logo,.invite-dialog-icon{display:grid;place-items:center;width:54px;height:54px;flex:none;border-radius:14px;background:#f2ecfa;color:#592c91}.invite-detail{flex:1;min-width:0}.invite-detail h2{font-size:19px;overflow-wrap:anywhere;margin:10px 0 7px}.invite-detail p{display:flex;gap:7px;align-items:center;font-size:12px}.invite-status{display:inline-block;font-size:11px;padding:5px 8px;border-radius:6px;background:#f4f2f6;color:#665b72}.invite-status.connected{background:#e8f5ee;color:#216b47}.invite-status.pending{background:#fff3db;color:#876022}.invite-primary,.invite-secondary{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:46px;padding:12px 18px;border-radius:10px;font:inherit;font-size:13px;font-weight:650;cursor:pointer;border:1px solid #dbcee9;background:white;color:#592c91}.invite-primary{background:#592c91;color:white;border-color:#592c91}.invite-primary:hover{background:#472276}.invite-secondary:hover{background:#f8f4fc}.invite-primary:disabled,.invite-secondary:disabled{opacity:.55;cursor:wait}.teacher-invitations button:focus-visible,.teacher-invite-dialog button:focus-visible{outline:3px solid #b591de;outline-offset:3px}.invite-success,.invite-error{display:flex;align-items:center;gap:10px;padding:15px;border-radius:10px;font-size:14px;line-height:1.7;background:#eaf6ef;color:#216b47}.invite-error{background:#fff0f2;color:#a12742}.invite-empty{text-align:center;padding:55px 22px;border:1px dashed #dacbe9;border-radius:16px;background:#fbf9fd;color:#78678b}.invite-empty h2{font-size:19px;color:#33253f;margin:14px 0}.invite-empty p{font-size:14px;line-height:1.7}.teacher-invite-dialog{position:fixed;inset:0;margin:auto;width:min(540px,calc(100vw - 32px));max-height:calc(100dvh - 40px);overflow:auto;padding:32px;border:0;border-radius:22px;background:white;color:#302738;box-shadow:0 24px 80px #21103133}.teacher-invite-dialog::backdrop{background:#21142b70;backdrop-filter:blur(4px)}.invite-close{position:absolute;top:18px;right:18px;width:38px;height:38px;display:grid;place-items:center;border:0;background:transparent;color:#77658a;border-radius:8px;cursor:pointer}.invite-dialog-icon{margin:0 0 22px}.teacher-invite-dialog h2{font-size:27px;line-height:1.3;margin:10px 0 14px;overflow-wrap:anywhere}.teacher-invite-dialog>p{font-size:14px;line-height:1.75;color:#74667f}.invite-dialog-info{display:flex;gap:14px;background:#f7f3fb;border-radius:12px;padding:18px;margin:24px 0;color:#6b4b8a}.invite-dialog-info svg{flex:none}.invite-dialog-info strong{font-size:13px;color:#3e2c50}.invite-dialog-info p{font-size:13px;line-height:1.7;margin:6px 0 0}.invite-expiry{display:flex;align-items:center;gap:8px}.invite-dialog-actions{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:26px}.teacher-invite-dialog .invite-dialog-foot{font-size:11px;line-height:1.8;margin:18px 0 0;text-align:center}.invite-close:hover{background:#f2ecfa}@media(max-width:600px){.invites-heading{align-items:flex-start}.invites-heading h1{font-size:25px}.teacher-invite-row{flex-wrap:wrap;padding:20px;gap:14px}.teacher-invite-row>button{width:100%}.teacher-invite-dialog{padding:26px 22px}.invite-dialog-actions{grid-template-columns:1fr}.invite-dialog-actions .invite-primary{grid-row:1}}
</style>
