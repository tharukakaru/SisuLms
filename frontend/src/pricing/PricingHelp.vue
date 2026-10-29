<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue'
defineProps({term:String,text:String})
const trigger=ref(null),open=ref(false),pinned=ref(false),position=ref({})
const id='pricing-help-'+Math.random().toString(36).slice(2)
function show(){
 const r=trigger.value.getBoundingClientRect(),width=Math.min(300,window.innerWidth-32)
 position.value={width:width+'px',left:Math.max(16,Math.min(r.left,window.innerWidth-width-16))+'px',...(r.top>200?{bottom:window.innerHeight-r.top+8+'px'}:{top:r.bottom+8+'px'})}
 open.value=true
}
function close(){open.value=false;pinned.value=false}
function leave(){if(!pinned.value)open.value=false}
function toggle(){if(pinned.value)close();else{pinned.value=true;show()}}
function outside(e){if(!trigger.value?.contains(e.target)&&!document.getElementById(id)?.contains(e.target))close()}
function escape(e){if(e.key==='Escape')close()}
onMounted(()=>{document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);window.addEventListener('resize',close);window.addEventListener('scroll',close,true)})
onBeforeUnmount(()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);window.removeEventListener('resize',close);window.removeEventListener('scroll',close,true)})
</script>
<template><button ref="trigger" type="button" class="pricing-help" :aria-label="'Explain '+term" :aria-expanded="open" :aria-controls="id" :aria-describedby="open?id:undefined" @pointerenter="show" @pointerleave="leave" @focus="show" @blur="close" @click.stop.prevent="toggle">*</button><Teleport to="body"><span v-if="open" :id="id" role="tooltip" class="pricing-help-popup" :style="position" @pointerenter="show" @pointerleave="leave"><strong>{{term}}</strong>{{text}}</span></Teleport></template>
<style scoped>
.pricing-help{display:inline-flex!important;align-items:center;justify-content:center;position:relative;width:auto!important;height:auto;min-width:0!important;padding:0!important;margin:0 0 0 2px;border:0!important;border-radius:0;background:transparent!important;box-shadow:none!important;color:#d92d20!important;font:700 16px/1 sans-serif;vertical-align:baseline;cursor:help}.pricing-help::after{content:"";position:absolute;inset:-6px -4px}.pricing-help:focus-visible{outline:2px solid #d92d20;outline-offset:3px}.pricing-help-popup{position:fixed;z-index:10000;box-sizing:border-box;padding:14px 16px;border:1px solid #ddd0eb;border-radius:12px;background:#2e1b46;color:#fff;box-shadow:0 8px 26px #25133b26;font:400 13px/1.7 Arial,sans-serif;white-space:normal;text-align:left}.pricing-help-popup strong{display:block;color:#e4d0ff;margin-bottom:4px;font-size:13px}
</style>
