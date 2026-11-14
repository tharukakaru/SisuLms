<script setup>
import {computed,onMounted} from 'vue'
import FlagSelect from './FlagSelect.vue'
const props=defineProps({modelValue:{type:String,default:''}})
const emit=defineEmits(['update:modelValue'])

onMounted(()=>{if(!props.modelValue)emit('update:modelValue','Sri Lanka')})
</script>
<template><FlagSelect :model-value="modelValue || 'Sri Lanka'" @update:model-value="emit('update:modelValue',$event)" /></template>
