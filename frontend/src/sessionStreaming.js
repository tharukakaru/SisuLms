import {youtubeVideoId} from './marketplace.js'
export function streamVideoId(value){
 const text=String(value||'').trim()
 if(!text)return ''
 const id=/^[\w-]{11}$/.test(text)?text:youtubeVideoId(text)
 if(!id)throw Error('Use a valid YouTube video or broadcast URL, or its 11-character video ID.')
 return id
}
export function sessionStream(data){
 const result={...data}
 if(result.mode==='Physical'){result.youtube_id='';result.meeting_url='';return result}
 result.meeting_provider ||= 'YouTube'
 if(!['YouTube','Zoom','Google Meet'].includes(result.meeting_provider))throw Error('Choose YouTube, Zoom or Google Meet.')
 result.youtube_id=streamVideoId(result.youtube_id)
 if(result.meeting_url){
  const u=new URL(result.meeting_url),host=u.hostname
  const allowed=result.meeting_provider==='Zoom'?['zoom.us','zoom.com'].some(d=>host===d||host.endsWith('.'+d)):result.meeting_provider==='Google Meet'?host==='meet.google.com':['youtube.com','www.youtube.com','youtu.be'].includes(host)
  if(u.protocol!=='https:'||u.username||u.password||(u.port&&u.port!=='443')||!allowed)throw Error('Use an HTTPS meeting link from the selected provider.')
 }
 return result
}
