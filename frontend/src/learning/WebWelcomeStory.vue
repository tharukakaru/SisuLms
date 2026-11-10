<script setup>
import discover from '../assets/figma/discover.png'
</script>

<template>
  <section class="web-welcome-story" aria-label="Welcome to SISU">
    <div class="web-story-copy">
      <span>A LITTLE SPARK. A BIGGER WORLD.</span>
      <h1>Big dreams.<br>Start here.</h1>
      <p>A place for curious minds, inspiring teachers<br>and all the things you’ll become.</p>
    </div>
    <img class="web-story-art" :src="discover" alt="Students learning together with the SISU mascot" width="560" height="460">
    <footer><strong>More than lessons. A place to belong.</strong><span>Learn · Connect · Grow</span></footer>
  </section>
</template>

<style scoped>
.web-welcome-story{display:none}
@media(min-width:1000px){
  .web-welcome-story{display:flex;flex-direction:column;min-width:0;min-height:900px;padding:35px 0 0;position:relative;overflow:hidden;background:white;border-radius:32px;color:#56288d}
  .web-welcome-story>.sisu-original-logo{margin-left:48px}
  .web-story-copy{padding:32px 48px 10px}
  .web-story-copy>span{font:400 11px/1.4 'Manrope Variable',sans-serif;letter-spacing:1.6px}
  .web-story-copy h1{font:800 clamp(40px,3.8vw,55px)/1.08 'Manrope Variable',sans-serif!important;letter-spacing:-1.2px;margin:24px 0;color:#56288d}
  .web-story-copy p{font:700 16px/1.4 'Manrope Variable',sans-serif;color:#56288d;margin:0}
  .web-story-art{display:block;width:calc(100% - 36px);height:auto;aspect-ratio:560/460;object-fit:contain;margin:32px 18px 0}
  .web-welcome-story footer{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:10px;min-height:172px;padding:46px 48px 24px;margin-top:auto;background:url('../assets/figma/story-footer.svg') top center/cover no-repeat;color:white}
  .web-welcome-story footer strong{font-size:16px;line-height:1.4}
  .web-welcome-story footer span{font-size:12px;line-height:1.4}
}
</style>
