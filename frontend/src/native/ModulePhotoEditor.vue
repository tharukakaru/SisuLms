<script setup>
import {ref,onBeforeUnmount} from 'vue'
import {request,upload} from './client'
const props=defineProps({room:Object}),emit=defineEmits(['saved'])
const dialog=ref(null),busy=ref(false),error=ref(''),files=ref({}),previews=ref({})
const fields=[{key:'profile_image',label:'Profile photo'},{key:'cover_image',label:'Cover image'}]
function reset(){Object.values(previews.value).forEach(URL.revokeObjectURL);previews.value={};files.value={};error.value=''}
function open(){reset();dialog.value.showModal()}
function close(){if(!busy.value)dialog.value.close()}
function choose(event,key){const file=event.target.files?.[0];if(!file)return;if(!['image/jpeg','image/png'].includes(file.type)){error.value='Choose a PNG or JPEG image.';return}if(previews.value[key])URL.revokeObjectURL(previews.value[key]);files.value[key]=file;previews.value[key]=URL.createObjectURL(file);error.value=''}
async function save(){busy.value=true;error.value='';try{const images={};for(const [kind,file] of Object.entries(files.value)){const body=new FormData();body.append('file',file);body.append('kind',kind);body.append('classroom',props.room.name);images[kind]=(await upload('programme_certificates','upload',body)).url}const saved=await request('programme_courses','module_images',{classroom:props.room.name,images});emit('saved',saved);dialog.value.close();reset()}catch(e){error.value=e.message||'Could not save photos. Please try again.'}finally{busy.value=false}}
onBeforeUnmount(reset)
</script>
<template>
<button class="button subtle photo-edit" type="button" @click.stop="open">Edit photos</button>
<Teleport to="body"><dialog ref="dialog" class="photo-dialog" aria-labelledby="photo-editor-title" @click.stop @keydown.stop @cancel="busy&&$event.preventDefault()">
<h2 id="photo-editor-title">Edit classroom photos</h2><p>Choose your photos, then save to update this classroom.</p>
<div class="photo-fields"><label v-for="field in fields" :key="field.key">{{field.label}}<img v-if="previews[field.key]||room[field.key]" :src="previews[field.key]||room[field.key]" :alt="field.label" :class="field.key"><input type="file" accept="image/png,image/jpeg" :disabled="busy" @change="choose($event,field.key)"></label></div>
<p v-if="error" role="alert" class="photo-error">{{error}}</p><footer><button type="button" class="button subtle" :disabled="busy" @click="close">Cancel</button><button type="button" class="button primary" :disabled="busy||!Object.keys(files).length" @click="save">{{busy?'Saving…':'Save photos'}}</button></footer>
</dialog></Teleport>
</template>
<style scoped>
.photo-edit{margin-bottom:12px}.photo-dialog{width:min(520px,calc(100vw - 32px));max-height:85vh;overflow:auto;border:1px solid #e7e0ef;border-radius:20px;padding:24px;color:#252035;background:white;margin:auto;box-shadow:0 20px 80px #20152f44}.photo-dialog::backdrop{background:#21152c80}.photo-dialog h2{font-size:22px;margin:0 0 10px}.photo-dialog p{line-height:1.5;margin-bottom:18px}.photo-fields{display:grid;gap:20px}.photo-fields label{display:grid;gap:10px;font-weight:600}.photo-fields img{width:100%;height:120px;object-fit:cover;border-radius:12px}.photo-fields img.profile_image{width:88px;height:88px;border-radius:50%}.photo-fields input{width:100%;font-size:14px}.photo-dialog footer{display:flex;justify-content:flex-end;gap:12px;margin-top:24px}.photo-error{color:#a42135}
</style>
