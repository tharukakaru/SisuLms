<script setup>
import {ref, watch, onBeforeUnmount} from 'vue'
const props = defineProps({message: {type: String, default: ''}, failure: Boolean})
const visible = ref(false)
let timer
function stopTimer(){clearTimeout(timer)}
function dismiss(){stopTimer();visible.value=false}
function schedule(){stopTimer();if(!props.failure && visible.value)timer=setTimeout(dismiss,12000)}
watch(()=>[props.message,props.failure],()=>{stopTimer();visible.value=!!props.message;schedule()},{immediate:true})
onBeforeUnmount(stopTimer)
</script>
<template>
<Teleport to="body">
  <aside v-if="visible" class="owner-action-notice" :class="{'notice-failure':failure}" :role="failure?'alert':'status'" aria-atomic="true" @mouseenter="stopTimer" @mouseleave="schedule" @focusin="stopTimer" @focusout="schedule">
    <div><strong>{{failure?'Action needs attention':'Update'}}</strong><p>{{message}}</p></div>
    <button type="button" aria-label="Dismiss notification" @click="dismiss">×</button>
  </aside>
</Teleport>
</template>
<style scoped>
.owner-action-notice{position:fixed;top:calc(16px + env(safe-area-inset-top,0px));left:50%;transform:translateX(-50%);z-index:10000;display:flex;align-items:flex-start;gap:18px;width:min(560px,calc(100vw - 32px));box-sizing:border-box;padding:18px 20px;background:#fff;color:#243c32;border:1px solid #b5d8c3;border-left:5px solid #288153;border-radius:14px;box-shadow:0 8px 32px #0003;font:15px/1.5 system-ui,sans-serif;max-height:60vh;overflow:auto;overflow-wrap:anywhere}.owner-action-notice p{margin:6px 0 0}.owner-action-notice button{flex-shrink:0;margin-left:auto;border:0;border-radius:8px;background:transparent;color:inherit;font-size:26px;cursor:pointer;min-width:44px;min-height:44px}.owner-action-notice button:focus-visible{outline:2px solid currentColor;outline-offset:2px}.notice-failure{border-color:#ecc0c0;border-left-color:#b43535;color:#742323}
</style>
