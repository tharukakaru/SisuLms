<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
import InstituteRegistration from './InstituteRegistration.vue'
import DemoLesson from './DemoLesson.vue'
const demoClass=ref(null)
import ProfileEditor from '../commerce/ProfileEditor.vue'
import MobileVerification from './MobileVerification.vue'
import InstituteJoinPicker from './InstituteJoinPicker.vue'
import TeacherSetup from './TeacherSetup.vue'
const joinPurpose=ref('')
const props=defineProps({session:{type:Object,required:true},embedded:Boolean,instituteScope:Boolean,section:{type:String,default:'discover'}})
const profileVersion=ref(0)

const tab=ref(props.section),query=ref(''),providers=ref([]),news=ref([]),classes=ref([]),busy=ref(false),error=ref(''),selected=ref(null),following=ref({}),saving=ref('')
async function load(){
 if(!props.embedded&&props.session.onboarding_kind==='Teacher')return
 if(busy.value)return
 busy.value=true;error.value=''
 try{
  if(tab.value==='profile')return
  if(tab.value==='discover'){
   const rows=await request(props.instituteScope?'campus_join':'profiles',props.instituteScope?'people':'search',{query:query.value},'GET')
   const links=await request('profiles','follow_status',{profiles:JSON.stringify(rows.map(p=>p.name))},'GET')
   providers.value=rows;following.value=Object.fromEntries(links.map(r=>[r.profile,r.name]))
  }
  else if(tab.value==='news')news.value=await request('profiles','followed_updates',{},'GET')
  else classes.value=await request('profiles','followed_classes',{},'GET')
 }catch(e){error.value=e.message}finally{busy.value=false}
}
function choose(value){if(busy.value)return;tab.value=value;load()}
async function follow(p){
 if(saving.value)return
 saving.value=p.name;error.value=''
 try{
  const relationship=following.value[p.name]
  if(relationship){await request('profiles','change_relationship',{relationship,status:'Left'});const next={...following.value};delete next[p.name];following.value=next}
  else {const result=await request('profiles','relate',{profile:p.name,kind:'Follow'});following.value={...following.value,[p.name]:result.name}}
 }catch(e){error.value=e.message}finally{saving.value=''}
}
onMounted(load)
</script>
<template>
<TeacherSetup v-if="!embedded&&session.onboarding_kind==='Teacher'"/><template v-else><DemoLesson v-if="demoClass" :classroom="demoClass" @close="demoClass=null" @unlocked="load"/><main class="general-campus" :class="{embedded}">
<aside v-if="!embedded" class="campus-sidebar"><a class="campus-brand" href="/">sisu.</a><p>Your learning space</p><nav aria-label="Dashboard"><button v-for="item in [['discover','Teachers & institutes'],['classes','My classes'],['news','News'],['profile','My profile']]" :key="item[0]" :aria-pressed="tab===item[0]" :disabled="busy" @click="choose(item[0])">{{item[1]}}</button></nav><a href="/api/method/logout">Sign out</a></aside><div class="campus-content">
<header v-if="!embedded"><span>YOUR LEARNING SPACE</span><h1>{{session.onboarding_kind==='Teacher'?'Your teaching community':'My SISU'}}</h1><p>{{session.onboarding_kind==='Teacher'?'Open your teaching workspace above, or find an institute to teach with.':'Discover your next class and stay connected with the people you learn from.'}}</p></header>
<section v-if="session.onboarding_kind==='Teacher'" class="teacher-join"><h2>Teach with your institute</h2><p>Request to join an institute. Its administrator must approve you before you can use its teaching workspace.</p><div class="actions"><button @click="joinPurpose='Existing teacher confirmation'">I already teach at an institute</button><button @click="joinPurpose='New application'">Apply to an institute</button></div><InstituteJoinPicker v-if="joinPurpose" :key="joinPurpose" :purpose="joinPurpose" @back="joinPurpose=''"/></section>
<nav class="legacy-tabs" aria-label="My SISU sections"><button v-for="item in [['discover','Teachers & institutes'],['classes','My classes'],['news','News'],['profile','My profile']]" :key="item[0]" :aria-pressed="tab===item[0]" :disabled="busy" @click="choose(item[0])">{{item[1]}}</button></nav>
<p v-if="busy" role="status">Loading your space…</p><div v-if="error" role="alert"><p>{{error}}</p><button :disabled="busy" @click="load">Try again</button></div>
<section v-if="tab==='discover'"><form @submit.prevent="load"><label for="provider-search">Find teachers and institutes</label><div class="search"><input id="provider-search" v-model="query" maxlength="80" placeholder="Search by name"><button :disabled="busy">Search</button></div></form><p>{{instituteScope?'Teachers and student profiles in your selected institute.':'Follow for news and free classes. Register separately to join a provider.'}}</p><div class="cards"><article v-for="p in providers" :key="p.name"><small>{{p.kind}}</small><h2>{{p.display_name}}</h2><p>{{p.tagline||p.bio}}</p><div class="actions"><button v-if="p.kind!=='Student'" :disabled="!!saving" :aria-pressed="!!following[p.name]" @click="follow(p)">{{following[p.name]?'Following':saving===p.name?'Following…':'Follow'}}</button><button v-if="session.onboarding_kind!=='Teacher'&&(p.kind==='Institute'||p.independent)" @click="selected=p">Register now →</button></div></article></div><div v-if="!busy&&!error&&!providers.length" class="friendly-empty"><span aria-hidden="true">◇</span><h3>{{query?'No matches just yet':'Your learning community starts here'}}</h3><p>{{query?'Try another name or clear your search.':'Teachers and institutes will appear here when their profiles are published. Come back soon to find your next learning space.'}}</p></div></section>
<section v-else-if="tab==='news'"><h2>From the people you follow</h2><article v-for="n in news" :key="n.name"><small>{{n.display_name}}</small><h3>{{n.headline}}</h3><p>{{n.body}}</p></article><div v-if="!busy&&!error&&!news.length" class="friendly-empty"><span aria-hidden="true">✧</span><h3>A little quiet, for now</h3><p>Their latest updates will appear here after you follow them.</p></div></section>
<section v-else-if="tab==='profile'"><h2>My account</h2><p>You can explore SISU without joining an institute. Verify your phone and complete your profile when you are ready to follow providers or register.</p><ProfileEditor :member="{user:session.user,full_name:session.user,role:session.onboarding_kind==='Institute'?'Admin':session.onboarding_kind||'Student'}"/><a href="/api/method/logout">Sign out</a></section>
<section v-else><h2>Classes from your follows</h2><p>Institute classes you have enrolled in are also available in that institute’s workspace.</p><div class="cards"><article v-for="c in classes" :key="c.name"><small>{{c.fee_mode==='Free'?'Free':'Locked'}} · {{c.provider_name}}</small><h3>{{c.title}}</h3><p>{{c.subject}}</p><span v-if="c.demo" class="demo-badge">{{c.unlocked?'Unlocked demo':'Locked demo'}}</span><button v-if="c.demo" class="button primary" @click="demoClass=c">{{c.unlocked?'Open demo lesson':'Enter enrollment key'}}</button><p v-else>Register with this provider and open its workspace to enroll. Following does not unlock paid classes.</p></article></div><div v-if="!busy&&!error&&!classes.length" class="friendly-empty"><span aria-hidden="true">▱</span><h3>Your next class is waiting to be discovered</h3><p>Follow a teacher or institute to discover their published free classes here.</p></div></section>
<InstituteRegistration v-if="selected" :institute="selected" @close="selected=null"/>
</div></main></template>
</template>
<style scoped>.demo-badge{display:block;margin:12px 0;color:#633491;font-size:13px;font-weight:700}.friendly-empty{min-height:230px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:32px;border:1px dashed #dcd4e9;border-radius:22px;background:linear-gradient(135deg,#f5f2fb99,#fff9);margin:24px 0;color:#746784}.friendly-empty>span{font-size:60px;opacity:.25}.friendly-empty h3{font-size:20px;color:#574668}.friendly-empty p{max-width:480px}.search input::placeholder{font-size:13px;color:#8a7f97}.general-campus .search input{padding-inline:20px}
.general-campus{max-width:1150px;margin:32px auto;padding:24px;color:#38284a;font-family:Manrope,system-ui,sans-serif}.general-campus header span{font-size:12px;letter-spacing:.12em}.general-campus h1{font-size:38px;margin:10px 0}.general-campus p{line-height:1.7}.general-campus nav,.actions,.search{display:flex;gap:14px;flex-wrap:wrap}.general-campus nav{margin:28px 0}.general-campus button{padding:12px 18px;border:1px solid #d8cfe7;border-radius:12px;background:white;color:#502785;font:inherit;cursor:pointer}.general-campus button[aria-pressed=true]{background:#56288d;color:white}.general-campus button:disabled{opacity:.6;cursor:default}.general-campus input{flex:1;min-width:170px;padding:14px;border:1px solid #d8cfe7;border-radius:12px;font:inherit}.general-campus label{display:block;margin-bottom:10px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(290px,100%),1fr));gap:20px}.general-campus article{padding:24px;border:1px solid #e5ddef;border-radius:18px;margin:16px 0;background:white}.general-campus h2{font-size:23px}.actions{margin-top:18px}
.general-campus{display:grid;grid-template-columns:230px minmax(0,1fr);max-width:1440px;gap:36px;margin:0 auto;min-height:100vh;background:#faf9fe}.campus-sidebar{padding:24px 14px;border-right:1px solid #e5ddef}.campus-brand{font-size:38px;font-weight:800;color:#56288d;text-decoration:none}.general-campus .campus-sidebar nav{display:grid;gap:10px}.general-campus .campus-sidebar button{width:100%;text-align:left}.general-campus .legacy-tabs{display:none}.campus-content{min-width:0;padding:24px 8px}.general-campus .search button,.general-campus .actions button{width:auto}.general-campus header{margin-bottom:32px}.general-campus header p{color:#6d627c}@media(max-width:760px){.general-campus{grid-template-columns:1fr;gap:0;padding:16px}.campus-sidebar{border-right:0;border-bottom:1px solid #e5ddef;padding:8px}.general-campus .campus-sidebar nav{grid-template-columns:repeat(2,minmax(0,1fr));margin:16px 0}.campus-content{padding:24px 0}.general-campus h1{font-size:30px}}
.general-campus.embedded{display:block;min-height:0;padding:0;margin:0;background:transparent;max-width:none}.embedded .campus-content{padding:0}</style>
