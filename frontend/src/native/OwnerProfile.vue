<script setup>
import {computed, reactive, ref, onBeforeUnmount} from 'vue'
import Icon from '../Icon.vue'
import {request} from './client'
const props=defineProps({profile:Object})
const fields=reactive({current_password:'',new_password:'',confirm_password:''})
const visible=reactive({current_password:false,new_password:false,confirm_password:false})
const busy=ref(false),error=ref(''),changed=ref(false)
const inputs=[{key:'current_password',label:'Current password',autocomplete:'current-password'},
  {key:'new_password',label:'New password',autocomplete:'new-password'},
  {key:'confirm_password',label:'Confirm new password',autocomplete:'new-password'}]
const role=computed(()=>({Primary:'Primary owner',Administrator:'Administrator',Admin:'Admin'})[props.profile?.level]||'Administrator')
const matches=computed(()=>fields.confirm_password && fields.new_password===fields.confirm_password)
function clear(){Object.keys(fields).forEach(key=>{fields[key]='';visible[key]=false})}
async function save(){
 if(busy.value)return
 error.value=''
 if(fields.new_password!==fields.confirm_password){error.value='The new passwords do not match.';return}
 busy.value=true
 try{await request('admin_profile','change_password',{...fields});clear();changed.value=true}
 catch(e){error.value=e.message;fields.current_password='';visible.current_password=false}
 finally{busy.value=false}
}
onBeforeUnmount(clear)
</script>
<template>
<div class="admin-profile">
 <section class="profile-identity" aria-labelledby="profile-details-title">
  <h2 id="profile-details-title">Your account</h2>
  <p v-if="!profile" role="status">Loading your profile…</p>
  <template v-else>
   <div class="profile-person"><span class="profile-avatar"><Icon name="UserRound" :size="26"/></span><div><h3>{{profile.name}}</h3><p>{{role}}</p></div></div>
   <dl><div><dt>Email address</dt><dd>{{profile.email}}</dd></div><div><dt>Mobile number</dt><dd>{{profile.phone_hint||'Not registered'}}</dd></div><div><dt>Sign-in protection</dt><dd><Icon name="ShieldCheck" :size="17"/>{{profile.sms_mfa?'Password + SMS verification':'Password sign-in'}}</dd></div></dl>
   <p class="profile-help">These details belong to your signed-in administrator account.</p>
  </template>
 </section>
 <section class="profile-password" aria-labelledby="password-title">
  <h2 id="password-title">Change password</h2>
  <template v-if="changed"><div class="password-success" role="status"><Icon name="CircleCheck"/><div><h3>Password changed</h3><p>You’ve been signed out on all devices. Sign in again with your new password{{profile?.sms_mfa?' and SMS code':''}}.</p></div></div><a class="button primary" href="/login?redirect-to=/campus">Back to sign in <Icon name="ArrowRight" :size="17"/></a></template>
  <form v-else @submit.prevent="save">
   <p>Use at least 12 characters. A longer, unique phrase makes a stronger password.</p>
   <div v-for="field in inputs" :key="field.key" class="profile-field">
    <label :for="'admin-'+field.key">{{field.label}}</label>
    <div class="password-control"><input :id="'admin-'+field.key" v-model="fields[field.key]" :type="visible[field.key]?'text':'password'" :autocomplete="field.autocomplete" :minlength="field.key==='current_password'?undefined:12" maxlength="128" required :disabled="busy" :aria-describedby="field.key==='confirm_password'&&fields.confirm_password?'password-match':undefined"/><button type="button" :aria-controls="'admin-'+field.key" :aria-label="(visible[field.key]?'Hide ':'Show ')+field.label.toLowerCase()" :aria-pressed="visible[field.key]" :disabled="busy" @click="visible[field.key]=!visible[field.key]">{{visible[field.key]?'Hide':'Show'}}</button></div>
   </div>
   <p v-if="fields.confirm_password" id="password-match" :class="matches?'match-ok':'match-error'" aria-live="polite">{{matches?'New passwords match.':'New passwords do not match yet.'}}</p>
   <p v-if="error" class="password-error" role="alert">{{error}}</p>
   <div class="password-actions"><button class="button primary" :disabled="busy">{{busy?'Updating password…':'Update password'}}<Icon name="ArrowRight" :size="17"/></button><button type="button" class="button subtle" :disabled="busy" @click="clear();error=''">Clear</button></div>
   <p class="profile-help"><Icon name="LockKeyhole" :size="16"/>Changing your password signs you out on all devices.</p>
  </form>
 </section>
</div>
</template>
<style scoped>
.admin-profile{display:grid;grid-template-columns:minmax(220px,1fr) minmax(300px,1.4fr);gap:56px;max-width:1060px;padding:28px 0}.admin-profile h2{margin:0 0 20px}.profile-person{display:flex;gap:14px;align-items:center;margin:28px 0}.profile-person h3{margin:0;overflow-wrap:anywhere}.profile-person p{margin:4px 0 0;color:var(--muted)}.profile-avatar{width:52px;height:52px;border-radius:12px;background:#eee6f7;color:#592c91;display:grid;place-items:center;flex-shrink:0}.profile-identity dl{margin:0}.profile-identity dl>div{padding:16px 0;border-bottom:1px solid var(--line)}.profile-identity dt{font-size:12px;color:var(--muted);margin-bottom:6px}.profile-identity dd{margin:0;display:flex;align-items:center;gap:7px;overflow-wrap:anywhere;word-break:break-word}.profile-password{border-left:1px solid var(--line);padding-left:40px}.profile-password form>p:first-child{color:var(--muted);margin:0 0 24px;max-width:54ch}.profile-field{margin:20px 0}.profile-field label{display:block;font-weight:600;font-size:13px;margin:0 0 8px}.password-control{display:flex;align-items:center;background:white;border:1px solid #cbbbdc;border-radius:9px;overflow:hidden}.password-control:focus-within{outline:2px solid #592c91;outline-offset:3px}.password-control input{flex:1;width:100%;min-width:0;border:0;outline:0;background:transparent;padding:12px;color:var(--ink);font:inherit}.password-control button{align-self:stretch;min-width:62px;padding:0 12px;border:0;border-left:1px solid var(--line);background:#f5f0fa;color:#54258a;cursor:pointer;font:inherit;font-size:12px;font-weight:700}.password-control button:focus-visible{outline:2px solid #592c91;outline-offset:-4px}.password-control button:hover{background:#ece3f5}.password-control button:disabled{opacity:.6;cursor:wait}.password-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.password-actions .button,.profile-password>a{display:inline-flex;gap:14px;align-items:center;justify-content:center}.admin-profile .profile-help{font-size:12px;color:var(--muted);line-height:1.65;margin-top:20px;display:flex;gap:8px;align-items:flex-start}.profile-help svg{flex-shrink:0;margin-top:2px}.match-ok{color:#21613f;font-size:13px}.match-error{color:#a1263b;font-size:13px}.password-error{padding:12px 16px;background:#fff1f3;color:#922439;border-radius:8px}.password-success{display:flex;gap:14px;padding:20px;background:#eef7f2;color:#21613f;border-radius:12px;margin-bottom:24px}.password-success svg{flex-shrink:0}.password-success h3{margin:0 0 8px}.password-success p{margin:0}@media(max-width:960px){.admin-profile{grid-template-columns:1fr;gap:32px;max-width:620px}.profile-password{border-left:0;border-top:1px solid var(--line);padding:28px 0 0}}@media(max-width:480px){.password-actions .primary{flex:1}.admin-profile{padding-top:20px}}
</style>
