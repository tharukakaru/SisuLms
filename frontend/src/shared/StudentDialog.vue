<script setup>
import {ref,onMounted,onBeforeUnmount,nextTick} from 'vue'
import Icon from '../Icon.vue'
const props=defineProps({title:{type:String,required:true},description:String,icon:{type:String,default:'BookOpen'},busy:Boolean})
const emit=defineEmits(['close'])
const dialog=ref(null)
let previousFocus
function close(){if(!props.busy)emit('close')}
onMounted(async()=>{previousFocus=document.activeElement;await nextTick();dialog.value?.showModal()})
onBeforeUnmount(()=>{dialog.value?.close();if(previousFocus?.isConnected)previousFocus.focus()})
</script>
<template>
  <dialog ref="dialog" class="student-flow-dialog" :aria-label="title" @cancel.prevent="close">
    <header class="student-flow-heading">
      <span class="student-flow-symbol"><Icon :name="icon" :size="24"/></span>
      <div><h2>{{title}}</h2><p v-if="description">{{description}}</p></div>
      <button type="button" class="student-flow-close" :aria-label="'Close '+title.toLowerCase()" :disabled="busy" @click="close"><Icon name="X" :size="20"/></button>
    </header>
    <div class="student-flow-body"><slot/></div>
    <footer v-if="$slots.actions" class="student-flow-actions"><slot name="actions"/></footer>
  </dialog>
</template>
<style>
.student-flow-dialog{--flow-accent:#572b91;--flow-ink:#282032;--flow-muted:#655d74;--flow-border:#e4dfeb;position:fixed;inset:0;margin:auto;padding:0;width:min(620px,calc(100vw - 32px));max-height:calc(100dvh - 32px);border:0;border-radius:20px;background:#fff;color:var(--flow-ink);box-shadow:0 24px 80px #24172f33;overflow:auto;overscroll-behavior:contain;scrollbar-width:thin;scrollbar-color:#bda7d1 #faf8fc;font:14px/1.65 Manrope,system-ui,sans-serif;box-sizing:border-box;scroll-padding-block:110px}
.student-flow-dialog::backdrop{background:#24172f80}
.student-flow-heading{position:sticky;top:0;z-index:2;display:flex;align-items:flex-start;gap:14px;padding:24px;background:#f3edf9;border-bottom:1px solid var(--flow-border)}
.student-flow-symbol{width:44px;height:44px;flex:0 0 44px;display:grid;place-items:center;border-radius:12px;background:#fff;color:var(--flow-accent)}
.student-flow-heading>div{flex:1;min-width:0}.student-flow-heading h2{font-size:24px;line-height:1.3;letter-spacing:-.6px;margin:0 0 6px;overflow-wrap:anywhere}.student-flow-heading p{margin:0;color:var(--flow-muted);font-size:13px}
.student-flow-close{flex:0 0 44px;width:44px;height:44px;display:grid;place-items:center;border:1px solid #d8cce5;border-radius:10px;background:white;color:var(--flow-accent);cursor:pointer}
.student-flow-body{padding:24px;display:grid;gap:18px}.student-flow-body :is(p,h3){margin:0}.student-flow-body h3{font-size:18px;line-height:1.5}.student-flow-body p{color:var(--flow-muted)}
.student-flow-body label{display:grid;gap:8px;font-weight:600}.student-flow-body :is(input:not([type=checkbox]),select,textarea){box-sizing:border-box;width:100%;min-height:48px;border:1px solid #bfb0d0;border-radius:10px;background:white;color:var(--flow-ink);padding:12px 14px;font:inherit}.student-flow-body input::placeholder{color:#766c84}
.student-flow-body form{display:grid;gap:16px}.student-flow-body pre{margin:0;padding:18px;border:1px solid var(--flow-border);border-radius:12px;background:#faf8fc;white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}
.student-flow-body .error{background:#fff1f3;border:1px solid #edc1ca;color:#9a263c;padding:12px 16px;border-radius:10px}.student-flow-body .student-flow-notice{padding:14px 16px;background:#f5f1fa;border-radius:10px}
.student-flow-dialog .button{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;border-radius:10px;padding:11px 17px;font:600 14px/1.5 Manrope,system-ui,sans-serif;cursor:pointer}.student-flow-dialog .button.primary{background:var(--flow-accent);color:#fff;border:1px solid var(--flow-accent)}.student-flow-dialog .button.subtle{background:white;color:var(--flow-accent);border:1px solid #cfc0df}.student-flow-dialog .text-button{color:var(--flow-accent);min-height:44px;text-align:left}
.student-flow-actions{position:sticky;bottom:0;z-index:2;display:flex;justify-content:flex-end;gap:12px;padding:18px 24px;background:white;border-top:1px solid var(--flow-border)}
.student-flow-dialog :is(button,input,select,textarea,a):focus-visible{outline:3px solid #9872c7;outline-offset:3px}.student-flow-dialog button:disabled{opacity:.55;cursor:not-allowed}
@media(max-width:600px){.student-flow-dialog{width:calc(100vw - 20px);max-height:calc(100dvh - 20px);border-radius:16px}.student-flow-heading{padding:18px 16px;gap:10px}.student-flow-heading h2{font-size:21px}.student-flow-symbol{width:36px;height:36px;flex-basis:36px}.student-flow-body{padding:20px 16px}.student-flow-body :is(input,select,textarea){font-size:16px}.student-flow-actions{padding:14px 16px;flex-wrap:wrap}.student-flow-actions .button{flex:1;min-width:110px}}
</style>
