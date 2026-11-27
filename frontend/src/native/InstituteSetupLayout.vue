<script setup>
import BrandLogo from '../BrandLogo.vue'
import Icon from '../Icon.vue'
defineProps({title:String,description:String,step:{type:Number,default:0}})
const steps=['Verify your identity','Institute profile','Subscription']
</script>

<template>
  <div class="institute-setup">
    <header class="institute-setup-header">
      <BrandLogo/>
      <nav aria-label="Account"><a href="/me"><Icon name="UserRound" :size="17"/>Account settings</a><a href="/api/method/logout"><Icon name="LogOut" :size="17"/>Sign out</a></nav>
    </header>
    <main class="institute-setup-main">
      <ol class="institute-setup-progress" aria-label="Institute setup progress">
        <li v-for="(label,index) in steps" :key="label" :class="{current:step===index,complete:step>index}" :aria-current="step===index?'step':undefined">
          <span class="step-number"><Icon v-if="step>index" name="Check" :size="17"/><template v-else>{{index+1}}</template></span>
          <span>{{label}}<small>{{step>index?'Completed':step===index?'Current step':'Up next'}}</small></span>
        </li>
      </ol>
      <header class="institute-setup-intro"><h1>{{title}}</h1><p>{{description}}</p></header>
      <slot/>
    </main>
    <footer class="institute-setup-footer"><BrandLogo/><span>Your institute. Your learning community.</span></footer>
  </div>
</template>

<style scoped>
.institute-setup{--setup-purple:#572b91;--setup-ink:#2c2038;--setup-muted:#685b77;--setup-line:#e6ddec;background:#faf8fc;min-height:100dvh;font-family:'Manrope Variable',sans-serif;color:var(--setup-ink);padding:0 32px;caret-color:var(--setup-purple);scrollbar-color:#baa6ce #faf8fc}
.institute-setup-header,.institute-setup-main,.institute-setup-footer{max-width:1160px;margin-inline:auto;box-sizing:border-box}
.institute-setup-header{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:28px 0;border-bottom:1px solid var(--setup-line)}
.institute-setup-header :deep(.sisu-original-logo){max-width:135px}.institute-setup-header nav{display:flex;gap:12px;flex-wrap:wrap}.institute-setup-header a{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:8px 12px;border-radius:9px;color:var(--setup-purple);font-size:13px;text-decoration:none;box-sizing:border-box}.institute-setup-header a:hover{background:#eee7f5}
.institute-setup-main{padding:36px 0 48px}.institute-setup-progress{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;list-style:none;padding:0 0 28px;margin:0;border-bottom:1px solid var(--setup-line)}
.institute-setup-progress li{display:flex;gap:12px;align-items:center;font-size:14px;color:var(--setup-muted);line-height:1.4}.step-number{width:36px;height:36px;display:grid;place-items:center;flex-shrink:0;border:1px solid #c9bbd8;border-radius:50%;font-weight:700;background:white}.institute-setup-progress small{display:block;font-size:12px;font-weight:400;margin-top:4px}.institute-setup-progress .current{font-weight:700;color:var(--setup-purple)}.current .step-number{color:white;background:var(--setup-purple);border-color:var(--setup-purple)}.complete .step-number{background:#e7f3ec;color:#226442;border-color:#b8d7c5}
.institute-setup-intro{margin:36px 0 30px}.institute-setup-intro h1{font-size:clamp(28px,3vw,36px);line-height:1.2;letter-spacing:-.03em;font-weight:800;margin:0 0 12px;text-wrap:balance}.institute-setup-intro p{font-size:15px;line-height:1.75;color:var(--setup-muted);max-width:70ch;margin:0}
.institute-setup-footer{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:24px 0;border-top:1px solid var(--setup-line);color:var(--setup-muted);font-size:12px}.institute-setup-footer :deep(.sisu-original-logo){width:80px}.institute-setup :deep(:is(button,a,input,select,textarea):focus-visible){outline:3px solid #9066ba;outline-offset:3px}.institute-setup ::selection{background:#e5d7f4;color:#352044}
@media(max-width:600px){.institute-setup{padding:0 18px}.institute-setup-header{padding:18px 0;gap:10px;flex-wrap:wrap}.institute-setup-header nav{gap:4px}.institute-setup-header a{padding:8px;font-size:12px}.institute-setup-main{padding-top:24px}.institute-setup-progress{gap:12px;padding-bottom:22px}.institute-setup-progress li{flex-direction:column;align-items:flex-start;gap:9px;font-size:12px}.institute-setup-progress small{font-size:12px}.institute-setup-intro{margin:26px 0}.institute-setup-footer{align-items:flex-start;flex-wrap:wrap}}
</style>
