<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue'
import {request} from './client'
const props=defineProps({provider:Boolean})
const emit=defineEmits(['opening'])
const chosen=computed(()=>institutes.value.find(i=>i.institute===selected.value))
const institutes=ref([]),selected=ref(''),loading=ref(true),saving=ref(false),error=ref('')
async function load(){loading.value=true;error.value='';try{const data=await request('campus_context','choices',{},'GET');institutes.value=data.institutes;selected.value=data.selected||''}catch(e){error.value=e.message}finally{loading.value=false}}
async function change(){saving.value=true;error.value='';try{await request('campus_context',selected.value?'select':'clear',selected.value?{institute:selected.value}:{});emit('opening');window.location.assign('/campus')}catch(e){error.value=e.message;saving.value=false}}
onMounted(()=>{load();window.addEventListener('sisu-memberships',load)})
onBeforeUnmount(()=>window.removeEventListener('sisu-memberships',load))
</script>
<template><section v-if="loading||error||institutes.length" class="campus-switcher" :aria-label="provider?'Teaching workspace':'Institute'"><label><span class="sr-only">Choose institute</span><select v-model="selected" :disabled="loading||saving" @change="change" aria-label="Choose institute"><option value="">{{loading?'Loading…':provider?'Choose institute':'Overall dashboard'}}</option><option v-for="item in institutes" :key="item.institute" :value="item.institute">{{item.title}}</option></select></label><span v-if="saving" role="status">Opening…</span><div v-if="error" role="alert">{{error}} <button @click="load">Retry</button></div></section></template>
<style scoped>.campus-switcher{display:flex;justify-content:flex-end;align-items:center;gap:8px;margin:0;max-width:340px}.campus-switcher select{max-width:100%;width:220px;min-height:34px;padding:5px 25px 5px 10px;border:1px solid #e8e7ed;border-radius:6px;background:var(--student-card,#fff);color:var(--student-ink,#38284a);font:inherit;font-size:13px}.campus-switcher label{min-width:0}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}.campus-switcher select:focus{outline:1px solid #998ba8;outline-offset:1px;box-shadow:none}@media(max-width:600px){.campus-switcher{max-width:100%}.campus-switcher select{width:190px}}</style>
