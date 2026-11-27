<script setup>
import {ref,onMounted} from 'vue'
import Icon from '../Icon.vue'
import {request} from './client'
import './student-count.css'
const props=defineProps({instituteTeacher:Boolean})
const data=ref(null),busy=ref(false),error=ref(''),search=ref(''),classroom=ref(''),page=ref(0)
const month=ref(new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Colombo'}).slice(0,7))
async function load(reset=false){if(busy.value)return;if(reset)page.value=0;busy.value=true;error.value='';try{data.value=await request('student_count','students',{month:month.value,classroom:classroom.value,search:search.value,page:page.value},'GET')}catch(e){error.value=e.message}finally{busy.value=false}}
const date=value=>new Date(value.replace(' ','T')+'+05:30').toLocaleString('en-GB',{timeZone:'Asia/Colombo',dateStyle:'medium',timeStyle:'short'})
onMounted(()=>load())
</script>
<template><section class="student-count-space"><header class="page-heading"><div><h1>Students</h1><p>{{instituteTeacher?'Students enrolled in your assigned institute classes.':'Your students, their courses and monthly attendance.'}}</p></div><span class="count-total" v-if="data">{{data.total}} {{data.total===1?'student':'students'}}</span></header>
<form class="count-filters" @submit.prevent="load(true)"><label>Find a student<input v-model="search" type="search" placeholder="Name or student ID"></label><label>Class or course<select v-model="classroom"><option value="">All my classes</option><option v-for="r in data?.rooms||[]" :key="r.name" :value="r.name">{{r.title}}</option></select></label><label>Attendance month<input v-model="month" type="month" required></label><button class="button primary" :disabled="busy">{{busy?'Loading…':'Apply filters'}}</button></form>
<p v-if="error" class="count-error" role="alert">{{error}}</p><p class="count-help">★ marks a recorded attendance. Reconnecting to the same session counts once.</p>
<div class="count-table" v-if="data?.rows.length"><table><thead><tr><th>Student</th><th>Enrolled classes & courses</th><th>Attendance this month</th></tr></thead><tbody><tr v-for="s in data.rows" :key="s.name"><td><strong>{{s.full_name}}</strong><small>{{s.name}}</small></td><td><ul class="count-course-list"><li v-for="c in s.courses" :key="c.name">{{c.title}}<small v-if="c.programme">Programme module</small></li></ul></td><td><span class="count-attendance" :class="{qualified:s.session_count>=2}"><span v-if="s.session_count" aria-hidden="true">★</span> {{s.session_count}} distinct {{s.session_count===1?'session':'sessions'}}</span><details v-if="s.sessions.length"><summary>View attended sessions</summary><ul class="count-session-list"><li v-for="s in s.sessions" :key="s.name"><span aria-hidden="true">★</span> {{s.title}}<small>{{date(s.starts_at)}}</small></li></ul></details><small v-else>No attendance recorded for this month.</small></td></tr></tbody></table></div>
<div v-else-if="data&&!busy" class="count-empty"><Icon name="Users" :size="28"/><h2>No matching students</h2><p>Students appear here when they enroll in a class you manage. Try another course or search.</p></div>
<nav v-if="data&&(page||data.total>50)" class="count-actions" aria-label="Student pages"><button class="button subtle" :disabled="busy||!page" @click="page--;load()">Previous</button><span>Page {{page+1}}</span><button class="button subtle" :disabled="busy||(page+1)*50>=data.total" @click="page++;load()">Next</button></nav></section></template>
