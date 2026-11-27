<script setup>
import {ref,onMounted} from 'vue'
import {Building2,ArrowRight,UserRound} from 'lucide-vue-next'
import BrandLogo from '../BrandLogo.vue'
import {request} from './client'
const props=defineProps({teacher:Boolean})
const busy=ref(false),error=ref(''),heading=ref(null)
onMounted(()=>heading.value?.focus())
async function recover(){
  busy.value=true;error.value=''
  try{
    await request(props.teacher?'teacher_workspace':'campus_context',props.teacher?'open_workspace':'clear')
    location.assign('/campus#dashboard')
    // A hash-only navigation keeps the old Vue tree alive; load the new session context.
    location.reload()
  }catch(e){error.value='We couldn’t open another workspace. Try again or sign in with your account.';busy.value=false}
}
</script>
<template>
  <main class="workspace-recovery">
    <BrandLogo/>
    <section aria-labelledby="workspace-changed-title" class="workspace-recovery-panel">
      <Building2 :size="32" aria-hidden="true"/>
      <h1 ref="heading" id="workspace-changed-title" tabindex="-1">Your institute access has changed</h1>
      <p>You’re no longer connected to this institute workspace. Contact its administrator if you need to rejoin.</p>
      <p v-if="teacher">Your personal teaching space is still separate. You can open it to view your own classes and plan.</p>
      <p v-if="error" role="alert" class="workspace-recovery-error">{{error}}</p>
      <button class="button primary" :disabled="busy" @click="recover"><UserRound v-if="teacher" :size="18" aria-hidden="true"/>{{busy?'Opening workspace…':teacher?'Switch to Personal':'Choose another workspace'}}<ArrowRight :size="18" aria-hidden="true"/></button>
      <a href="/api/method/logout">Sign out</a>
    </section>
  </main>
</template>
<style scoped>
.workspace-recovery{max-width:680px;margin:0 auto;padding:48px 24px;color:var(--student-ink,#292332)}
.workspace-recovery-panel{margin-top:40px;padding:32px;border:1px solid #e2d9ed;border-radius:16px;background:#fff}
.workspace-recovery-panel>svg{color:#592c91;margin-bottom:20px}
.workspace-recovery h1{font-size:clamp(24px,4vw,32px);line-height:1.25;margin:0 0 18px;letter-spacing:-.02em}
.workspace-recovery h1:focus{outline:none}
.workspace-recovery p{font-size:16px;line-height:1.65;color:#63576e;margin:0 0 16px}
.workspace-recovery button{display:flex;align-items:center;justify-content:center;gap:10px;min-height:48px;margin-top:28px;width:100%;white-space:normal}
.workspace-recovery a{display:block;width:fit-content;margin:20px auto 0;color:#592c91;text-underline-offset:4px;min-height:24px}
.workspace-recovery :is(button,a):focus-visible{outline:3px solid #8b61bb;outline-offset:4px}
.workspace-recovery .workspace-recovery-error{color:#a12742;background:#fff0f2;border-radius:8px;padding:14px}
@media(max-width:480px){.workspace-recovery{padding:24px 16px}.workspace-recovery-panel{padding:24px;margin-top:28px}}
</style>
