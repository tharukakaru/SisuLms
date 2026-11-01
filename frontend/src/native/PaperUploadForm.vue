<script setup>
import {ref,computed} from 'vue'
import {labels} from '../i18n'
import {PAPER_ACCEPT,uploadPaperDocument,validatePaperUpload} from './paperUpload'
const props=defineProps({classroom:String,language:String})
const emit=defineEmits(['close','uploaded','busy'])
const copy=computed(()=>({...labels.en.paperUpload,...labels[props.language]?.paperUpload}))
const title=ref(''),description=ref(''),file=ref(null),busy=ref(false),progress=ref(0),error=ref('')
let requestId=null
function changed(){requestId=null}
function choose(event){file.value=event.target.files[0]||null;changed();error.value=''}
async function submit(){
  if(busy.value)return
  error.value=''
  try{validatePaperUpload(title.value,file.value)}catch(e){error.value=e.message;return}
  busy.value=true;emit('busy',true);progress.value=0
  try{
    requestId ||= crypto.randomUUID()
    const result=await uploadPaperDocument({classroom:props.classroom,title:title.value,description:description.value,file:file.value,requestId,onProgress:value=>progress.value=value})
    emit('uploaded',result)
  }catch(e){error.value=e.message}finally{busy.value=false;emit('busy',false)}
}
</script>
<template>
<form class="panel paper-panel paper-upload-form" @submit.prevent="submit">
  <div class="section-heading"><h2>{{copy.heading}}</h2><button type="button" class="text-button" :disabled="busy" @click="emit('close')">{{copy.cancel}}</button></div>
  <fieldset :disabled="busy">
    <label>{{copy.title}}<input v-model="title" required maxlength="120" @input="changed"></label>
    <label>{{copy.instructions}}<textarea v-model="description" maxlength="1000" @input="changed"></textarea></label>
    <label>{{copy.document}}<input type="file" :accept="PAPER_ACCEPT" required @change="choose" aria-describedby="paper-format-help"></label>
    <p id="paper-format-help" class="field-help">{{copy.formats}}</p>
    <p v-if="file" class="upload-file-summary">{{file.name}} · {{(file.size/1024/1024).toFixed(2)}} MB</p>
    <p class="field-help">{{copy.access}}</p>
    <button class="button primary" :disabled="busy">{{busy?copy.uploading:copy.heading}}</button>
  </fieldset>
  <div v-if="busy" role="status"><progress :value="progress" max="100" :aria-label="copy.progress"></progress> {{progress}}% — {{progress===100?copy.processing:copy.uploading}}</div>
  <p v-if="error" role="alert" class="error">{{error}}</p>
</form>
</template>
<style scoped>.paper-upload-form fieldset{border:0;padding:0;margin:0;min-width:0}.paper-upload-form progress{width:min(100%,280px)}.paper-upload-form input[type=file]{max-width:100%;width:100%}.paper-upload-form :is(input,textarea,button):focus-visible{outline:2px solid var(--student-accent,#6c6aee);outline-offset:3px}</style>
