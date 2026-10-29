<script setup>
import {ref,onMounted} from 'vue'
import {request} from './client'
const data=ref(null),email=ref(''),reason=ref(''),busy=ref(false),error=ref(''),note=ref('')
async function load(){data.value=await request('owner_access','access_list',{},'GET')}
async function run(fn){busy.value=true;error.value='';note.value='';try{await fn()}catch(e){error.value=e.message}finally{busy.value=false}}
async function add(){await run(async()=>{const r=await request('owner_access','add',{email:email.value,reason:reason.value});await load();note.value=r.status;email.value=''})}
async function remove(user){if(!window.confirm(`Remove Super Admin access for ${user}? Their user account will remain.`))return;await run(async()=>{const r=await request('owner_access','remove',{email:user,reason:reason.value});await load();note.value=r.status})}
onMounted(()=>run(load))
</script>
<template><section class="panel owner-block"><h2>Super Admin access</h2><p v-if="busy" role="status">Updating access…</p><p v-if="error" role="alert">{{error}}</p><p v-if="note" role="status">{{note}}</p><template v-if="data"><p><strong>Primary owner:</strong> {{data.primary}} · protected</p><p>Each administrator signs in with their own account. Only the primary owner can grant or revoke access.</p><form v-if="data.can_manage" @submit.prevent="add"><label>Email address<input v-model="email" type="email" required autocomplete="off"></label><label>Reason for adding or removing access<textarea v-model="reason" required maxlength="1000"/></label><button class="button primary" :disabled="busy||!reason.trim()">Add Super Admin & send setup email</button></form><article v-for="m in data.members" :key="m.user" class="owner-review"><div><strong>{{m.user}}</strong><p>{{m.enabled?'Active':'Revoked'}}</p></div><button v-if="data.can_manage&&m.enabled" class="button subtle" :disabled="busy||!reason.trim()" @click="remove(m.user)">Remove access</button></article></template></section></template>
