<script setup>
import {ref,watch,nextTick} from 'vue'
const props=defineProps({modelValue:{type:String,default:''},label:{type:String,required:true},disabled:Boolean,invalid:Boolean})
const emit=defineEmits(['update:modelValue'])
const digits=ref(Array.from({length:6},(_,i)=>props.modelValue[i]||'')),inputs=ref([])
watch(()=>props.modelValue,value=>{if(value!==digits.value.join(''))digits.value=Array.from({length:6},(_,i)=>value[i]||'')})
function focus(index){nextTick(()=>{inputs.value[index]?.focus();inputs.value[index]?.select()})}
function update(index,text){
 const clean=text.replace(/[^0-9]/g,'').slice(0,6)
 if(!clean){digits.value[index]='';emit('update:modelValue',digits.value.join(''));return}
 const start=clean.length===6?0:index
 for(let i=0;i<clean.length&&start+i<6;i++)digits.value[start+i]=clean[i]
 emit('update:modelValue',digits.value.join(''))
 focus(Math.min(start+clean.length,5))
}
function input(index,event){update(index,event.target.value);event.target.value=digits.value[index]}
function paste(index,event){event.preventDefault();update(index,event.clipboardData.getData('text'))}
function key(index,event){
 if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();focus(Math.max(0,Math.min(5,index+(event.key==='ArrowLeft'?-1:1))))}
 if(event.key==='Backspace'&&!digits.value[index]&&index>0){event.preventDefault();digits.value[index-1]='';emit('update:modelValue',digits.value.join(''));focus(index-1)}
}
</script>
<template>
 <div class="otp-code" role="group" :aria-label="label">
  <p class="otp-label">{{label}}</p>
  <div class="otp-digits">
   <input v-for="(_,index) in digits" :key="index" :ref="el=>inputs[index]=el" :value="digits[index]" :aria-label="`${label}, digit ${index+1} of 6`" :aria-invalid="invalid||undefined" :disabled="disabled" type="text" inputmode="numeric" pattern="[0-9]" maxlength="6" :autocomplete="index===0?'one-time-code':'off'" autocapitalize="off" spellcheck="false" required @input="input(index,$event)" @paste="paste(index,$event)" @keydown="key(index,$event)" @focus="$event.target.select()"/>
  </div>
  <p class="otp-hint">Enter or paste your 6-digit code.</p>
 </div>
</template>
<style scoped>
.otp-code{margin:0;text-align:center}.otp-label{font-size:14px;font-weight:600;color:#28203b;margin:0 0 14px}.otp-digits{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;max-width:392px;margin:0 auto}
.otp-digits input{box-sizing:border-box;width:100%;min-width:0;height:58px;margin:0;padding:8px 0;border:1px solid #9985ad;border-radius:10px;background:#fcfbfe;color:#28203b;text-align:center;font-family:inherit;line-height:1.2;font-size:24px;font-weight:600;font-variant-numeric:tabular-nums;caret-color:#592b91}
.otp-digits input:focus{border-color:#592b91;outline:2px solid #592b91;outline-offset:2px;background:#faf8fe}.otp-digits input[aria-invalid="true"]{border-color:#a33246}.otp-digits input:disabled{background:#f5f1fa;opacity:.65}.otp-digits input::selection{background:#e3d5f7;color:#28203b}.otp-hint{font-size:13px;color:#64566f;margin:12px 0 0;line-height:1.5}
@media(max-width:380px){.otp-digits{gap:6px}.otp-digits input{height:48px;font-size:22px}}
</style>
