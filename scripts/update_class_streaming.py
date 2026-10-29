from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'frontend/src/App.vue'
s=p.read_text(encoding='utf-8')
s=s.replace("import ClassWelcome from './ClassWelcome.vue'", "import ClassWelcome from './ClassWelcome.vue'\nimport SessionStreamingFields from './SessionStreamingFields.vue'\nimport LessonPlayer from './LessonPlayer.vue'\nimport {sessionStream} from './sessionStreaming.js'")
s=s.replace("if(modal.value==='material'&&", "if(modal.value==='session'){if(form.value.ends_at<=form.value.starts_at)throw Error('End time must be after start time');form.value=sessionStream(form.value)}\n    if(modal.value==='material'&&",1)
start=s.index('<label v-if="form.mode===\'Online\'">Live provider')
end=s.index('<label>Description<textarea',start)
s=s[:start]+'<SessionStreamingFields v-if="form.mode===\'Online\'" :form="form"/>'+s[end:]
start=s.index('<a v-if="m.youtube_id" :href="\'https://www.youtube.com/watch?v=\'')
end=s.index('</a>',start)+4
s=s[:start]+s[end:]
start=s.index('<div v-if="activeVideo" class="video-frame">')
end=s.index('</div>',start)+6
s=s[:start]+'''<LessonPlayer v-if="activeVideo" :video-id="activeVideo" :title="selected.sessions.find(s=>s.youtube_id===activeVideo)?.title||selected.materials.find(m=>m.youtube_id===activeVideo)?.title" @close="activeVideo=''"/>'''+s[end:]
s=s.replace(':href="safeLink(welcomeSession.meeting_url)"', ':href="\'\'"')
s=s.replace('<button v-else-if="safeLink(s.meeting_url)" class="button primary small" @click="welcomeSession=s">Join {{s.meeting_provider}} <Icon name="ArrowUpRight" :size="15"/></button>', '<p v-else-if="s.mode===\'Online\'&&s.meeting_provider!==\'YouTube\'" class="field-help">{{manager?\'Add the YouTube broadcast URL from your \'+s.meeting_provider+\' meeting to enable viewing inside SISU.\':\'Your teacher will connect the classroom stream before this lesson.\'}}</p>')
s=s.replace("v-if=\"manager&&s.youtube_id&&s.mode==='Online'\"", "v-if=\"manager&&s.youtube_id&&s.mode==='Online'&&(!s.meeting_provider||s.meeting_provider==='YouTube')\"")
s=s.replace("s.status==='Completed'?'Watch recording':'Open live class'", "s.status==='Completed'?'Watch recording':'Watch inside classroom'")
s=s.replace("<template v-if=\"detailTab==='Sessions'\"><article", "<template v-if=\"detailTab==='Sessions'\"><div class=\"section-heading\"><div><h2>Live lessons & schedule</h2><p>YouTube, Zoom or Google Meet broadcasts, together in your classroom.</p></div><button v-if=\"manager\" class=\"button primary\" @click=\"edit('session',selected.room)\"><Icon name=\"CalendarPlus\" :size=\"18\"/>Schedule a lesson</button></div><article")
s=s.replace("<p>{{time(s.starts_at)}} – {{time(s.ends_at)}} · {{s.location||'Your online classroom'}}</p>","<p>{{time(s.starts_at)}} – {{time(s.ends_at)}} · Sri Lanka time · {{s.mode==='Online'?(s.meeting_provider||'YouTube'):s.location}}</p>")
s=s.replace('<p class="form-note"><Icon name="MessageCircle" :size="17"/>Students who opted in will receive a WhatsApp update.</p>', '<p class="form-note"><Icon name="CalendarCheck2" :size="17"/>Saved lessons appear in the classroom and My schedule. WhatsApp updates require a connected messaging service and student opt-in.</p>')
s=s.replace("modal==='news'?'Publish update':'Save changes'", "modal==='news'?'Publish update':modal==='session'?'Save class schedule':'Save changes'")
p.write_text(s,encoding='utf-8')
p=root/'frontend/preview.html';s=p.read_text(encoding='utf-8').replace("frame-src 'none'", "frame-src https://www.youtube-nocookie.com https://www.youtube.com");p.write_text(s,encoding='utf-8')
p=root/'frontend/src/preview/PreviewShell.vue';s=p.read_text(encoding='utf-8');s=s.replace("if(u.protocol==='https:'&&u.hostname==='www.youtube.com'&&u.pathname==='/watch'&&/^[\\w-]{11}$/.test(u.searchParams.get('v')||''))return;",'');p.write_text(s,encoding='utf-8')
p=root/'frontend/src/preview/adapter.js';s=p.read_text(encoding='utf-8');s="import {sessionStream} from '../sessionStreaming.js'\n"+s;s=s.replace("row={...v,name:old?.name||id('session'),status:v.status||'Scheduled'}", "row={...sessionStream(v),name:old?.name||id('session'),status:v.status||'Scheduled'}");p.write_text(s,encoding='utf-8')
p=root/'institute_lms/api.py';s=p.read_text(encoding='utf-8');s=s.replace("if doc.meeting_provider!='YouTube':doc.youtube_id=''\n    elif doc.meeting_url:doc.youtube_id=youtube_id(doc.meeting_url)","# Zoom and Meet can broadcast through YouTube into the classroom player.\n    if doc.mode!='Online':doc.youtube_id=''\n    elif doc.meeting_provider=='YouTube' and doc.meeting_url:doc.youtube_id=youtube_id(doc.meeting_url)");p.write_text(s,encoding='utf-8')
