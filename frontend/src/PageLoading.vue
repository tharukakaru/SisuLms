<script setup>
defineProps({error:Object})
function reload(){window.location.reload()}
</script>
<template><section class="page-loading" :role="error?'alert':'status'" :aria-busy="!error"><span v-if="!error" class="loading-dot" aria-hidden="true"></span><div><h2>{{error?'This page couldn’t load':'Opening your workspace'}}</h2><p>{{error?'Check your connection, then reload to try again.':'Getting everything ready for you…'}}</p><button v-if="error" class="button primary" @click="reload">Reload page</button></div></section></template>
<style scoped>.page-loading{display:flex;align-items:center;gap:18px;padding:32px;margin:16px 0;border:1px solid var(--student-border,#e6e0ef);border-radius:18px;background:var(--student-card,#faf8ff)}.page-loading h2{font-size:18px;margin:0 0 8px}.page-loading p{color:var(--student-muted,#6c6277);line-height:1.6}.loading-dot{height:26px;width:26px;flex:none;border:3px solid #e6def3;border-top-color:#7045ac;border-radius:50%;animation:page-spin 1s linear infinite}@keyframes page-spin{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.loading-dot{animation:none}}</style>
