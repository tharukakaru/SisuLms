<script setup>
import BrandLogo from './BrandLogo.vue'
defineProps({error:Object})
function reload(){window.location.reload()}
</script>
<template><section :class="error?'page-load-error':'loading-screen'" :role="error?'alert':'status'" :aria-busy="!error"><BrandLogo/><template v-if="error"><h2>This page couldn’t load</h2><p>Check your connection, then reload to try again.</p><button class="button primary" @click="reload">Reload page</button></template><p v-else>Making room for learning…</p></section></template>
<style scoped>.loading-screen{min-height:100vh;height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:25px;background:rgb(108 106 238 / 4%)}.loading-screen p{font-size:13px;color:#6C6AEE;margin:0}.page-load-error{min-height:60vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:20px;padding:24px;text-align:center}</style>
