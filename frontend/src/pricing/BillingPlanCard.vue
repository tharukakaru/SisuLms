<script setup>
import {computed} from 'vue'
import Icon from '../Icon.vue'
import {landingPlanDetails} from './landingPlanDetails'
const props=defineProps({plan:{type:Object,required:true},selected:Boolean,disabled:Boolean,expanded:Boolean,currency:{type:String,default:'LKR'}})
const emit=defineEmits(['choose','update:expanded'])
const name=computed(()=>props.plan.plan||props.plan.name)
const details=computed(()=>landingPlanDetails(name.value))
const amount=computed(()=>props.plan.monthly_minor??(props.plan.monthly_lkr==null?null:props.plan.monthly_lkr*100))
const money=computed(()=>amount.value==null?'Price unavailable':format(amount.value/100))
function format(value){return new Intl.NumberFormat('en-LK',{style:'currency',currency:props.currency,maximumFractionDigits:0}).format(value)}
</script>
<template>
 <article class="plan" :class="['tier-'+details?.tier,{selected}]">
  <header><h3>{{name}}</h3><span v-if="selected" class="selected-label"><Icon name="Check" :size="12"/>Selected</span></header>
  <p class="price">{{money}} / month<span v-if="details&&currency==='LKR'">+ {{format(plan.active_student_lkr??details.usageRate)}} per active student</span></p>
  <div class="tier-card" aria-hidden="true"><span class="tc-mark">sisu.</span><span class="tc-chip"><svg viewBox="0 0 40 30" fill="none"><rect x=".5" y=".5" width="39" height="29" rx="6"/><path d="M13 0v10H0m27-10v10h13M13 30V20H0m27 10V20h13M13 10h14v10H13z"/></svg></span><span class="tc-edition">LEARNVERSE</span><span class="tc-name">{{name}}</span></div>
  <p class="plan-est"><strong>{{money}}</strong><span>/ month base fee</span></p>
  <template v-if="details">
   <dl class="rows"><div><dt>Students</dt><dd>{{details.students}}</dd></div><div><dt>Teachers</dt><dd>{{details.teachers}}</dd></div><div><dt>Operators</dt><dd>{{details.operators}}</dd></div></dl>
   <p class="plan-for">{{details.description}}</p>
   <ul class="plan-feature-list plan-highlights"><li v-for="feature in details.highlights" :key="feature" class="feature-included"><Icon class="feature-state" name="Check" :size="15" aria-label="Included"/><strong class="feature-copy">{{feature}}</strong></li></ul>
   <p class="feature-section-label">Advanced features</p>
   <ul class="plan-feature-list"><li v-for="feature in details.advanced" :key="feature.label" :class="feature.included?'feature-included':'feature-unavailable'"><Icon class="feature-state" :name="feature.included?'Check':'Minus'" :size="15" :aria-label="feature.included?'Included':'Not included'"/><span class="feature-copy"><strong v-if="feature.included">{{feature.label}}</strong><template v-else>{{feature.label}}</template></span></li></ul>
   <details class="plan-full-features" :open="expanded"><summary :aria-label="'Show or hide core features for '+name" @click.prevent="emit('update:expanded',!expanded)"><span>{{expanded?'Hide core':'Core features'}}</span><Icon :name="expanded?'X':'Plus'" :size="18"/></summary><ul class="plan-feature-list"><li v-for="feature in details.core" :key="feature.label" class="feature-included"><Icon class="feature-state" name="Check" :size="15" aria-label="Included"/><strong class="feature-copy">{{feature.label}}</strong></li></ul></details>
  </template>
  <button class="choose-plan" type="button" :disabled="disabled||selected||amount==null" :aria-label="selected?name+' selected':'Choose '+name+' plan'" @click="emit('choose',name)"><span>{{selected?'Selected':'Choose plan'}}</span><Icon :name="selected?'Check':'ArrowUpRight'" :size="17"/></button>
 </article>
</template>

<style scoped>
.plans{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.plan{display:flex;flex-direction:column;padding:26px 22px 22px;border-radius:var(--r);background:#f0f0f0;color:var(--ink);transition:opacity .35s,transform .5s var(--ease)}
.plan:hover{transform:translateY(-4px)}
.plan.tier-3{background:#070707;color:#fff;box-shadow:0 0 0 1px var(--line-d)}
.plan h3{font-size:30px;font-weight:400;letter-spacing:-.035em;margin:0}
.price{font-size:14.5px;font-weight:600;color:var(--purple);margin:6px 0 0}
.price span{display:block;font-weight:400;color:var(--muted)}
.tier-3 .price{color:var(--purple-l)}
.tier-3 .price span{color:var(--muted-d)}
.plan-est{margin:0 0 10px;min-height:56px;font-size:14px;color:var(--muted)}
.plan-est strong{display:block;font-size:26px;font-weight:400;letter-spacing:-.03em;color:var(--ink);font-variant-numeric:tabular-nums}
.tier-3 .plan-est{color:var(--muted-d)}
.tier-3 .plan-est strong{color:#fff}
.plan.is-over .tier-card{opacity:.35}
.plan.is-over .plan-est{color:var(--ink);font-weight:600}
.tier-3 .rows div{border-color:var(--line-d)}
.tier-3 .rows dt{color:var(--muted-d)}
.plan-for{font-size:14px;color:var(--muted);margin:14px 0 4px}
.tier-3 .plan-for{color:var(--muted-d)}
.plan .ticks{margin:6px 0 22px}
.plan .ticks li{font-size:14px;padding:5px 0 5px 24px}
.plan .ticks li:before{top:10px}
.plan .button{margin-top:auto}
.tier-card{position:relative;aspect-ratio:1.586;margin:18px 0 16px;border-radius:12px;overflow:hidden;transition:opacity .35s,transform .7s var(--ease)}
.plan:hover .tier-card{transform:rotate(-1.5deg) scale(1.015)}
.tier-0 .tier-card{background:linear-gradient(135deg,#ffffff,#ececec 55%,#dcdcdc);box-shadow:inset 0 0 0 1px #0000000f}
.tier-1 .tier-card{background:linear-gradient(135deg,#f4f4f6,#bdbec6 40%,#ebebef 58%,#a3a4ad)}
.tier-2 .tier-card{background:linear-gradient(135deg,#f6e2a6,#d0a84e 45%,#e9cd83 62%,#a87f2e)}
.tier-3 .tier-card{background:linear-gradient(135deg,#2e2e2e,#0c0c0c);box-shadow:inset 0 0 0 1px #ffffff1f}
.tc-mark{position:absolute;left:14px;top:10px;font-size:20px;font-weight:800;letter-spacing:-.06em;color:#171717d9}
.tc-mark span{color:var(--purple)}
.tc-chip{position:absolute;left:16px;top:44%;width:34px;height:26px;border-radius:6px;background:linear-gradient(135deg,#f3e4b5,#c6a45d)}
.tc-name{position:absolute;right:14px;bottom:10px;font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#171717b3}
.tier-3 .tc-mark,.tier-3 .tc-name{color:#ffffffd9}
.tier-3 .tc-mark span{color:var(--purple-l)}

/* Minimal membership artwork and aligned feature lists. */
.plan .tier-card { isolation:isolate;aspect-ratio:1.8;border:1px solid #00000012;border-radius:10px;box-shadow:none;transform:none;transition:none; }
.plan:hover .tier-card { transform:none;box-shadow:none; }
.plan .tier-card:before,.plan .tier-card:after { content:none; }
.tier-0 .tier-card { background:#512779;color:#fff; }
.tier-1 .tier-card { background:#dde1e5;color:#25313b; }
.tier-2 .tier-card { background:#ddc798;color:#4a381b; }
.tier-3 .tier-card { background:#303944;color:#f5f5f7;border-color:#ffffff20; }
.plan .tc-mark { color:inherit;font-size:25px;left:18px;top:13px;letter-spacing:-1px;text-shadow:none; }
.plan .tc-mark span { color:inherit; }
.plan .tc-name { color:inherit;font-size:10px;font-weight:500;letter-spacing:.1em;right:17px;bottom:17px;text-shadow:none; }
.plan .tc-edition { position:absolute;left:18px;bottom:17px;font-size:8px;letter-spacing:.1em;opacity:.65; }
.plans { align-items:stretch; }
.plan { height:100%; }
.plan .plan-est { min-height:64px; }
.plan .plan-for { min-height:44px;display:flex;align-items:center; }
.plan-feature-list { list-style:none;padding:0;margin:0; }
.plan-feature-list li { display:flex;align-items:flex-start;gap:10px;min-height:44px;padding:10px 0;border-bottom:1px solid #0000000b;font-size:13px;line-height:1.5; }
.feature-section-label { margin:20px 0 8px;padding:0;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#8b8890; }
.tier-3 .feature-section-label { color:#b3acbd; }
.plan-feature-list .feature-copy { flex:1; }
.plan-feature-list strong { font-weight:600; }
.plan-feature-list .feature-state { width:15px;flex:none;color:#794bb1; }
.plan-feature-list .feature-included { color:#17121c; }
.plan-feature-list .feature-unavailable,.plan-feature-list .feature-unavailable .feature-state { color:#8b8890;font-weight:400; }
.plan-feature-list small { display:block;font-size:10px;font-weight:400;color:#77717e;line-height:1.6; }
.tier-3 .plan-feature-list li { border-color:#ffffff0b; }
.tier-3 .plan-feature-list .feature-included { color:#f6f4f9; }
.tier-3 .plan-feature-list .feature-state { color:#bca0e0; }
.tier-3 .plan-feature-list .feature-unavailable,.tier-3 .plan-feature-list .feature-unavailable .feature-state { color:#96919c; }
.tier-3 .plan-feature-list small { color:#b3acbd; }
.plan-full-features { margin:0 0 24px;border-bottom:1px solid #00000018; }
.plan-full-features summary { cursor:pointer;display:flex;align-items:center;justify-content:space-between;padding:16px 0;font-size:13px;font-weight:500;list-style:none; }
.plan-full-features summary::-webkit-details-marker { display:none; }
.plan-full-features .see-less { display:none; }
.plan-full-features[open] .see-more { display:none; }
.plan-full-features[open] .see-less { display:inline; }
.plan-full-features[open] .expand-symbol { transform:rotate(45deg); }
.plan-full-features summary:focus-visible { outline:2px solid #9868d7;outline-offset:3px;border-radius:4px; }
.tier-3 .plan-full-features { border-color:#ffffff24; }
@media(max-width:600px) { .plan-feature-list li { min-height:48px; } }
/* Reserve the same room for release notes in every plan column. */

/* Satin membership finishes with restrained branding. */
.plan .tier-card { aspect-ratio:1.586;border-radius:13px;border:1px solid #ffffff50;box-shadow:inset 0 1px 0 #ffffff65,0 8px 16px -12px #0007; }
.tier-0 .tier-card { background:radial-gradient(ellipse at 100% 0%,#b880f0 0,transparent 65%),linear-gradient(125deg,#4e2085,#8240c4);color:#fff; }
.tier-1 .tier-card { background:radial-gradient(ellipse at 100% 0%,#ebdce5 0,transparent 65%),linear-gradient(125deg,#a3adb8,#e4ebed 55%,#b8c9d1);color:#27343c; }
.tier-2 .tier-card { background:radial-gradient(ellipse at 100% 0%,#f3e9ce 0,transparent 65%),linear-gradient(125deg,#ac8849,#e4cca0 60%,#ccb27a);color:#443419; }
.tier-3 .tier-card { background:radial-gradient(ellipse at 100% 0%,#576670 0,transparent 65%),linear-gradient(125deg,#15181e,#30343e);color:#f2f3f5; }
.plan .tc-mark { top:18px;left:19px;font-size:28px;letter-spacing:-1.6px; }
.plan .tc-name { left:19px;right:auto;bottom:19px;font-size:10px;letter-spacing:.14em;font-weight:600; }
.plan .tc-edition { left:auto;right:18px;bottom:20px;font-size:6px;letter-spacing:.16em;opacity:.65; }
.plan .tc-chip { display:block;position:absolute;right:20px;top:55%;width:31px;height:24px;border-radius:5px;background:linear-gradient(120deg,#c4c4c2,#f2f1ec,#a5a6a5);box-shadow:inset 0 0 0 1px #ffffff80; }
.plan .tc-chip svg { width:100%;height:100%;stroke:#656763;stroke-width:.55;opacity:.65; }

.plan{--ink:#17121c;--muted:#67616d;--muted-d:#b9b4bf;--purple:#67418f;--purple-l:#c8a5f2;--line-d:#ffffff24;--r:16px;--ease:ease;box-sizing:border-box;min-width:0;padding:26px 20px 22px!important;border:1px solid transparent!important;border-radius:16px!important;background:#f5f5f5;font-family:Manrope,sans-serif;transition:none}
.plan:hover{transform:none}.plan.selected{outline:2px solid #9868d7;outline-offset:3px}
.plan header{display:flex;align-items:center;justify-content:space-between;gap:6px;min-height:40px;position:relative}.plan h3{font-size:28px!important;line-height:1.3;margin:0!important;color:inherit!important}
.selected-label{position:absolute;right:0;top:-17px;display:inline-flex;align-items:center;gap:3px;color:#542785;background:#eee8f6;padding:4px 6px;border-radius:5px;font-size:10px}
.plan p{font-size:13px;line-height:1.6;color:var(--muted)}.plan .price{margin:6px 0 0;min-height:42px}.plan .plan-est{margin:0 0 10px}.plan .plan-for{margin:14px 0 4px}.tier-card{flex-shrink:0}
.plan .rows{margin:0}.rows div{display:flex;align-items:center;justify-content:space-between;gap:8px;border-top:1px solid #00000018;padding:12px 0;font-size:13px}.rows dt{color:var(--muted)}.rows dd{margin:0;text-align:right}
.plan.tier-2{border-color:#c8a5f2!important;background:#f5f1fc}.tier-2 h3{color:#6331b5!important}
.plan.tier-3{--muted:#b9b4bf;background:#1c1c1c;color:#fff;border-color:#3a3a3a!important;box-shadow:none}
.plan .feature-section-label{margin:20px 0 8px;font-size:11px}.plan .feature-unavailable,.plan .feature-unavailable .feature-state{color:var(--muted)}.plan-feature-list li{box-sizing:border-box}.plan-feature-list svg{margin-top:2px}.plan-full-features summary{min-height:50px;box-sizing:border-box}
.plan .choose-plan{display:flex;align-items:center;justify-content:center;gap:15px;margin-top:auto!important;padding:12px 15px;min-height:46px;width:100%;border:0;border-radius:30px;background:#111;color:#fff;font:600 13px Manrope,sans-serif;cursor:pointer}.tier-3 .choose-plan{background:#fff;color:#111}.choose-plan:hover:not(:disabled){background:#542785;color:#fff}.choose-plan:disabled{opacity:.6;cursor:default}.choose-plan:focus-visible{outline:2px solid #9868d7;outline-offset:4px}

</style>
