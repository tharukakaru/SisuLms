<script setup>
import {computed,ref} from 'vue'
import countries from './countries.json'
const props=defineProps({modelValue:String,phone:Boolean,disabled:Boolean})
const emit=defineEmits(['update:modelValue'])
const open=ref(false),search=ref(''),root=ref(null)
const flags=import.meta.glob('/node_modules/flag-icons/flags/4x3/*.svg',{eager:true,query:'?url',import:'default'})
const flag=c=>flags['/node_modules/flag-icons/flags/4x3/'+c.code.toLowerCase()+'.svg']
const selected=computed(()=>countries.find(c=>(props.phone?c.code:c.name)===props.modelValue))
const options=computed(()=>countries.filter(c=>(c.name+' '+c.dial+' '+c.code).toLowerCase().includes(search.value.toLowerCase())))
function choose(c){emit('update:modelValue',props.phone?c.code:c.name);open.value=false;root.value?.querySelector('button')?.focus()}
</script>
<template><span ref="root" class="flag-select" @focusout="e=>{if(!root.contains(e.relatedTarget))open=false}" @keydown.esc.stop.prevent="open=false"><button type="button" class="trigger" :disabled="disabled" :aria-expanded="open" :aria-label="phone?'Country calling code':'Country'" @click="open=!open;search='' "><img v-if="selected" :src="flag(selected)" alt=""><span>{{selected?(phone?selected.dial:selected.name):(modelValue||'Choose country')}}</span><span aria-hidden="true">&#9662;</span></button><span v-if="open" class="menu"><input v-model="search" aria-label="Search countries" placeholder="Search country or code" @keydown.enter.prevent><span class="options"><button v-for="c in options" :key="c.code" type="button" :aria-pressed="selected?.code===c.code" @click="choose(c)"><img :src="flag(c)" alt=""><span>{{c.name}}{{phone?' '+c.dial:''}}</span></button><span v-if="!options.length">No countries found</span></span></span></span></template>
<style scoped>
.flag-select{position:relative;display:block;min-width:0;width:100%;font:inherit}.trigger{display:flex;align-items:center;gap:8px;width:100%;min-height:44px;padding:10px 12px;border:1px solid #e4dfed;border-radius:12px;background:#fcfbff;color:#272237;font:inherit;text-align:left;cursor:pointer}.trigger>span:first-of-type{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.flag-select img{width:24px;height:18px;flex-shrink:0;object-fit:cover;border-radius:2px;max-width:none}.menu{position:absolute;top:calc(100% + 5px);left:0;z-index:1000;display:block;width:max(100%,260px);max-width:80vw;padding:8px;border:1px solid #e4dfed;border-radius:12px;background:white;box-shadow:0 8px 28px #29203826}.menu input{box-sizing:border-box;width:100%;padding:10px;border:1px solid #e4dfed;border-radius:8px;font:inherit}.options{display:block;max-height:230px;overflow:auto;margin-top:6px}.options button{display:flex;align-items:center;gap:10px;width:100%;padding:10px;border:0;border-radius:6px;background:white;color:#272237;font:inherit;text-align:left;cursor:pointer}.options button:hover,.options button:focus-visible,.options button[aria-pressed=true]{background:#f1ebfa}.trigger:focus-visible{outline:2px solid #6431a1;outline-offset:2px}.trigger:disabled{opacity:.6;cursor:default}
</style>
