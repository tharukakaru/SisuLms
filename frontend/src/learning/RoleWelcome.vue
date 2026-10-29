<script setup>
import {computed} from 'vue'
import EducationMotion from './EducationMotion.vue'
const props=defineProps({role:{type:String,default:'Student'}})
const content=computed(()=>({
Student:{title:'Your next chapter starts with you.',items:['Live lessons, replays and all your class materials','Your own study room, milestone countdown and motto','Simple payments, tute delivery and class updates']},
Teacher:{title:'Teach your way. Keep everything together.',items:['Theory, revision and paper classes in one workspace','Schedules, assessments, attendance and student counts','Bank-slip reviews, clear invoices and tuition payouts']},
Admin:{title:'One institute. A thousand possibilities.',items:['Bring your teachers, classrooms and learners together','Track collections and teaching hours across the institute','Manage branding, memberships and owner settlements']},
'Super Admin':{title:'A clear view of the whole platform.',items:['Verify providers and review package payments','Review bank details and confirm tuition settlements','Manage organization access and platform readiness']}
}[props.role==='Institute'?'Admin':props.role]||{title:'Welcome to SISU.',items:[]}))
</script>
<template><section class="role-welcome" aria-live="polite"><EducationMotion/><div :key="role" class="role-features"><span class="eyebrow">{{role==='Admin'?'INSTITUTE':role}} · YOUR SPACE TO GROW</span><h2>{{content.title}}</h2><ul><li v-for="item in content.items" :key="item">{{item}}</li></ul><small>Features depend on your workspace package and permissions.</small></div></section></template>
<style scoped>.role-welcome{display:flex;align-items:center;gap:18px;padding:22px;background:linear-gradient(130deg,#f7f3fc,#fff);border:1px solid #e7ddef;border-radius:20px;margin:20px 0;color:#24162f}.role-welcome>.education-motion{width:170px;flex-shrink:0}.role-features{animation:welcome-in .3s ease}.role-features h2{font-size:22px;line-height:1.3;margin:10px 0}.role-features ul{padding-left:18px;font-size:12px;line-height:1.8}.role-features small{font-size:10px;color:#76677e}@keyframes welcome-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}@media(max-width:600px){.role-welcome{flex-direction:column;gap:4px;padding:18px}.role-welcome>.education-motion{width:150px}.role-features h2{font-size:20px}}@media(prefers-reduced-motion:reduce){.role-features{animation:none}}</style>

