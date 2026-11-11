<script setup>
import {onMounted, ref} from 'vue'
import {ArrowLeft, ArrowRight} from 'lucide-vue-next'

defineProps({googleAvailable:Boolean})
defineEmits(['google','choose-path'])
const heading=ref(null)
onMounted(()=>heading.value?.focus({preventScroll:true}))
</script>

<template>
  <div class="learner-signin">
    <button type="button" class="learner-back" @click="$emit('choose-path')"><ArrowLeft :size="13" :stroke-width="1.7" aria-hidden="true"/>Back</button>
    <h2 id="learner-signin-title" ref="heading" tabindex="-1">Your learning starts here.</h2>
    <p>Create your SISU learner account with Google.</p>
    <button type="button" class="learner-google" :disabled="!googleAvailable" :aria-describedby="!googleAvailable?'learner-google-unavailable':undefined" @click="$emit('google')">Continue with Google <ArrowRight :size="18" aria-hidden="true"/></button>
    <p v-if="!googleAvailable" id="learner-google-unavailable" class="learner-unavailable" role="status">Google sign-in is being set up for this site. Please try again later.</p>
    <button type="button" class="learner-other-path" @click="$emit('choose-path')">Choose another path <ArrowRight :size="18" aria-hidden="true"/></button>
  </div>
</template>

<style scoped>
.learner-signin{font-family:'Manrope Variable',sans-serif;color:var(--entry-ink)}
.learner-back{padding:0;border:0;background:none;font-family:inherit;cursor:pointer;display:flex;align-items:center;gap:3px;width:fit-content;min-height:24px;font-size:13px;color:#56288d;text-decoration:none}
.learner-back:hover{text-decoration:underline}
.learner-signin h2{font:800 36px/1.2 'Manrope Variable',sans-serif;letter-spacing:-1.2px;margin:20px 0;color:var(--entry-ink)}
.learner-signin h2:focus{outline:none}
.learner-signin>p{font-size:14px;line-height:24px;color:var(--entry-muted);margin:0}
.learner-google{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;min-height:54px;margin-top:20px;padding:16px 24px;border:0;border-radius:999px;background:#56288d;color:#fff;font:700 14px/22px 'Manrope Variable',sans-serif;cursor:pointer}
.learner-google:hover:not(:disabled){background:#462073}
.learner-google:disabled{opacity:.55;cursor:not-allowed}
.learner-other-path{display:flex;align-items:center;justify-content:center;gap:12px;min-height:48px;margin:24px auto 0;padding:12px 16px;font:700 14px/24px 'Manrope Variable',sans-serif;color:var(--entry-ink);background:transparent;border:0;cursor:pointer}
.learner-other-path svg{color:#56288d}
.learner-other-path:hover{color:#56288d}
.learner-signin .learner-unavailable{font-size:12px;line-height:1.6;margin-top:12px}
.learner-signin :is(a,button):focus-visible{outline:3px solid #8b61bb;outline-offset:4px}
@media(max-width:480px){.learner-signin h2{font-size:30px;letter-spacing:-1px}}
</style>
