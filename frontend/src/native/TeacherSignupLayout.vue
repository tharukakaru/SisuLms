<script setup>
import BrandLogo from '../BrandLogo.vue'
import WebWelcomeStory from '../learning/WebWelcomeStory.vue'
defineProps({active:Boolean,institute:Boolean})
</script>

<template>
  <div :class="[active?'teacher-signup-layout':'signup-layout-passthrough',{'institute-signup-layout':active&&institute}]">
    <aside v-if="active" class="teacher-signup-story">
      <a href="/campus" class="teacher-signup-brand" aria-label="SISU home"><BrandLogo/></a>
      <WebWelcomeStory provider/>
    </aside>
    <slot/>
  </div>
</template>

<style>
.signup-layout-passthrough{display:contents}
div.teacher-signup-layout{display:grid;grid-template-columns:minmax(0,600px) minmax(0,1fr);gap:96px;max-width:1440px;min-height:100vh;margin:0 auto;padding:24px;background:#fff;color:#19182e;font-family:'Manrope Variable',sans-serif}
.teacher-signup-story{min-width:0;position:relative;align-self:start;height:max(1052px,calc(100vh - 48px))}
.teacher-signup-brand{position:absolute;top:40px;left:48px;z-index:1;display:flex}
div.teacher-signup-layout .web-welcome-story{display:flex;flex-direction:column;min-height:1052px;height:100%;padding:142px 0 0;overflow:hidden;background:#fff;border-radius:0 0 32px 32px;color:#56288d}
div.teacher-signup-layout .web-story-copy{padding:0 48px}
div.teacher-signup-layout .web-story-copy>span{font:400 10px/1.4 'Manrope Variable',sans-serif;letter-spacing:1.3px}
div.teacher-signup-layout .web-story-copy h1{font:800 55px/1.08 'Manrope Variable',sans-serif!important;letter-spacing:-1.8px;margin:22px 0;color:#56288d}
div.teacher-signup-layout .web-story-copy p{font:700 16px/1.4 'Manrope Variable',sans-serif;color:#56288d;margin:0}
div.teacher-signup-layout .web-story-art{display:block;width:calc(100% - 140px);height:auto;aspect-ratio:1;object-fit:contain;margin:46px 68px 10px}
div.teacher-signup-layout .web-welcome-story footer{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;min-height:166px;padding:44px 48px 72px;gap:10px;margin-top:auto;background:url('../assets/figma/provider-story-footer.svg') top center/cover no-repeat;color:#56288d}
div.teacher-signup-layout .web-welcome-story footer strong{font-size:16px;line-height:1.4}
div.teacher-signup-layout .web-welcome-story footer span{font-size:12px;line-height:1.4}
div.teacher-signup-layout .teacher-signup-form{min-width:0;max-width:none;width:100%;margin:0;padding:60px 48px 24px 0;border:0;border-radius:0;background:#fff;box-shadow:none;color:#19182e;font-family:'Manrope Variable',sans-serif}
div.teacher-signup-layout .teacher-signup-form :is(h1,h2){font:800 36px/1.2 'Manrope Variable',sans-serif;letter-spacing:-1.2px;color:#19182e;margin:24px 0 20px}
div.teacher-signup-layout .teacher-signup-form .teacher-signup-back{display:flex;align-items:center;gap:4px;width:fit-content;min-height:24px;border:0;border-radius:0;background:none;padding:0;margin:0;color:#56288d;font:400 13px/24px 'Manrope Variable',sans-serif}
div.teacher-signup-layout .teacher-signup-form .teacher-signup-intro{color:#78758b;font-size:14px;line-height:24px;margin:0 0 20px}
div.teacher-signup-layout .teacher-signup-form fieldset{border:0;margin:0;padding:0;min-width:0}
div.teacher-signup-layout .teacher-signup-form label,div.teacher-signup-layout .teacher-field-group{display:grid;gap:6px;margin:0 0 12px;font:600 12px/1.5 'Manrope Variable',sans-serif;color:#19182e}
div.teacher-signup-layout .teacher-signup-form :is(input:not([type=checkbox]),select){min-width:0;width:100%;height:40px;padding:7px 14px;border:1px solid #e7e3ef;border-radius:14px;background:#fcfbfe;color:#19182e;font:400 14px/24px 'Manrope Variable',sans-serif;box-sizing:border-box}
div.teacher-signup-layout .teacher-signup-form input::placeholder{color:#858094;opacity:1}
div.teacher-signup-layout .teacher-signup-form .teacher-paired-fields{display:grid;grid-template-columns:1fr 1fr;gap:8px}
div.teacher-signup-layout .teacher-paired-fields label{margin:0}
div.teacher-signup-layout .teacher-sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}
div.teacher-signup-layout .teacher-signup-form .teacher-consent{display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin:0 0 18px;color:#78758b;font-size:12px;font-weight:400}
div.teacher-signup-layout .teacher-signup-form input[type=checkbox]{width:14px;height:14px;accent-color:#56288d;margin:0;flex-shrink:0}
div.teacher-signup-layout .teacher-consent a{text-decoration:underline}
div.teacher-signup-layout .teacher-signup-form button.teacher-submit{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;min-height:54px;margin:0;padding:14px 20px;border:0;border-radius:999px;background:#56288d;color:#fff;font:700 14px/24px 'Manrope Variable',sans-serif;cursor:pointer}
div.teacher-signup-layout .teacher-signup-form button.teacher-submit:hover:not(:disabled){background:#462073}
div.teacher-signup-layout .teacher-signup-form button:disabled{opacity:.55;cursor:not-allowed}
div.teacher-signup-layout .teacher-signup-form .teacher-extra-options{margin:16px 0 20px;color:#78758b;font-size:12px;line-height:1.6}
div.teacher-signup-layout .teacher-extra-options summary{cursor:pointer;color:#56288d;padding:6px 0}
div.teacher-signup-layout .teacher-extra-options[open] summary{margin-bottom:12px}
div.teacher-signup-layout .teacher-signup-form .teacher-help{font-size:12px;line-height:1.6;color:#78758b;margin:10px 0 16px}
div.teacher-signup-layout .teacher-signup-form :is(button,a,input,select,summary):focus-visible{outline:3px solid #8b61bb;outline-offset:3px}
div.teacher-signup-layout .teacher-signup-form .signup-feedback:empty{display:none}
div.teacher-signup-layout .teacher-signup-form .application-layout{display:block;max-width:none;margin:0}
div.teacher-signup-layout .teacher-signup-form .application-form{padding:0;border:0;box-shadow:none;background:none;border-radius:0}
div.teacher-signup-layout .teacher-signup-form .application-form form{margin:0}
div.teacher-signup-layout.institute-signup-layout .teacher-signup-form label,div.teacher-signup-layout.institute-signup-layout .teacher-field-group{gap:8px;margin-bottom:20px}
div.teacher-signup-layout.institute-signup-layout .teacher-paired-fields label{margin:0}
div.teacher-signup-layout.institute-signup-layout .teacher-signup-form :is(input:not([type=checkbox]),select){height:50px;padding-block:12px}
@media(min-width:1000px){
  div.teacher-signup-layout.institute-signup-layout .teacher-signup-form{padding-top:24px}
}
@media(min-width:1000px) and (max-width:1250px){
  div.teacher-signup-layout{grid-template-columns:minmax(0,45%) minmax(0,1fr);gap:48px}
  div.teacher-signup-layout .teacher-signup-form{padding-right:24px}
  div.teacher-signup-layout .web-story-copy{padding-inline:32px}
  div.teacher-signup-layout .web-story-copy h1{font-size:48px!important}
  div.teacher-signup-layout .web-story-art{width:calc(100% - 64px);margin-inline:32px}
}
@media(max-width:999px){
  div.teacher-signup-layout{display:block;padding:32px 24px;max-width:696px}
  div.teacher-signup-layout .web-welcome-story{display:none}
  .teacher-signup-story{height:auto}
  .teacher-signup-brand{position:static;margin-bottom:48px}
  div.teacher-signup-layout .teacher-signup-form{padding:0}
}
@media(max-width:480px){
  div.teacher-signup-layout .teacher-signup-form :is(h1,h2){font-size:30px;letter-spacing:-1px}
  div.teacher-signup-layout .teacher-signup-form .teacher-paired-fields{grid-template-columns:1fr}
}
</style>
