<script setup>
import {ref,watch,useAttrs} from 'vue'
import countries from './countries.json'
defineOptions({inheritAttrs:false})
const props=defineProps({modelValue:{type:String,default:''}})
const emit=defineEmits(['update:modelValue','input'])
const attrs=useAttrs(),region=ref('LK'),number=ref('')
const sorted=[...countries].sort((a,b)=>b.dial.length-a.dial.length)
watch(()=>props.modelValue,v=>{v=String(v||'');if(!v){number.value='';return}const current=countries.find(c=>c.code===region.value);const c=v.startsWith(current.dial)?current:sorted.find(c=>v.startsWith(c.dial));if(c){region.value=c.code;number.value=v.slice(c.dial.length)}else number.value=v},{immediate:true})
function update(){const c=countries.find(c=>c.code===region.value);let n=number.value.replace(/[\s()-]/g,'');if(n.startsWith('+')){const found=sorted.find(x=>n.startsWith(x.dial));if(found){region.value=found.code;n=n.slice(found.dial.length);number.value=n;emit('update:modelValue',found.dial+n);emit('input');return}}if(c.code==='LK')n=n.replace(/^0/,'');emit('update:modelValue',n?c.dial+n:'');emit('input')}
</script>
<template><span class="phone-field"><select v-model="region" aria-label="Country calling code" :disabled="attrs.disabled" @change="update"><option v-for="c in countries" :key="c.code" :value="c.code">{{c.flag}} {{c.dial}} · {{c.name}}</option></select><input v-bind="attrs" v-model="number" type="tel" inputmode="tel" autocomplete="tel-national" placeholder="Phone number" maxlength="15" @input="update"></span></template>
<style scoped>.phone-field{display:flex;gap:8px;align-items:stretch;width:100%;min-width:0}.phone-field select{width:120px;flex:0 0 120px}.phone-field input{min-width:0;flex:1;width:0}.phone-field select,.phone-field input{box-sizing:border-box;min-height:44px;margin:0;padding:10px 12px;border:1px solid #e4dfed;border-radius:12px;background:#fcfbff;color:#272237;font:inherit}</style>
