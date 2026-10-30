<script setup>
import {computed,onMounted,ref,watch} from 'vue'
import {request} from './client'
import {emptyQuestion,quizErrors,hasQuizErrors,completeAnswers} from './classroomQuizRules'
import {labels} from '../i18n'
const props=defineProps({classroom:String,language:{type:String,default:'en'}})
const emit=defineEmits(['capability','editing','busy','readiness'])
const copy=computed(()=>({...labels.en.classroomQuiz,...(labels[props.language]?.classroomQuiz||{})}))
const rows=ref([]),canManage=ref(false),busy=ref(false),error=ref(''),message=ref(''),page=ref(0)
const schemaReady=ref(false)
const editor=ref(null),preview=ref(false),errors=ref({questions:[]}),selected=ref(null),answers=ref([]),review=ref(false),result=ref(null),results=ref([]),resultsPage=ref(0)
watch(busy,value=>emit('busy',value))
async function run(fn){if(busy.value)return;busy.value=true;error.value='';message.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}
async function load(){const data=await request('classroom_quizzes','listing',{classroom:props.classroom,page:page.value});rows.value=data.items}
async function initialize(){
  if(busy.value)return
  schemaReady.value=false;canManage.value=false
  emit('readiness',{status:'loading',can_manage:null,error:''})
  await run(async()=>{
    let data
    try{
      data=await request('classroom_quizzes','metadata',{classroom:props.classroom})
      if(typeof data?.can_manage!=='boolean'||typeof data?.schema_ready!=='boolean')throw Error('The quiz setup response was incomplete. Update the backend and retry.')
    }catch(e){emit('readiness',{status:'error',can_manage:null,error:e.message});throw e}
    canManage.value=data.can_manage;schemaReady.value=data.schema_ready
    emit('capability',data.can_manage)
    emit('readiness',{status:data.schema_ready?'ready':'setup',can_manage:data.can_manage,error:''})
    if(data.schema_ready)await load()
  })
}
function create(){if(!canManage.value||!schemaReady.value||busy.value)return;selected.value=null;editor.value={classroom:props.classroom,title:'',instructions:'',questions:[emptyQuestion()]};preview.value=false;errors.value={questions:[]};error.value='';message.value='';emit('editing',true)}
function back(){editor.value=null;selected.value=null;preview.value=false;error.value='';message.value='';emit('editing',false)}
async function save(publish=false){
  errors.value=publish?quizErrors(editor.value):{questions:[]}
  if(publish&&hasQuizErrors(errors.value))return
  await run(async()=>{const saved=await request('classroom_quizzes','save',{data:editor.value,publish});Object.assign(editor.value,saved);message.value=publish?copy.value.published:copy.value.saved;await load();if(publish){editor.value=null;emit('editing',false)}})
}
async function open(row){await run(async()=>{const data=await request('classroom_quizzes','detail',{name:row.name});selected.value=data;result.value=data.result||null;answers.value=data.questions.map(()=>null);review.value=false;resultsPage.value=0;results.value=[];if(data.can_manage){results.value=await request('classroom_quizzes','submissions',{name:data.name,page:0})}emit('editing',true)})}
function edit(){editor.value=JSON.parse(JSON.stringify(selected.value));selected.value=null;preview.value=false;errors.value={questions:[]}}
async function showPreview(){preview.value=true;error.value=''}
function reviewAnswers(){if(!completeAnswers(selected.value.questions,answers.value)){error.value=copy.value.answerAll;return}error.value='';review.value=true}
async function submit(){await run(async()=>{result.value=await request('classroom_quizzes','submit',{name:selected.value.name,answers:answers.value});review.value=false;await load()})}
async function resultPage(delta){await run(async()=>{const next=resultsPage.value+delta;const data=await request('classroom_quizzes','submissions',{name:selected.value.name,page:next});results.value=data;resultsPage.value=next})}
defineExpose({create,back,initialize})
onMounted(initialize)
</script>

<template>
<section class="classroom-quizzes" :aria-label="copy.quizzes" :aria-busy="busy">
  <p v-if="error" class="error" role="alert">{{error}}</p>
  <p v-if="message" class="form-note" role="status">{{message}}</p>
  <form v-if="editor&&!preview" class="panel paper-panel" novalidate @submit.prevent="save(true)">
    <div class="section-heading"><h2>{{copy.editor}}</h2><button type="button" class="text-button" :disabled="busy" @click="back">{{copy.cancel}}</button></div>
    <fieldset :disabled="busy" class="quiz-fields">
      <label>{{copy.title}} <span aria-hidden="true">*</span><input v-model="editor.title" maxlength="120" required :aria-invalid="!!errors.title" aria-describedby="quiz-title-error"></label>
      <p v-if="errors.title" id="quiz-title-error" class="error" role="alert">{{errors.title}}</p>
      <label>{{copy.instructions}}<textarea v-model="editor.instructions" maxlength="2000"></textarea></label>
      <p role="status">{{editor.questions.length}} / 50 {{copy.questions}}</p>
      <p v-if="errors.count" class="error" role="alert">{{errors.count}}</p>
      <article v-for="(q,i) in editor.questions" :key="i" class="paper-question">
        <div class="section-heading"><h3>{{copy.question}} {{i+1}}</h3><button type="button" class="text-button" @click="editor.questions.splice(i,1);errors.questions=[]">{{copy.remove}}</button></div>
        <label>{{copy.question}}<textarea v-model="q.prompt" maxlength="3000" required :aria-invalid="!!errors.questions[i]?.prompt" :aria-describedby="'quiz-question-error-'+i"></textarea></label>
        <div :id="'quiz-question-error-'+i" class="error" role="alert"><p v-for="(text,key) in errors.questions[i]" :key="key">{{text}}</p></div>
        <label v-for="(_,j) in q.options" :key="j">{{copy.option}} {{'ABCD'[j]}}<input v-model="q.options[j]" maxlength="500" required :aria-invalid="!!errors.questions[i]?.options" :aria-describedby="'quiz-question-error-'+i"></label>
        <label>{{copy.correctOption}}<select v-model="q.answer" required :aria-invalid="!!errors.questions[i]?.answer" :aria-describedby="'quiz-question-error-'+i"><option :value="null" disabled>{{copy.choose}}</option><option v-for="(_,j) in q.options" :key="j" :value="j">{{'ABCD'[j]}}</option></select></label>
      </article>
      <button type="button" class="button subtle" :disabled="editor.questions.length>=50" @click="editor.questions.push(emptyQuestion())">{{copy.add}}</button>
      <div class="paper-actions"><button v-if="editor.status!=='Published'" type="button" class="button subtle" @click="save(false)">{{copy.save}}</button><button type="button" class="button subtle" @click="showPreview">{{copy.preview}}</button><button class="button primary">{{editor.status==='Published'?copy.update:copy.publish}}</button></div>
      <p class="field-help">{{copy.draftHelp}}</p>
    </fieldset>
  </form>
  <section v-else-if="editor&&preview" class="panel paper-panel">
    <button class="text-button" @click="preview=false">{{copy.backEditor}}</button><h2>{{editor.title||copy.untitled}}</h2><p class="quiz-text">{{editor.instructions}}</p><p class="badge violet">{{copy.teacherPreview}}</p>
    <article v-for="(q,i) in editor.questions" :key="i" class="paper-question"><h3>{{i+1}}. {{q.prompt||copy.incomplete}}</h3><p v-for="(option,j) in q.options" :key="j"><strong>{{'ABCD'[j]}}.</strong> {{option||copy.incomplete}} <span v-if="q.answer===j" class="badge green">{{copy.correct}}</span></p><p v-if="q.answer===null" class="field-help">{{copy.noKey}}</p></article>
  </section>
  <section v-else-if="selected" class="panel paper-panel">
    <button class="text-button" :disabled="busy" @click="back">{{copy.back}}</button><h2>{{selected.title}}</h2><p class="quiz-text">{{selected.instructions}}</p><p>{{selected.questions.length}} {{copy.questions}}</p>
    <template v-if="selected.can_manage">
      <button class="button subtle" :disabled="selected.locked||busy" @click="edit">{{copy.edit}}</button><p v-if="selected.locked" class="field-help">{{copy.locked}}</p>
      <article v-for="(q,i) in selected.questions" :key="i" class="paper-question"><h3>{{i+1}}. {{q.prompt}}</h3><p v-for="(option,j) in q.options" :key="j">{{'ABCD'[j]}}. {{option}} <span v-if="q.answer===j" class="badge green">{{copy.correct}}</span></p></article>
      <h3>{{copy.results}}</h3><p v-if="!results.length">{{copy.noResults}}</p>
      <article v-for="r in results" :key="r.name" class="paper-question"><h4>{{r.student_user}}</h4><p>{{r.score}} / {{r.total}} · {{r.percentage}}% · {{r.submitted_at}}</p><details><summary>{{copy.answers}}</summary><div v-for="(q,i) in JSON.parse(r.snapshot)" :key="i"><p>{{i+1}}. {{q.prompt}}</p><p>{{'ABCD'[JSON.parse(r.answers)[i]]}}. {{q.options[JSON.parse(r.answers)[i]]}} — {{JSON.parse(r.correctness)[i]?copy.correct:copy.incorrect}}</p></div></details></article>
      <div class="paper-actions"><button class="button subtle" :disabled="busy||!resultsPage" @click="resultPage(-1)">{{copy.previous}}</button><button class="button subtle" :disabled="busy||results.length<30" @click="resultPage(1)">{{copy.next}}</button></div>
    </template>
    <div v-else-if="result" role="status"><h3>{{copy.submitted}}</h3><p>{{result.score}} / {{result.total}} · {{result.percentage}}%</p><p>{{copy.oneAttempt}}</p></div>
    <template v-else>
      <p>{{copy.oneAttempt}}</p><p v-if="review" class="form-note">{{copy.reviewHelp}}</p>
      <fieldset v-for="(q,i) in selected.questions" :key="i" class="paper-question" :disabled="busy||review"><legend>{{i+1}}. {{q.prompt}}</legend><label v-for="(option,j) in q.options" :key="j" class="paper-check"><input v-model="answers[i]" type="radio" :name="'quiz-answer-'+i" :value="j">{{'ABCD'[j]}}. {{option}}</label></fieldset>
      <div class="paper-actions"><button v-if="!review" class="button primary" :disabled="busy" @click="reviewAnswers">{{copy.review}}</button><template v-else><button class="button subtle" :disabled="busy" @click="review=false">{{copy.change}}</button><button class="button primary" :disabled="busy" @click="submit">{{copy.submit}}</button></template></div>
    </template>
  </section>
  <template v-else>
    <h3>{{copy.quizzes}}</h3><div class="paper-grid"><article v-for="q in rows" :key="q.name" class="panel paper-panel"><span class="badge violet">{{copy.quiz}} · {{q.status}}</span><h2>{{q.title||copy.untitled}}</h2><p class="quiz-text">{{q.instructions}}</p><p>{{q.question_count}} {{copy.questions}}</p><button class="button subtle" :disabled="busy" @click="open(q)">{{canManage?copy.open:q.submitted?copy.viewResult:copy.start}}</button></article></div>
    <p v-if="!rows.length&&!busy" class="empty-mini">{{copy.empty}}</p>
    <div v-if="rows.length||page" class="paper-actions"><button class="button subtle" :disabled="busy||!page" @click="page--;run(load)">{{copy.previous}}</button><button class="button subtle" :disabled="busy||rows.length<30" @click="page++;run(load)">{{copy.next}}</button></div>
  </template>
</section>
</template>
<style scoped>
.quiz-fields{border:0;padding:0;margin:0;min-width:0}.quiz-text{white-space:pre-wrap;overflow-wrap:anywhere}.paper-question{min-width:0;overflow-wrap:anywhere}.paper-question h3{font-size:16px}.classroom-quizzes :is(input,textarea,select,button,summary):focus-visible{outline:2px solid var(--student-accent,#6c6aee);outline-offset:3px}.classroom-quizzes [aria-invalid=true]{border-color:var(--danger,#b42318)}summary{cursor:pointer}.classroom-quizzes button:disabled{opacity:.55;cursor:not-allowed}
</style>
