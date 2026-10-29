import {apiURL,errorDetails} from './contracts'
export function csrf(){return window.csrf_token || document.querySelector('meta[name="csrf-token"]')?.content || ''}
export async function decode(response){
  if (!response.headers.get('content-type')?.includes('application/json')) throw Error('The Frappe service returned an unexpected response. Check your connection or sign in again.')
  const data=await response.json()
  if(!response.ok || data.exc || data.exc_type){const detail=errorDetails(data,response.status);throw Object.assign(Error(detail.message),detail)}
  return data.message
}
export async function upload(module,method,body){return decode(await fetch(apiURL(module,method),{method:'POST',credentials:'same-origin',body,headers:{'X-Frappe-CSRF-Token':csrf()}}))}
export async function request(module, method, args = {}, verb = 'POST') {
  const url = apiURL(module,method)
  const response = await fetch(url + (verb === 'GET' ? '?' + new URLSearchParams(args) : ''), {
    method: verb, credentials: 'same-origin', cache: 'no-store',
    headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf() },
    ...(verb === 'POST' ? { body: JSON.stringify(args) } : {}),
  })
  return decode(response)
}
