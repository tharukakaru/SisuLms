<script setup>
import {computed,ref} from 'vue'
import {guideContent} from './learning/guideContent'
import Icon from './Icon.vue'
const props=defineProps({role:String,demo:Boolean})
defineEmits(['tour','navigate'])
const search=ref('')
const guides=computed(()=>guideContent.filter(g=>['Super Admin','PlatformAdmin'].includes(props.role)?g.audience==='owner':g.audience==='all'||g.audience==='student'&&props.role==='Student'||g.audience==='provider'&&props.role!=='Student'||g.audience==='admin'&&props.role==='Admin').filter(g=>[g.title,g.body,...(g.steps||[]),...(g.examples||[]),...(g.rates||[]).map(r=>r.name)].join(' ').toLowerCase().includes(search.value.toLowerCase())).map(g=>({...g,steps:g.steps||[g.body]})))
</script>
<template><div class="page-heading"><div><div class="eyebrow">A LITTLE GUIDANCE GOES A LONG WAY</div><h1>Your SISU field guide.</h1><p>Quick walkthroughs for your {{role.toLowerCase()}} workspace.</p></div><button v-if="!['Super Admin','PlatformAdmin'].includes(role)" class="button primary" @click="$emit('tour')"><Icon name="Play" :size="17"/>Start product tour</button></div><section class="walkthrough-intro"><span class="stat-icon mint"><Icon name="Globe2" :size="28"/></span><div><h2>Local roots. A global learning community.</h2><p>Choose your country, education system and teaching languages when creating a workspace. Discover institutes and independent teachers, or start with one small task below.</p></div></section><label class="search guide-search">Search this guide<input type="search" v-model="search" placeholder="Classes, payments, profile…" aria-label="Search user guide"></label><div class="walkthrough-grid"><article v-for="(g,i) in guides" :key="g.title" class="panel" :class="{'pricing-guide':g.formula}"><div class="section-heading"><span class="stat-icon violet"><Icon :name="g.icon" :size="24"/></span><span class="eyebrow">WALKTHROUGH {{String(i+1).padStart(2,'0')}}</span></div><h2>{{g.title}}</h2><template v-if="g.formula"><p>{{g.body}}</p><div v-if="g.rates" class="guide-rate-wrap"><table class="guide-rates"><caption>Monthly platform pricing · LKR</caption><thead><tr><th scope="col">Package</th><th scope="col">Monthly package fee</th><th scope="col">Per active student per class/course per 30-day access period</th></tr></thead><tbody><tr v-for="r in g.rates" :key="r.name"><th scope="row">{{r.name}}</th><td>LKR {{r.base}}</td><td>+ LKR {{r.rate}}</td></tr></tbody></table></div><p class="guide-formula">{{g.formula}}</p></template><ol><li v-for="(s,j) in g.steps" :key="s"><span>{{j+1}}</span><p>{{s}}</p></li></ol><section v-if="g.examples" class="guide-examples" aria-label="Monthly pricing examples"><h3>See how it adds up</h3><p v-for="example in g.examples" :key="example">{{example}}</p></section><button v-if="!['Super Admin','PlatformAdmin'].includes(role)" class="button subtle" @click="$emit('navigate',g.page)">Open workspace <Icon name="ArrowRight" :size="16"/></button></article></div><section class="panel integration-status"><span class="stat-icon peach"><Icon name="ShieldCheck" :size="25"/></span><div><h3>Need a little help?</h3><p>Contact your institute for class questions. For account and platform billing questions, contact SISU through your provider. Online payments require an activated gateway; local previews never transfer money.</p></div></section></template>

<style scoped>
.pricing-guide{grid-column:1/-1;min-width:0}
.pricing-guide>p{font-size:14px;line-height:1.8}
.guide-rate-wrap{overflow-x:auto;margin:22px 0;border:1px solid #e7e0f0;border-radius:14px}
.guide-rates{width:100%;border-collapse:collapse;text-align:left;font-size:14px}
.guide-rates caption{text-align:left;padding:14px 18px;font-weight:700;background:#f6f2fb;color:#4b2777}
.guide-rates th,.guide-rates td{padding:14px 18px;border-top:1px solid #e7e0f0;vertical-align:top}
.guide-rates thead{font-size:12px;color:#655a72}
.guide-formula{padding:16px 20px;background:#eee8f8;color:#492274;border-radius:12px;font-weight:700}
.guide-examples{background:#f8f6fb;border:1px solid #e7e0f0;border-radius:14px;padding:20px;margin:20px 0}
.guide-examples h3{margin:0 0 14px;font-size:17px}
.guide-examples p{font-size:13px;line-height:1.8;margin:10px 0;color:#514560}
@media(max-width:560px){.guide-rates th,.guide-rates td{padding:12px 8px;font-size:12px}.guide-rates th:last-child{width:42%}}
</style>
