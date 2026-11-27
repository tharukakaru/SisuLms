<script setup>
import {onMounted,ref} from 'vue'
import {ArrowRight} from 'lucide-vue-next'
import VerificationLayout from './VerificationLayout.vue'

defineProps({checking:Boolean,error:String})
defineEmits(['back','billing','check'])
const heading=ref(null)
onMounted(()=>heading.value?.focus({preventScroll:true}))
</script>

<template>
  <VerificationLayout class="payment-required-layout" @back="$emit('back')">
    <h1 ref="heading" tabindex="-1">Your subscription needs attention.</h1>
    <p class="verification-intro">If you manage this workspace’s billing, review the invoice. Otherwise contact its administrator.</p>
    <section class="application-review-status" aria-labelledby="payment-required-title">
      <strong id="payment-required-title">Payment required</strong>
      <p>Owner or billing delegate: review the invoice. Learners and assigned teachers: contact the workspace administrator.</p>
    </section>
    <div class="payment-required-actions" :aria-busy="checking">
      <button type="button" class="teacher-submit" @click="$emit('billing')">Open billing<ArrowRight :size="16" aria-hidden="true"/></button>
      <button type="button" class="teacher-submit verification-secondary" :disabled="checking" @click="$emit('check')">{{checking?'Checking…':'Check again'}}<ArrowRight :size="16" aria-hidden="true"/></button>
    </div>
    <p v-if="error" class="payment-required-error" role="alert">{{error}}</p>
  </VerificationLayout>
</template>

<style scoped>
.payment-required-layout :deep(.teacher-signup-form h1:focus){outline:none}
.payment-required-actions{display:grid;gap:20px}
.payment-required-error{font-size:13px;line-height:1.6;color:#a52a46;margin:16px 0 0}
</style>
