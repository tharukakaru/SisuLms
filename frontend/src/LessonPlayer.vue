<script setup>
import {computed} from 'vue'
import Icon from './Icon.vue'
const props=defineProps({videoId:String,title:String})
defineEmits(['close'])
const source=computed(()=>/^[\w-]{11}$/.test(props.videoId||'')?'https://www.youtube-nocookie.com/embed/'+props.videoId+'?playsinline=1&rel=0&origin='+encodeURIComponent(location.origin):'')
</script>
<template>
 <section class="lesson-player video-frame" aria-label="Classroom lesson player">
  <header><div><span class="eyebrow">YOUR SISU CLASSROOM</span><h3>{{title||'Your lesson'}}</h3></div><button class="icon-button" aria-label="Close lesson player" @click="$emit('close')"><Icon name="X"/></button></header>
  <iframe v-if="source" :key="source" :src="source" :title="title||'Classroom lesson video'" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
  <p v-else role="alert">This lesson needs a valid YouTube video or broadcast link.</p>
  <footer><Icon name="MonitorPlay" :size="17"/><span>Stay here, settle in and learn. Your class materials are a tab away.</span></footer>
  <details><summary>Video not playing?</summary><p>The teacher must allow embedding and start the broadcast. Private, age-restricted or removed videos may not play here. Your browser must allow the YouTube player.</p></details>
 </section>
</template>
<style scoped>
.lesson-player{width:100%;margin:24px 0;border:1px solid #e4dbee;border-radius:16px;overflow:hidden;background:#fff}.lesson-player header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 22px}.lesson-player h3{margin:7px 0 0;font-size:18px}.lesson-player iframe{display:block;width:100%;height:auto!important;aspect-ratio:16/9;border:0;background:#15101d}.lesson-player footer{display:flex;align-items:center;gap:10px;padding:16px 22px;background:#f8f5fc;font-size:13px;color:#583d77}.lesson-player details{padding:12px 22px;font-size:12px;line-height:1.6}.lesson-player summary{cursor:pointer}
</style>
