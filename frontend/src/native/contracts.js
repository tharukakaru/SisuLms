export function object(value) { if (typeof value === 'string') { try { return JSON.parse(value) } catch { return {} } } return value && typeof value === 'object' ? value : {} }
export function errorDetails(data = {}, status = 0) {
  let message = status === 401 ? 'Sign in to continue.' : status === 403 ? 'Access denied. Check your membership and subscription.' : 'The service could not complete this request. Try refreshing or contact your administrator.'
  try { message = JSON.parse(JSON.parse(data._server_messages)[0]).message.replace(/<[^>]*>/g, '') } catch {}
  const code = status === 401 ? 'authentication' : /quota|allowance|capacity|limit|allocation/i.test(message) ? 'quota' : /index|source|evidence/i.test(message) ? 'knowledge' : /provider|configured|OpenAI/i.test(message) ? 'provider' : status === 403 ? 'forbidden' : 'validation'
  return {message, code, status}
}
export function paymentLabel(status) { return ({created:'Created',pending:'Pending — awaiting verified settlement',succeeded:'Paid — verified by server',failed:'Failed',cancelled:'Cancelled'})[status] || 'Processing / review required' }
export function planView(raw = {}) { const s = object(raw); return {...s,features:object(s.features),limits:object(s.limits),overrides:object(s.overrides),state:s.state || 'unavailable'} }
export function sources(result) { return (Array.isArray(result?.sources) ? result.sources : []).filter(s=>s && s.title && s.material).map(s=>({id:s.id,title:s.title,material:s.material,section:s.section,classroom:s.classroom,source_type:s.source_type})) }
export function materialURL(s) { return s?.source_type==='IL Material' && s.material ? '/api/method/institute_lms.materials.content?'+new URLSearchParams({material:s.material,action:'view'}) : null }
export function hostedCheckout(value) { const u=new URL(value); if(u.protocol!=='https:' || u.username || u.password || u.hostname!=='payments.lk' || (u.port&&u.port!=='443') || !/^\/(?:si\/|ta\/)?checkout\/chk_[A-Za-z0-9]+$/.test(u.pathname))throw Error('Unrecognized payment checkout host. Contact your administrator.'); return u.href }
export function quotaWarning(bytes,quota) { return quota && Number(bytes)>Number(quota.remaining) ? 'This file exceeds the remaining organization storage allowance.' : '' }
export function requestIdentity(previous,payload) { const text=JSON.stringify(payload); return previous?.payload===text ? previous : {payload:text,id:crypto.randomUUID()} }
export function apiURL(module,method) { if(!/^[a-z_]+$/.test(module)||!/^[a-z_]+$/.test(method))throw Error('Invalid API method');return `/api/method/institute_lms.${module}.${method}` }
