<script setup>
import lightLogo from './assets/sisu-original-light.png'
import darkLogo from './assets/sisu-original-dark.png'
</script>
<template><picture class="sisu-original-logo" role="img" aria-label="SISU"><img class="sisu-logo-light" :src="lightLogo" alt="" aria-hidden="true"><img class="sisu-logo-dark" :src="darkLogo" alt="" aria-hidden="true"></picture></template>
<style>
/* Original transparent PNGs stay unchanged. The frame excludes their empty canvas margins. */
.sisu-original-logo{display:inline-block;position:relative;overflow:hidden;width:128px;aspect-ratio:1444 / 448;flex-shrink:0;vertical-align:middle;line-height:0}
.sisu-original-logo img{position:absolute;width:138.504155%;max-width:none!important;height:auto;left:-19.598338%;top:-179.241071%;margin:0!important;padding:0!important;object-fit:contain}
.sisu-original-logo .sisu-logo-dark{display:none}
[data-student-theme=dark] .sisu-original-logo .sisu-logo-light,.entry-dark .sisu-original-logo .sisu-logo-light{display:none}
[data-student-theme=dark] .sisu-original-logo .sisu-logo-dark,.entry-dark .sisu-original-logo .sisu-logo-dark{display:block}
</style>
