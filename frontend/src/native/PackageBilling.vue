<script setup>
import SubscriptionBilling from './SubscriptionBilling.vue'
const emit=defineEmits(['changed'])
</script>
<template><SubscriptionBilling @changed="emit('changed')"/></template>
