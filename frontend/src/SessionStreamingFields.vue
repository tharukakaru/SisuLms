<script setup>
import Icon from './Icon.vue'
import {ref} from 'vue'
import {request} from './native/client'
const props=defineProps({form:Object}),zoomBusy=ref(false),zoomNotice=ref('')
async function createZoom(){zoomBusy.value=true;zoomNotice.value='';try{const r=await request('workspace','create_zoom_session',{session:props.form.name});if(r.meeting_url)props.form.meeting_url=r.meeting_url;zoomNotice.value=r.preview?'Preview only: no Zoom meeting was created.':'Zoom meeting created with a waiting room and passcode.'}catch(e){zoomNotice.value=e.message}finally{zoomBusy.value=false}}
const providers=[{name:'YouTube',icon:'Play',text:'Broadcast straight to your classroom'},{name:'Zoom',icon:'Video',text:'Teach in Zoom · stream into SISU'},{name:'Google Meet',icon:'Monitor',text:'Teach in Meet · stream into SISU'}]
</script>
<template>
  <section class="stream-settings" aria-label="Class streaming setup">
    <div class="stream-heading"><span class="stat-icon violet"><Icon name="Radio"/></span><div><h3>One class. All together.</h3><p>Choose where you teach. Students watch here in SISU.</p></div></div>
    <div class="stream-providers" role="group" aria-label="Teaching platform">
      <button v-for="p in providers" :key="p.name" type="button" :aria-pressed="form.meeting_provider===p.name" :class="{chosen:form.meeting_provider===p.name}" @click="form.meeting_provider=p.name;form.meeting_url=''">
        <Icon :name="p.icon" :size="22"/><strong>{{p.name}}</strong><small>{{p.text}}</small>
      </button>
    </div>
<div v-if="form.meeting_provider==='Zoom'" class="stream-note"><div><button type="button" class="button subtle" :disabled="!form.name||zoomBusy||!!form.meeting_url" @click="createZoom">Create protected Zoom meeting</button><p>{{form.name?'Uses your connected Zoom host account. Waiting room and passcode are enabled.':'Save this session first, then reopen it to create the Zoom meeting.'}}</p><p v-if="zoomNotice" role="status">{{zoomNotice}}</p></div></div>
    <label v-if="form.meeting_provider!=='YouTube'">{{form.meeting_provider}} host meeting link · optional<input v-model="form.meeting_url" type="url" :placeholder="form.meeting_provider==='Zoom'?'https://us02web.zoom.us/j/…':'https://meet.google.com/…'"><small>For your teaching setup. Students use the classroom player.</small></label>
    <label>{{form.meeting_provider==='YouTube'?'YouTube live or recorded lesson URL':'YouTube broadcast URL from '+form.meeting_provider}}<input v-model="form.youtube_id" placeholder="https://www.youtube.com/watch?v=…"><small>You can save the schedule now and add the broadcast before class.</small></label>
    <div class="stream-note"><Icon name="MonitorPlay" :size="20"/><p>Students watch the video inside this classroom. Use a public or unlisted video with embedding enabled. Unlisted links can still be shared outside SISU.</p></div>
    <details v-if="form.meeting_provider!=='YouTube'"><summary>Set up {{form.meeting_provider}} streaming</summary><ol><li>Create your meeting in {{form.meeting_provider}}.</li><li>Enable YouTube live streaming on the host account and connect your channel.</li><li>Copy the YouTube broadcast URL into the field above.</li><li>At class time, start the meeting and its YouTube broadcast.</li></ol><p>Your {{form.meeting_provider}} plan and administrator must allow streaming. This is a broadcast: students watch in SISU; their cameras and microphones do not join the host meeting. Saving this schedule does not create or start a provider meeting.</p></details>
  </section>
</template>
<style scoped>
.stream-settings{border:1px solid #e6ddf1;border-radius:18px;padding:22px;margin:20px 0;background:linear-gradient(130deg,#fbf8ff,#fff 70%)}.stream-heading{display:flex;align-items:center;gap:14px;margin-bottom:20px}.stream-heading h3{margin:0 0 6px;font-size:19px}.stream-heading p,.stream-note p{margin:0;font-size:13px;line-height:1.6}.stream-providers{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px}.stream-providers button{display:flex;flex-direction:column;align-items:flex-start;gap:10px;text-align:left;border:1px solid #ded6e8;border-radius:12px;background:white;padding:16px;color:inherit;cursor:pointer}.stream-providers button.chosen{border-color:#54218a;box-shadow:0 0 0 1px #54218a;background:#f5effc;color:#54218a}.stream-providers small{font-size:11px;line-height:1.5}.stream-note{display:flex;gap:12px;padding:14px;background:#f1ebf8;border-radius:10px;color:#543d70}.stream-note svg{flex-shrink:0}.stream-settings details{margin-top:18px;font-size:13px;line-height:1.8}.stream-settings summary{cursor:pointer;color:#54218a;font-weight:650}.stream-settings label{margin-top:18px}.stream-settings label small{display:block;position:static;font-size:12px;line-height:1.6;margin-top:7px}@media(max-width:600px){.stream-providers{grid-template-columns:1fr}.stream-providers button{gap:5px}.stream-settings{padding:15px}}
</style>
