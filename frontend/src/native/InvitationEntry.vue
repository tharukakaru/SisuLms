<script setup>
import {Mail,ArrowRight} from 'lucide-vue-next'
defineProps({signupAvailable:Boolean})
defineEmits(['signup'])
</script>
<template>
 <div class="invitation-entry">
  <Mail :size="30" aria-hidden="true"/>
  <h2 id="invitation-entry-title">Your teaching invitation awaits</h2>
  <p>Sign in with the email address that received the invitation. You’ll be able to review the institute and accept or decline.</p>
  <a class="entry-primary" href="/login?redirect-to=%2Fcampus%23invitations">Sign in to review invitation <ArrowRight :size="18" aria-hidden="true"/></a>
  <template v-if="signupAvailable"><p class="invitation-new">New to SISU?</p><button type="button" class="entry-secondary" @click="$emit('signup')">Create your teacher account <ArrowRight :size="18" aria-hidden="true"/></button><p class="invitation-hint">Use the invited email. Your invitation will be waiting after verification and sign-in.</p></template>
 </div>
</template>
<style scoped>
.invitation-entry{color:#30243d}.invitation-entry>svg{color:#592c91;margin-bottom:12px}.invitation-entry h2{line-height:1.25!important;letter-spacing:-.02em!important}.invitation-entry p{font-size:16px;line-height:1.65;color:#63576e;margin:16px 0 24px}.invitation-entry :is(a,button){display:flex;justify-content:center;align-items:center;gap:12px;min-height:50px;width:100%;white-space:normal;text-align:center;box-sizing:border-box}.invitation-entry .invitation-new{margin:28px 0 12px;font-weight:650;color:#30243d}.invitation-entry .invitation-hint{font-size:14px;margin-bottom:0}.invitation-entry :is(a,button):focus-visible{outline:3px solid #8b61bb;outline-offset:4px}
</style>
