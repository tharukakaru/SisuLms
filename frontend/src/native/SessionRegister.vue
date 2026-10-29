<script setup>
import {ref,watch} from 'vue'
import {request} from './client'
const props=defineProps({session:{type:String,required:true}})
const emit=defineEmits(['saved'])
const rows=ref([]),page=ref(0),more=ref(false),busy=ref(false),error=ref(''),message=ref('')
async function load(){
  busy.value=true;error.value='';message.value='';rows.value=[]
  try{const data=await request('attendance_register','roster',{session:props.session,page:page.value});rows.value=data.rows.map(r=>({...r,status:r.status||''}));more.value=data.has_more}
  catch(e){error.value=e.message}finally{busy.value=false}
}
async function save(){
  busy.value=true;error.value='';message.value=''
  try{await request('attendance_register','submit',{session:props.session,entries:rows.value.map(r=>({student:r.student,status:r.status,note:r.note}))});message.value='Attendance saved. You can edit and submit this register again.';emit('saved')}
  catch(e){error.value=e.message}finally{busy.value=false}
}
async function changePage(delta){page.value+=delta;await load()}
watch(()=>props.session,()=>{page.value=0;load()},{immediate:true})
</script>
<template>
  <form @submit.prevent="save" class="session-register">
    <h3>Session attendance register</h3>
    <p>Mark every student on this page. Saved records stay available for later corrections.</p>
    <p v-if="error" class="error" role="alert">{{error}}</p>
    <p v-if="message" role="status">{{message}}</p>
    <div class="ops-table"><table v-if="rows.length"><thead><tr><th>Student</th><th>Present</th><th>Status</th><th>Note</th></tr></thead>
      <tbody><tr v-for="r in rows" :key="r.student"><td>{{r.full_name}}<br><small>{{r.student}}</small></td>
        <td><input type="checkbox" :aria-label="'Present: '+r.full_name" :checked="r.status==='Present'" :disabled="busy" @change="r.status=$event.target.checked?'Present':'Absent'"></td>
        <td><select v-model="r.status" :disabled="busy" required :aria-label="'Attendance: '+r.full_name"><option disabled value="">Not marked</option><option>Present</option><option>Absent</option><option>Excused</option></select></td>
        <td><input v-model="r.note" :disabled="busy" maxlength="500" :aria-label="'Note: '+r.full_name"></td>
      </tr></tbody></table></div>
    <p v-if="!busy&&!error&&!rows.length">No active enrolled students in this session.</p>
    <button type="submit" class="button primary" :disabled="busy||!rows.length||rows.some(r=>!r.status)">{{busy?'Please wait…':'Submit attendance'}}</button>
    <p v-if="rows.length">Save changes before moving to another page or session.</p>
    <div class="inline"><button type="button" class="button subtle" :disabled="busy||!page" @click="changePage(-1)">Previous students</button><button type="button" class="button subtle" :disabled="busy||!more" @click="changePage(1)">Next students</button></div>
  </form>
</template>
