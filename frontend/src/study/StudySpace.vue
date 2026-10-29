<script setup>
import {computed,ref,watch,onMounted,onBeforeUnmount,nextTick} from 'vue'
import Icon from '../Icon.vue'
import {createTimer,restoreTimer,startTimer,pauseTimer,displayedTime,elapsedTime,isFinished,formatTimer} from './timer'
import {createStudyAudio} from './audio'
import {studyTracks as sourceTracks} from './mediaLibrary'
const studyTracks=sourceTracks.map((track,index)=>({...track,displayTitle:'SISU Learning Lofi '+String(index+1).padStart(2,'0')}))
import {studyGradients} from './gradients'

const props=defineProps({member:Object,standalone:Boolean})
defineEmits(['notify','plans','navigate'])
const key='sisu-study-v1:'+props.member.name
let saved={};try{saved=JSON.parse(localStorage.getItem(key))||{}}catch{}
const root=ref(null),immersive=ref(false),timer=ref(restoreTimer(saved.timer)),now=ref(Date.now())
const minutes=ref(Math.round(timer.value.duration/60000)),recorded=ref(!!saved.recorded)
const sessions=ref(Array.isArray(saved.sessions)?saved.sessions.slice(-30):[])
const gradient=ref(studyGradients.some(g=>g.id===saved.gradient)?saved.gradient:'lavender')
const selectedGradient=computed(()=>studyGradients.find(g=>g.id===gradient.value))
const sound=ref(studyTracks.some(t=>t.id===saved.sound)?saved.sound:studyTracks[4].id)
const activeTrack=computed(()=>studyTracks.find(t=>t.id===sound.value))
const volume=ref(Number.isFinite(saved.volume)?Math.max(0,Math.min(1,saved.volume)):.25)
const playing=ref(false),busy=ref(false),message=ref(''),error=ref('')
const digits=computed(()=>formatTimer(displayedTime(timer.value,now.value)))
const total=computed(()=>Math.round(sessions.value.filter(s=>s.day===new Date(now.value).toLocaleDateString('en-CA')).reduce((a,s)=>a+s.seconds,0)/60))
const audio=createStudyAudio(()=>{playing.value=false;error.value='This track could not load. Please choose another.'})
let interval,disposed=false
function persist(){try{localStorage.setItem(key,JSON.stringify({timer:timer.value,gradient:gradient.value,sound:sound.value,volume:volume.value,sessions:sessions.value,recorded:recorded.value}))}catch{error.value='Your browser could not save these preferences.'}}
function stopAudio(){audio.stop();playing.value=false}
function logSession(){if(recorded.value||timer.value.mode==='break')return;const seconds=Math.floor(elapsedTime(timer.value)/1000);if(seconds>=1)sessions.value=[...sessions.value,{day:new Date().toLocaleDateString('en-CA'),seconds}].slice(-30);recorded.value=true}
function tick(){now.value=Date.now();if(isFinished(timer.value,now.value)){timer.value=pauseTimer(timer.value,now.value);logSession();stopAudio();message.value=timer.value.mode==='break'?'Break complete. Ready when you are.':'Focus session complete. Time for a little break.';persist()}}
function begin(){error.value='';message.value='';if(isFinished({...timer.value,running:true,startedAt:Date.now()})){timer.value=createTimer(timer.value.mode,minutes.value);recorded.value=false}timer.value=startTimer(timer.value);now.value=Date.now();persist()}
function pause(){timer.value=pauseTimer(timer.value);stopAudio();message.value='Paused. Take your time.';persist()}
function reset(){timer.value=createTimer(timer.value.mode,minutes.value);recorded.value=false;message.value='Timer reset.';stopAudio();persist()}
function chooseMode(mode){if(timer.value.running)return;minutes.value=mode==='break'?5:25;timer.value=createTimer(mode,minutes.value);recorded.value=false;message.value='';persist()}
function setMinutes(value){if(timer.value.running)return;try{const next=createTimer(timer.value.mode,Number(value));minutes.value=Number(value);timer.value=next;recorded.value=false;error.value='';message.value='';persist()}catch(e){error.value=e.message}}
function end(){timer.value=pauseTimer(timer.value);logSession();stopAudio();timer.value=createTimer(timer.value.mode,minutes.value);recorded.value=false;message.value='Study session saved.';persist()}
async function toggleAudio(){if(playing.value){stopAudio();return}busy.value=true;try{const started=await audio.play(sound.value,volume.value,activeTrack.value.src);if(!disposed)playing.value=started;error.value=''}catch{if(!disposed)error.value='Could not start this track. Try another track or press Play again.'}finally{busy.value=false}}
function changeSound(){stopAudio();error.value='';persist()}
async function fullScreen(){if(immersive.value){if(document.fullscreenElement===root.value)await document.exitFullscreen();immersive.value=false;return}immersive.value=true;await nextTick();try{await root.value.requestFullscreen()}catch{/* The fixed focus view also works without browser fullscreen. */}}
function fullscreenChanged(){if(!document.fullscreenElement)immersive.value=false}
function keydown(e){if(e.key==='Escape')immersive.value=false}
watch(gradient,persist)
watch(volume,value=>{audio.volume(value);persist()})
watch(immersive,value=>document.body.classList.toggle('study-immersive',value))
onMounted(()=>{tick();interval=setInterval(tick,500);document.addEventListener('visibilitychange',tick);document.addEventListener('fullscreenchange',fullscreenChanged);document.addEventListener('keydown',keydown)})
onBeforeUnmount(()=>{disposed=true;persist();clearInterval(interval);audio.dispose();document.removeEventListener('visibilitychange',tick);document.removeEventListener('fullscreenchange',fullscreenChanged);document.removeEventListener('keydown',keydown);document.body.classList.remove('study-immersive');if(document.fullscreenElement===root.value)document.exitFullscreen().catch(()=>{})})
</script>

<template>
  <div ref="root" class="pastel-study" :class="{immersive}">
    <header class="focus-heading">
      <div><span class="eyebrow">A LITTLE SPACE, JUST FOR YOU</span><h1>Settle in. Let’s study.</h1><p>Your colour. Your music. Your moment to focus.</p></div>
      <button class="focus-secondary" @click="fullScreen"><Icon :name="immersive?'Minimize':'Maximize'" :size="17"/>{{immersive?'Exit full screen':'Full screen'}}</button>
    </header>
    <div class="focus-layout">
      <section class="focus-canvas" :style="{background:selectedGradient.background}" aria-label="Study timer">
        <span class="focus-kicker"><Icon name="Sprout" :size="16"/> MAKE TIME FOR YOU</span>
        <div class="focus-timer">
          <div class="focus-modes" aria-label="Timer mode"><button v-for="mode in [{id:'focus',label:'Focus timer'},{id:'stopwatch',label:'Stopwatch'},{id:'break',label:'Take a break'}]" :key="mode.id" :aria-pressed="timer.mode===mode.id" :disabled="timer.running" @click="chooseMode(mode.id)">{{mode.label}}</button></div>
          <div class="focus-clock" role="timer" aria-live="off" :aria-label="(timer.mode==='stopwatch'?'Time studied ':'Time remaining ')+digits">{{digits}}</div>
          <p class="focus-caption">{{timer.running?'One thing at a time.':timer.elapsed?'A little pause.':'Make room for a little progress.'}}</p>
          <div v-if="timer.mode!=='stopwatch'" class="focus-duration"><button v-for="n in [5,25,45,60]" :key="n" :disabled="timer.running" :aria-pressed="timer.duration===n*60000" @click="setMinutes(n)">{{n}} min</button><label><input :value="minutes" type="number" min="1" max="180" :disabled="timer.running" aria-label="Custom focus minutes" @change="setMinutes($event.target.value)"/><span>min</span></label></div>
          <div class="focus-actions"><button class="focus-start" @click="timer.running?pause():begin()"><Icon :name="timer.running?'Pause':'Play'" :size="20"/>{{timer.running?'Pause':timer.elapsed?'Resume':'Start studying'}}</button><button class="focus-icon" @click="reset" aria-label="Reset study timer"><Icon name="RotateCcw" :size="19"/></button><button v-if="timer.elapsed||timer.running" class="focus-icon" @click="end" aria-label="Save and finish study session"><Icon name="Check" :size="19"/></button></div>
          <p class="focus-status" role="status">{{message}}</p>
        </div>
        <footer class="focus-canvas-footer"><span>{{selectedGradient.name}}</span><span>{{total}} {{total===1?'minute':'minutes'}} focused today</span></footer>
      </section>
      <aside class="focus-customize">
        <section class="focus-card"><div class="focus-card-title"><h2>Find your colour</h2><Icon name="Palette" :size="20"/></div><p>20 colour blends. Find the one that feels like you.</p><div class="gradient-chart" aria-label="Gradient themes"><button v-for="g in studyGradients" :key="g.id" :aria-pressed="gradient===g.id" :aria-label="g.name" :title="`${g.name}: ${g.from} → ${g.to}`" @click="gradient=g.id"><span class="gradient-swatch" :style="{background:g.background}"><Icon v-if="gradient===g.id" name="Check" :size="18"/></span><span class="gradient-name">{{g.name}}</span></button></div></section>
        <section class="focus-card"><div class="focus-card-title"><h2>A little background music</h2><Icon name="Headphones" :size="20"/></div><p>{{studyTracks.length}} tracks to help you settle in.</p><label class="music-label" for="study-sound">Choose a track</label><select id="study-sound" v-model="sound" @change="changeSound"><option v-for="track in studyTracks" :key="track.id" :value="track.id">{{track.displayTitle}}</option></select><div class="focus-audio"><button class="focus-icon" :disabled="busy" :aria-label="playing?'Stop study music':'Play study music'" @click="toggleAudio"><Icon :name="playing?'Pause':'Play'" :size="18"/></button><Icon name="Volume2" :size="17"/><input v-model.number="volume" type="range" min="0" max="1" step=".01" aria-label="Study music volume"/><span>{{Math.round(volume*100)}}%</span></div><small>{{playing?'Playing · '+activeTrack.displayTitle:'Press play when you’re ready.'}}</small></section>
      </aside>
    </div>
    <p v-if="error" class="focus-error" role="alert">{{error}}</p>
    <p class="focus-note">Your theme and timer are saved in this browser. Music stops when you pause, finish or leave Study Room.</p>
  </div>
</template>

<style scoped>
.pastel-study{color:#372947;--focus-accent:#63339a}.pastel-study *{box-sizing:border-box;animation:none!important;transition:none!important}.focus-heading{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:26px}.focus-heading h1{font-size:30px;letter-spacing:-1px;margin:8px 0}.focus-heading p{font-size:13px;color:#7b7285;margin:0}.focus-heading .eyebrow{color:#8a709f}.pastel-study button{font:inherit;cursor:pointer}.focus-secondary,.focus-icon{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:#fff;border:1px solid #e8e2ed;border-radius:12px;color:#51396a}.focus-secondary{font-size:12px!important;padding:12px 16px}.focus-layout{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:24px;align-items:stretch}.focus-canvas{min-height:650px;border-radius:26px;padding:32px;display:flex;flex-direction:column;border:1px solid #49335e0d;color:#372947}.focus-kicker{display:flex;align-items:center;gap:8px;font-size:10px;letter-spacing:1.7px;font-weight:700;opacity:.7}.focus-timer{margin:auto 0;text-align:center;padding:45px 0 18px}.focus-modes{display:inline-flex;flex-wrap:wrap;justify-content:center;gap:4px;padding:5px;border-radius:30px;background:#ffffff42}.focus-modes button{border:0;border-radius:24px;background:transparent;color:#5e4b70;padding:11px 16px;font-size:12px}.focus-modes button[aria-pressed=true]{background:#fff9;color:#382448}.focus-clock{font-size:clamp(48px,6vw,94px);font-weight:750;letter-spacing:-4px;line-height:1.15;font-variant-numeric:tabular-nums;margin:34px 0 12px;color:#372947}.focus-caption{font-size:14px;color:#665775}.focus-duration{display:flex;justify-content:center;flex-wrap:wrap;gap:7px;margin:30px 0}.focus-duration button,.focus-duration label{background:#ffffff40;border:1px solid #58466e26;border-radius:10px;color:#4e3a64;padding:9px 11px;font-size:11px}.focus-duration button[aria-pressed=true]{border-color:#795397;background:#ffffff73}.focus-duration label{display:flex;align-items:center;gap:3px;padding:6px}.focus-duration input{width:44px;min-height:0!important;padding:3px!important;border:0!important;background:transparent!important;color:inherit;font:inherit}.focus-actions{display:flex;justify-content:center;gap:9px}.focus-start{display:flex;align-items:center;gap:10px;border:0;border-radius:13px;padding:15px 25px;background:#63339a;color:white;font-size:13px!important}.focus-icon{width:46px;height:46px;flex-shrink:0}.focus-status{min-height:20px;margin:18px 0 0;font-size:12px;color:#665775}.focus-canvas-footer{display:flex;justify-content:space-between;gap:12px;font-size:11px;color:#705f7d}.focus-customize{display:flex;flex-direction:column;gap:18px}.focus-card{border:1px solid #eae3ef;background:#fff;border-radius:20px;padding:23px}.focus-card-title{display:flex;justify-content:space-between;align-items:center;gap:12px;color:#633e7d}.focus-card h2{font-size:15px;margin:0;color:#382947}.focus-card p{font-size:11px;line-height:1.6;color:#84788e;margin:9px 0 19px}.gradient-chart{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px 10px}.gradient-chart button{border:0;background:none;color:#76677f;min-width:0;padding:0;text-align:center}.gradient-swatch{display:flex;align-items:center;justify-content:center;height:44px;border-radius:9px;border:2px solid #49335e0a;color:#603b83}.gradient-chart button[aria-pressed=true] .gradient-swatch{outline:2px solid #7d51a4;outline-offset:2px;border-color:#fff}.gradient-name{display:block;font-size:8px;line-height:1.4;margin-top:6px}.music-label{display:block;font-size:10px;color:#796487;margin-bottom:7px}.focus-card select{width:100%;border:1px solid #e8dfef;border-radius:10px;background:#f9f6fc;padding:12px 9px;font:inherit;font-size:11px;color:#533d67}.focus-audio{display:flex;align-items:center;gap:9px;margin:16px 0 10px;color:#795a8b}.focus-audio .focus-icon{width:38px;height:38px;background:#f6f0fb}.focus-audio input{min-width:0;width:100%;accent-color:#79529c}.focus-audio>span{min-width:30px;font-size:10px}.focus-card small{font-size:10px;color:#81708b}.focus-note{font-size:10px;color:#8b8092;line-height:1.7;margin-top:19px}.focus-error{color:#a2344b;font-size:12px}.pastel-study button:disabled{opacity:.5;cursor:default}.pastel-study :is(button,input,select):focus-visible{outline:3px solid #8455b4;outline-offset:4px}.pastel-study.immersive{position:fixed;inset:0;z-index:300;overflow:auto;background:#f8f5fb;padding:24px}.immersive .focus-heading>div,.immersive .focus-customize,.immersive .focus-note{display:none}.immersive .focus-heading{position:absolute;right:38px;top:38px;z-index:1}.immersive .focus-layout{display:block}.immersive .focus-canvas{min-height:calc(100dvh - 48px)}.immersive .focus-clock{font-size:clamp(60px,10vw,140px)}
@media(max-width:1200px){.focus-layout{grid-template-columns:minmax(0,1fr) 310px;gap:18px}.focus-card{padding:20px}.focus-canvas{padding:25px}.focus-modes button{padding:10px 12px}}
@media(max-width:1000px){.focus-layout{grid-template-columns:1fr}.focus-canvas{min-height:540px}.focus-customize{display:grid;grid-template-columns:1fr 1fr;align-items:start}.focus-clock{font-size:80px}}
@media(max-width:600px){.focus-heading{align-items:flex-start}.focus-heading h1{font-size:23px}.focus-heading p{font-size:11px;max-width:220px}.focus-secondary{font-size:10px!important;padding:10px;white-space:nowrap}.focus-canvas{min-height:500px;padding:22px 14px;border-radius:20px}.focus-customize{display:flex}.focus-clock{font-size:55px;letter-spacing:-2px}.focus-modes button{font-size:10px;padding:10px}.focus-canvas-footer{font-size:9px}.focus-card{padding:21px}.gradient-name{font-size:9px}.gradient-swatch{height:48px}.immersive .focus-canvas{min-height:calc(100dvh - 28px)}.pastel-study.immersive{padding:14px}.immersive .focus-heading{top:24px;right:24px}.immersive .focus-kicker{margin-top:45px}}
</style>
<style scoped>
.focus-canvas{gap:24px;padding:28px}
.focus-kicker{align-self:flex-start;background:#ffffffe0;border-radius:20px;padding:9px 13px;opacity:1;color:#544164}
.focus-timer{background:#ffffffe0;border:1px solid #ffffff9c;border-radius:23px;padding:32px 16px 18px;width:100%;max-width:660px;margin:auto;box-shadow:0 12px 35px #3729470c}
.focus-canvas-footer{color:#493559;background:#ffffffe0;padding:11px 14px;border-radius:12px}
.gradient-chart button[aria-pressed=true] .gradient-swatch svg{background:#fff;border-radius:50%;padding:2px;box-sizing:content-box}
.gradient-swatch{height:48px;border-radius:11px}
.immersive .focus-timer{max-width:850px;padding:45px 20px}
@media(max-width:600px){.focus-canvas{padding:18px 12px;gap:20px}.focus-timer{padding:25px 8px 12px}.focus-kicker{font-size:9px}.focus-clock{font-size:50px}.focus-duration{gap:5px}.focus-duration button{padding:9px}.focus-canvas-footer{font-size:8px}}
</style>
<style>body.study-immersive{overflow:hidden}.study-immersive .soul-widget,.study-immersive .soul-companion{display:none}</style>
