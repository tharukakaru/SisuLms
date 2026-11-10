<script setup>
import TeacherSignupLayout from './TeacherSignupLayout.vue'
import {ArrowLeft} from 'lucide-vue-next'
import './verification.css'
defineProps({backHref:String})
defineEmits(['back'])
</script>

<template>
  <TeacherSignupLayout active verification>
    <main class="teacher-signup-form verification-content">
      <a v-if="backHref" :href="backHref" class="teacher-signup-back"><ArrowLeft :size="13" aria-hidden="true"/>Back to sign in</a>
      <button v-else type="button" class="teacher-signup-back" @click="$emit('back')"><ArrowLeft :size="13" aria-hidden="true"/>Back to sign in</button>
      <slot/>
    </main>
  </TeacherSignupLayout>
</template>
