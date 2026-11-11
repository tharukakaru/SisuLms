<script setup>
import {onMounted,ref} from 'vue'
import {ArrowLeft} from 'lucide-vue-next'

defineEmits(['choose','back'])
const heading=ref(null)
onMounted(()=>heading.value?.focus({preventScroll:true}))
</script>

<template>
  <div class="provider-account-choice">
    <button type="button" class="provider-back" @click="$emit('back')"><ArrowLeft :size="13" :stroke-width="1.7" aria-hidden="true"/>Back to role selection</button>
    <h2 id="provider-account-title" ref="heading" tabindex="-1">Choose your provider account</h2>
    <p>Teach independently or join an institute.</p>
    <div class="provider-choices">
      <button type="button" @click="$emit('choose','Individual Teacher','individual')"><strong>Individual teacher</strong><span>Your own profile, classes and institute memberships.</span></button>
      <button type="button" @click="$emit('choose','Individual Teacher','institute')"><strong>Institute teacher</strong><span>Create your teacher account, then request access to an existing institute.</span></button>
    </div>
  </div>
</template>

<style scoped>
.provider-account-choice{font-family:'Manrope Variable',sans-serif;color:var(--entry-ink)}
.provider-back{display:flex;align-items:center;gap:3px;width:fit-content;min-height:24px;padding:0;border:0;background:none;font:inherit;font-size:13px;color:#56288d;text-decoration:none;cursor:pointer}
.provider-back:hover{text-decoration:underline}
.provider-account-choice h2{font:800 36px/1.2 'Manrope Variable',sans-serif;letter-spacing:-1.2px;margin:24px 0 20px;color:var(--entry-ink)}
.provider-account-choice h2:focus{outline:none}
.provider-account-choice>p{font-size:14px;line-height:24px;color:var(--entry-muted);margin:0}
.provider-choices{display:grid;gap:20px;margin-top:20px}
.provider-choices button{display:flex;flex-direction:column;justify-content:center;gap:6px;min-height:102px;width:100%;padding:22px 24px;text-align:left;border:1px solid var(--entry-border);border-radius:20px;background:#fcfbfe;font-family:inherit;color:var(--entry-ink);cursor:pointer;transition:background .15s,border-color .15s}
.provider-choices strong{font-size:20px;font-weight:800;line-height:1.4}
.provider-choices span{font-size:14px;line-height:1.5;color:var(--entry-muted)}
.provider-choices button:hover{background:#f4effb;border-color:#9574bd}
.provider-account-choice :is(a,button):focus-visible{outline:3px solid #8b61bb;outline-offset:4px}
@media(max-width:480px){
  .provider-account-choice h2{font-size:30px;letter-spacing:-1px}
  .provider-choices button{padding:20px;min-height:112px}
  .provider-choices strong{font-size:19px}
  .provider-choices span{font-size:13px}
}
</style>
