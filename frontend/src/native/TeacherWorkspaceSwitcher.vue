<script setup>
import {ref,computed,watch,nextTick,onMounted,onBeforeUnmount} from 'vue'
import {UserRound,Building2,LockKeyhole,Plus,Check,CheckCircle2,Trash2,X,ChevronDown} from 'lucide-vue-next'
import {request} from './client'
const props=defineProps({data:Object,locked:Boolean,personalImage:String})
const emit=defineEmits(['join','changed'])
const busy=ref(''),error=ref(''),confirmCancel=ref(''),notice=ref(''),actionsFor=ref('')
const confirmDialog=ref(null),keepButton=ref(null),noticeDialog=ref(null),okButton=ref(null),joinButton=ref(null),cancelledInstitute=ref('')
const dropdown=ref(null),trigger=ref(null),menu=ref(null),expanded=ref(false),failedImages=ref({})
const current=computed(()=>props.data?.choices?.find(item=>item.institute===props.data.selected))
const logo=item=>!failedImages.value[item?.institute]&&(item?.image||(item?.kind==='Personal'?props.personalImage:''))
function closeMenu(restore=false){if(dropdown.value)dropdown.value.open=false;expanded.value=false;actionsFor.value='';if(restore)trigger.value?.focus()}
function toggled(event){expanded.value=event.target.open;if(!expanded.value)actionsFor.value=''}
function outside(event){if(!popup.value&&!dropdown.value?.contains(event.target))closeMenu()}
function focusOutside(event){if(!popup.value&&!dropdown.value?.contains(event.relatedTarget))closeMenu()}
function escapeMenu(event){if(popup.value)return;event.preventDefault();event.stopPropagation();closeMenu(true)}
async function focusMenu(){if(dropdown.value)dropdown.value.open=true;expanded.value=true;await nextTick();menu.value?.querySelector('button:not(:disabled)')?.focus()}
function moveFocus(event){
 if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return
 const buttons=[...menu.value.querySelectorAll('button:not(:disabled)')]
 if(!buttons.length)return
 event.preventDefault()
 const index=buttons.indexOf(document.activeElement)
 const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length
 buttons[next].focus()
}
function join(){closeMenu();emit('join')}
onMounted(()=>document.addEventListener('pointerdown',outside))
const popup=computed(()=>notice.value?'notice':confirmCancel.value?'confirm':'')
const confirming=computed(()=>props.data?.choices?.find(item=>item.institute===confirmCancel.value))
watch(confirming,item=>{
 if(confirmCancel.value&&(!item||item.status!=='Pending')){
  confirmCancel.value='';notice.value='Your institute request has changed. Your workspaces are up to date.'
 }
})
let previousOverflow
function dismissConfirmation(){if(!busy.value)confirmCancel.value=''}
function dismissNotice(){notice.value='';cancelledInstitute.value=''}
watch(popup,async(value,previous)=>{
 if(value){
  if(!previous){previousOverflow=document.body.style.overflow;document.body.style.overflow='hidden'}
  await nextTick()
  if(popup.value!==value)return
  if(value==='notice'){confirmDialog.value?.close?.();noticeDialog.value?.showModal?.();okButton.value?.focus()}
  else{noticeDialog.value?.close?.();confirmDialog.value?.showModal?.();keepButton.value?.focus()}
 }else{
  confirmDialog.value?.close?.();noticeDialog.value?.close?.();document.body.style.overflow=previousOverflow||''
  if(previous==='notice'){closeMenu();trigger.value?.focus()}
 }
})
onBeforeUnmount(()=>{document.removeEventListener('pointerdown',outside);if(popup.value)document.body.style.overflow=previousOverflow||''})

function select(item){
 if(busy.value)return
 confirmCancel.value='';error.value=''
 if(item.status==='Pending'&&item.request){actionsFor.value=actionsFor.value===item.institute?'':item.institute;return}
 actionsFor.value='';if(item.institute===props.data.selected){closeMenu(true);return}open(item)
}
async function open(item){
 if(item.locked||busy.value||item.institute===props.data.selected)return
 busy.value=item.institute;error.value=''
 try{await request('campus_context','select',{institute:item.institute});location.assign('/campus')}
 catch(e){error.value=e.message;busy.value=''}
}
async function cancel(item){
 if(busy.value||item.status!=='Pending'||!item.request)return
 busy.value=item.institute;error.value='';notice.value=''
 try{
  await request('teacher_workspace','cancel_request',{request:item.request})
  confirmCancel.value='';actionsFor.value='';cancelledInstitute.value=item.title;notice.value=`Request to ${item.title} cancelled. You can apply again whenever you’re ready.`
  window.dispatchEvent(new Event('sisu-membership-cancelled'))
  emit('changed')
 }catch(e){error.value=e.message}finally{busy.value=''}
}
</script>
<template>
 <section class="teacher-workspaces" aria-label="Switch teaching workspace">
  <details ref="dropdown" class="workspace-dropdown" @toggle="toggled" @keydown.esc="escapeMenu" @focusout="focusOutside">
   <summary ref="trigger" class="workspace-trigger" :aria-expanded="expanded" aria-controls="teaching-workspace-menu" :aria-label="`Switch workspace: ${current?.title||'Choose workspace'}`" @keydown.down.prevent="focusMenu">
    <span class="workspace-circle workspace-circle--current"><img v-if="logo(current)" :src="logo(current)" alt="" @error="failedImages[current.institute]=true"/><UserRound v-else-if="current?.kind==='Personal'" :size="20" aria-hidden="true"/><Building2 v-else :size="20" aria-hidden="true"/></span>
    <span class="workspace-trigger-label"><strong>{{current?.title||'Choose workspace'}}</strong><small>Current workspace</small></span>
    <ChevronDown :size="15" class="workspace-chevron" aria-hidden="true"/>
   </summary>
   <div class="workspace-popover" id="teaching-workspace-menu">
    <div class="workspace-menu-heading"><strong>Switch workspace</strong><span>Choose where you teach</span></div>
    <nav ref="menu" aria-label="Teaching workspaces" @keydown="moveFocus">
     <div v-for="item in data?.choices||[]" :key="item.institute" class="workspace-choice" :class="{'is-current':data.selected===item.institute}">
      <button type="button" class="workspace-option" :disabled="(item.locked&&!(item.status==='Pending'&&item.request))||!!busy" :aria-expanded="item.status==='Pending'&&item.request?actionsFor===item.institute:undefined" :aria-pressed="data.selected===item.institute" @click="select(item)">
       <span class="workspace-circle" :class="{'workspace-circle--locked':item.locked}"><img v-if="logo(item)" :src="logo(item)" alt="" @error="failedImages[item.institute]=true"/><UserRound v-else-if="item.kind==='Personal'" :size="20" aria-hidden="true"/><Building2 v-else :size="20" aria-hidden="true"/><span v-if="item.locked" class="workspace-mark"><LockKeyhole :size="11" aria-hidden="true"/></span></span>
       <span class="workspace-label">{{item.title}}<small v-if="item.locked">{{item.status==='Pending'?'Pending approval':'Unavailable'}}</small><small v-else-if="busy===item.institute">Opening…</small><small v-else-if="data.selected===item.institute" class="workspace-current">Current workspace</small><small v-else>Open workspace</small></span>
       <Check v-if="data.selected===item.institute" :size="18" class="workspace-selected" aria-hidden="true"/>
      </button>
      <button v-if="item.status==='Pending'&&item.request&&actionsFor===item.institute" type="button" class="request-bin" :aria-label="`Cancel request to ${item.title}`" title="Cancel request" :disabled="!!busy" @click="confirmCancel=item.institute;error='';notice=''"><Trash2 :size="16" aria-hidden="true"/></button>
     </div>
     <button ref="joinButton" class="workspace-join" type="button" :disabled="locked||!!busy" @click="join"><span class="workspace-circle workspace-circle--add"><Plus :size="18" aria-hidden="true"/></span><span>Join institute</span></button>
    </nav>
    <p v-if="error&&!confirmCancel" class="workspace-error" role="alert">{{error}}</p>
   </div>
  </details>
  <dialog ref="noticeDialog" class="request-confirm-dialog request-success-dialog" aria-labelledby="request-notice-title" aria-describedby="request-notice-description" @cancel.prevent="dismissNotice">
   <template v-if="notice">
    <button type="button" class="request-confirm-close" aria-label="Close notification popup" @click="dismissNotice"><X :size="20"/></button>
    <span class="request-confirm-icon request-success-icon"><CheckCircle2 :size="28" aria-hidden="true"/></span>
    <h2 id="request-notice-title">{{cancelledInstitute?'Request cancelled':'Request updated'}}</h2>
    <p id="request-notice-description">{{notice}}</p>
    <div class="request-confirm-actions"><button ref="okButton" type="button" class="request-notice-ok" @click="dismissNotice">OK</button></div>
   </template>
  </dialog>
  <dialog ref="confirmDialog" class="request-confirm-dialog" aria-labelledby="request-cancel-title" aria-describedby="request-cancel-description" @cancel.prevent="dismissConfirmation">
   <template v-if="confirming">
    <button type="button" class="request-confirm-close" aria-label="Close cancellation popup" :disabled="!!busy" @click="dismissConfirmation"><X :size="20"/></button>
    <span class="request-confirm-icon"><Trash2 :size="24" aria-hidden="true"/></span>
    <h2 id="request-cancel-title">Cancel your institute request?</h2>
    <p id="request-cancel-description">Your pending request to <strong>{{confirming.title}}</strong> will be withdrawn. You can apply again later.</p>
    <p v-if="error" class="request-confirm-error" role="alert">{{error}}</p>
    <div class="request-confirm-actions">
     <button ref="keepButton" type="button" class="request-keep" :disabled="!!busy" @click="dismissConfirmation">Keep request</button>
     <button type="button" class="request-remove" :disabled="!!busy" @click="cancel(confirming)">{{busy?'Cancelling…':'Cancel request'}}</button>
    </div>
   </template>
  </dialog>
 </section>
</template>
<style scoped>
.teacher-workspaces{position:relative;min-width:0;color:var(--student-ink,#30243d)}
.workspace-dropdown{position:relative}
.workspace-trigger{display:flex;align-items:center;gap:10px;min-height:52px;padding:6px 10px;border:1px solid #d4e8da;border-radius:10px;background:#f0f8f2;cursor:pointer;list-style:none;color:#21603f;max-width:228px}
.workspace-trigger::-webkit-details-marker{display:none}
.workspace-trigger:hover,.workspace-dropdown[open] .workspace-trigger{background:#e5f2e9;border-color:#accfb9}
.workspace-trigger-label{display:flex;flex-direction:column;gap:3px;min-width:0;text-align:left}
.workspace-trigger-label strong{font-size:12px;font-weight:650;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.workspace-trigger-label small{font-size:10px;white-space:nowrap;color:#38694a}
.workspace-chevron{flex-shrink:0;margin-left:4px;transition:transform .15s ease-out}
.workspace-dropdown[open] .workspace-chevron{transform:rotate(180deg)}
.workspace-popover{position:absolute;top:calc(100% + 10px);right:0;z-index:45;width:336px;max-width:calc(100vw - 32px);box-sizing:border-box;border-radius:14px;background:var(--student-card,#fff);box-shadow:0 12px 40px #25173629;padding:8px;text-align:left}
.workspace-menu-heading{display:flex;flex-direction:column;gap:4px;padding:12px 12px 16px}
.workspace-menu-heading strong{font-size:14px;color:#30243d}.workspace-menu-heading span{font-size:12px;color:#70617b}
.teacher-workspaces nav{display:flex;flex-direction:column;gap:4px;max-height:min(400px,60dvh);overflow:auto;overscroll-behavior:contain;scrollbar-color:#c9bad9 transparent;scrollbar-width:thin}
button{font:inherit;cursor:pointer;border:0;background:none;color:inherit;border-radius:9px}
.workspace-choice{display:flex;align-items:center;border-radius:10px;position:relative}
.workspace-option{display:flex;flex:1;align-items:center;gap:12px;text-align:left;padding:12px;min-height:64px;min-width:0;width:100%}
.workspace-circle{position:relative;flex-shrink:0;display:grid;place-items:center;width:36px;height:36px;border:1px solid #d7cddf;border-radius:50%;background:#f4eff9;color:#623894}
.workspace-circle img{width:100%;height:100%;object-fit:cover;border-radius:50%}
.workspace-circle--current,.is-current .workspace-circle{background:#217448;border-color:#217448;color:white}
.workspace-label{flex:1;min-width:0;font-size:13px;line-height:1.4;overflow-wrap:anywhere;color:#392c46}
.workspace-label small{display:block;font-size:11px;line-height:1.4;color:#74647e;margin-top:3px}
.workspace-choice.is-current{background:#f0f8f2}.is-current .workspace-label,.is-current .workspace-label small,.workspace-selected{color:#21603f}.is-current .workspace-label{font-weight:650}
.workspace-selected{flex-shrink:0}
.workspace-mark{position:absolute;bottom:-3px;right:-4px;border:2px solid white;background:#776780;color:white;border-radius:50%;width:17px;height:17px;display:grid;place-items:center}
.workspace-circle--locked{background:#f1eff3;color:#807487}
.workspace-join{display:flex;align-items:center;gap:12px;min-height:56px;padding:12px;margin-top:4px;border-top:1px solid #e6dff0;border-radius:0;font-size:13px;text-align:left;color:#592b91}
.workspace-circle--add{width:30px;height:30px;margin:3px;background:transparent;border-style:dashed}
.workspace-option:not(:disabled):hover,.workspace-join:not(:disabled):hover{background:#f4eff9}
button:disabled{cursor:default;opacity:.6}
button:focus-visible,summary:focus-visible{outline:2px solid #7853a4;outline-offset:2px}
.workspace-choice .request-bin{display:grid;place-items:center;width:40px;height:40px;flex-shrink:0;padding:0;margin-right:8px;background:#fff1f2;color:#ba293e;border:1px solid #f3c5ca}
.workspace-choice .request-bin:hover{background:#ffe0e5}
.workspace-error{font-size:12px;line-height:1.5;color:#a51d32;margin:8px;padding:8px;background:#fff1f2;border-radius:8px}
@media(min-width:701px) and (max-width:1100px){.workspace-popover{left:0;right:auto}}
@media(max-width:700px){.workspace-trigger{max-width:180px;min-height:46px;gap:8px;padding:5px 8px}.workspace-trigger-label small{display:none}.workspace-trigger .workspace-circle{width:30px;height:30px}.workspace-popover{position:fixed;left:16px;right:16px;top:auto;width:auto;margin-top:8px}.workspace-choice .request-bin{min-width:44px;min-height:44px}}
@media(max-width:430px){.workspace-trigger{max-width:150px}.workspace-trigger-label strong{max-width:80px;font-size:11px}}
@media(prefers-reduced-motion:reduce){.workspace-chevron{transition:none}}
.request-confirm-dialog{position:fixed;inset:0;margin:auto;width:min(460px,calc(100vw - 32px));max-height:calc(100dvh - 32px);overflow:auto;box-sizing:border-box;border:0;border-radius:16px;padding:32px;background:#fff;color:#30243d;box-shadow:0 24px 70px #25173638;text-align:left}.request-confirm-dialog::backdrop{background:#20132a80}.request-confirm-dialog:not([open]){display:none}.request-confirm-dialog .request-confirm-close{position:absolute;right:14px;top:14px;display:grid;place-items:center;width:40px;height:40px;min-width:40px;padding:0;color:#675574}.request-confirm-icon{display:grid;place-items:center;width:48px;height:48px;border-radius:12px;background:#fff0f2;color:#b52d43;margin-bottom:20px}.request-confirm-dialog h2{font-size:24px;line-height:1.25;letter-spacing:-.025em;margin:0 24px 14px 0;color:#30243d}.request-confirm-dialog p{font-size:14px;line-height:1.7;text-align:left;margin:0;color:#65566e;overflow-wrap:anywhere}.request-confirm-dialog strong{color:#30243d;font-weight:650}.request-confirm-actions{display:flex;gap:12px;margin-top:28px}.request-confirm-actions button{flex:1;min-width:0;max-width:none;min-height:46px;padding:12px 16px;font-size:14px;font-weight:650;display:flex;justify-content:center;align-items:center;border-radius:9px}.request-confirm-actions .request-keep{background:#f5f0fa;color:#56288d;border:1px solid #d8c9e7}.request-confirm-actions .request-remove{background:#b52d43;color:white;border:1px solid #b52d43}.request-confirm-actions .request-remove:hover{background:#982237}.request-confirm-actions .request-keep:hover{background:#eae0f4}.request-confirm-dialog button:disabled{opacity:.6;cursor:wait}.request-confirm-dialog .request-confirm-error{background:#fff0f2;color:#a02137;padding:12px;margin-top:16px;border-radius:8px}@media(max-width:480px){.request-confirm-dialog{padding:26px 22px}.request-confirm-dialog h2{font-size:22px}.request-confirm-actions{flex-direction:column-reverse;gap:10px}.request-confirm-actions button{width:100%}}
.request-success-dialog{width:min(420px,calc(100vw - 32px));text-align:center}.request-success-dialog .request-success-icon{margin:0 auto 20px;background:#eaf5ef;color:#217448;border-radius:50%;width:56px;height:56px}.request-success-dialog h2{margin:0 18px 12px;text-align:center}.request-success-dialog p{text-align:center}.request-confirm-actions .request-notice-ok{background:#592b91;color:#fff;min-height:46px}.request-confirm-actions .request-notice-ok:hover{background:#482172}
</style>
