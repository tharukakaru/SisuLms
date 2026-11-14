<script setup>
import {computed,onMounted} from 'vue'
import countries from './countries.json'
const props=defineProps({modelValue:{type:String,default:''}})
const emit=defineEmits(['update:modelValue'])
const known=computed(()=>countries.some(c=>c.name===props.modelValue))
onMounted(()=>{if(!props.modelValue)emit('update:modelValue','Sri Lanka')})
</script>
<template><select :value="modelValue || 'Sri Lanka'" @change="emit('update:modelValue',$event.target.value)" autocomplete="country-name"><option v-if="modelValue && !known" :value="modelValue">{{modelValue}}</option><option v-for="c in countries" :key="c.code" :value="c.name">{{c.flag}} {{c.name}}</option></select></template>
<style scoped>select{box-sizing:border-box;width:100%;min-height:44px;padding:10px 12px;border:1px solid #e4dfed;border-radius:12px;background:#fcfbff;color:#272237;font:inherit}</style>
