<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
import LmsIdentityCard from '../commerce/LmsIdentityCard.vue'
defineProps({member:Object});defineEmits(['profile'])
const profile=ref(null),error=ref('')
onMounted(async()=>{try{profile.value=(await request('profiles','me')).profile}catch(e){error.value=e.message}})
</script>
<template><section class="panel student-account-summary"><h1>My account</h1><p>Manage account verification, appearance and connected services. Edit your personal profile in My Profile.</p><LmsIdentityCard v-if="profile?.lms_id" :profile="profile"/><div v-else class="id-placeholder"><h2>Your digital ID belongs here</h2><p>Complete account verification to create your ID, then add a profile and cover photo in My Profile.</p></div><button class="button subtle" @click="$emit('profile')">Edit in My Profile</button><p v-if="error" role="alert">{{error}}</p></section></template>
<style scoped>.student-account-summary{padding:28px}.student-account-summary p{line-height:1.7}.id-placeholder{padding:28px;margin:24px 0;border:1px dashed #d6cce6;border-radius:20px;background:#f6f3fb}</style>
