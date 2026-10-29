<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue'
import animation from './education-motion.json'
const host=ref(null)
let player,observer,media,visible=true,disposed=false
function sync(){if(player)(media?.matches||!visible||document.hidden)?player.pause():player.play()}
onMounted(async()=>{media=matchMedia('(prefers-reduced-motion: reduce)');media.addEventListener('change',sync);document.addEventListener('visibilitychange',sync);const {default:lottie}=await import('lottie-web/build/player/lottie_light');if(disposed)return;player=lottie.loadAnimation({container:host.value,renderer:'svg',loop:true,autoplay:false,animationData:structuredClone(animation),rendererSettings:{progressiveLoad:true}});player.goToAndStop(20,true);observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;sync()});observer.observe(host.value);sync()})
onBeforeUnmount(()=>{disposed=true;observer?.disconnect();media?.removeEventListener('change',sync);document.removeEventListener('visibilitychange',sync);player?.destroy()})
</script>
<template><div class="education-motion"><div ref="host" aria-hidden="true" class="motion-canvas"></div></div></template>
<style scoped>.education-motion{position:relative;width:100%;max-width:390px;aspect-ratio:1.43;align-self:center}.motion-canvas{height:100%;width:100%;transition:transform .55s cubic-bezier(.2,.7,.3,1)}.education-motion:hover .motion-canvas{transform:translateY(-3px) scale(1.015)}@media(prefers-reduced-motion:reduce){.motion-canvas{transition:none!important;transform:none!important}}</style>
