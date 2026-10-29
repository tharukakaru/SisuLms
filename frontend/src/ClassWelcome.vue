<script setup>
import {computed, onMounted, ref} from 'vue'
import Icon from './Icon.vue'
import {useDailyAffirmation} from './study/useDailyAffirmation.js'
const props=defineProps({title:String,provider:String,href:String,joined:Boolean})
const emit=defineEmits(['enter','close'])
const thought=useDailyAffirmation(), action=ref(null)
const destination=computed(()=>{try{const u=new URL(props.href);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}})
onMounted(()=>{if(!props.joined)action.value?.focus({preventScroll:true})})
</script>
<template>
  <section class="class-welcome" aria-label="Welcome to your lesson">
    <div class="welcome-drawing" aria-hidden="true">
      <span class="welcome-orbit"></span><span class="welcome-spark spark-one">✦</span><span class="welcome-spark spark-two">+</span>
      <div class="welcome-book"><div class="book-page left-page"><i></i><i></i><i></i></div><div class="book-page right-page"><i></i><i></i><i></i></div></div>
      <span class="welcome-play"><Icon name="Play" :size="18"/></span>
    </div>
    <div class="welcome-message"><span class="welcome-eyebrow">A LITTLE MOMENT TO BEGIN</span><h3>{{title||'Your next little discovery'}}</h3><p>{{thought.text}}</p>
      <p class="welcome-hint">{{joined?'Settle in. Your lesson is right here.':'Take a breath, bring your curiosity. Join whenever you’re ready.'}}</p>
      <div class="welcome-actions">
        <a v-if="destination&&!joined" ref="action" :href="destination" target="_blank" rel="noopener noreferrer" class="button primary">Join {{provider||'lesson'}} <Icon name="ArrowUpRight" :size="16"/></a>
        <button v-else-if="!joined" ref="action" class="button primary" @click="emit('enter')">Enter lesson <Icon name="ArrowRight" :size="16"/></button>
        <button class="text-button" @click="emit('close')">{{joined?'Dismiss welcome':'Back to sessions'}}</button>
      </div>
    </div>
  </section>
</template>
<style scoped>
.class-welcome{display:flex;align-items:center;gap:28px;padding:24px;margin:20px 0;border:1px solid #e3d9f0;border-radius:18px;background:var(--surface,#fff);color:var(--text,#17141c)}
.welcome-drawing{width:160px;height:150px;flex-shrink:0;position:relative;display:grid;place-items:center;perspective:450px}.welcome-orbit{position:absolute;inset:5px;border:1px dashed #d8c9ea;border-radius:50%;background:#faf7ff}.welcome-book{display:flex;width:105px;height:76px;transform:rotate(-8deg);filter:drop-shadow(0 7px 6px #4c1d8018);animation:book-arrive .65s ease-out both}.book-page{background:#fff;border:2px solid #4c1d80;width:50%;padding:18px 8px;display:flex;flex-direction:column;gap:8px}.left-page{border-radius:8px 0 0 4px;transform:skewY(7deg)}.right-page{border-radius:0 8px 4px 0;transform:skewY(-7deg);transform-origin:left;animation:page-open .75s ease-out both}.book-page i{height:2px;background:#b49bce;border-radius:2px}.book-page i:last-child{width:60%}.welcome-spark{position:absolute;color:#4c1d80;font-size:24px}.spark-one{left:5px;top:14px}.spark-two{right:4px;bottom:18px}.welcome-play{position:absolute;bottom:12px;left:16px;border:4px solid var(--surface,#fff);background:#4c1d80;color:white;border-radius:50%;width:38px;height:38px;display:grid;place-items:center}.welcome-eyebrow{font-size:10px;letter-spacing:.13em;font-weight:650;color:#6c4596}.welcome-message{min-width:0}.welcome-message h3{font-size:21px;line-height:1.35;margin:9px 0}.welcome-message p{font-size:15px;line-height:1.65;margin:8px 0;overflow-wrap:anywhere}.welcome-message .welcome-hint{font-size:13px;color:var(--muted,#60586b)}.welcome-actions{display:flex;align-items:center;flex-wrap:wrap;gap:18px;margin-top:16px}.welcome-actions .button{min-height:44px}
@keyframes book-arrive{from{opacity:0;transform:translateY(10px) rotate(-14deg)}to{opacity:1;transform:translateY(0) rotate(-8deg)}}@keyframes page-open{from{transform:rotateY(-65deg) skewY(-7deg)}to{transform:rotateY(0) skewY(-7deg)}}
@media(hover:hover) and (prefers-reduced-motion:no-preference){.welcome-book,.welcome-spark,.welcome-play{transition:transform .35s}.class-welcome:hover .welcome-book{transform:translateY(-5px) rotate(-3deg);animation:none}.class-welcome:hover .spark-one{transform:rotate(30deg)}.class-welcome:hover .spark-two{transform:translateY(-5px)}.class-welcome:hover .welcome-play{transform:scale(1.08)}}
@media(max-width:600px){.class-welcome{flex-direction:column;gap:12px;padding:20px;align-items:flex-start}.welcome-drawing{align-self:center;width:130px;height:120px}.welcome-message h3{font-size:19px}}
@media(prefers-reduced-motion:reduce){.class-welcome *{animation:none!important;transition:none!important}}
</style>
