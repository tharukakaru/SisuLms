import {csrf,decode,request} from './client.js'
import {quotaWarning} from './contracts.js'
import {validatePaperUpload} from './paperUploadRules.js'
export {PAPER_ACCEPT,validatePaperUpload} from './paperUploadRules.js'
export async function uploadPaperDocument({classroom,title,description,file,requestId,onProgress}){
  validatePaperUpload(title,file)
  const quota=await request('release','workspace')
  const warning=quotaWarning(file.size,quota.storage);if(warning)throw Error(warning)
  const body=new FormData();body.append('classroom',classroom);body.append('title',title);body.append('description',description);body.append('request_id',requestId);body.append('file',file)
  return new Promise((resolve,reject)=>{
    const xhr=new XMLHttpRequest()
    xhr.open('POST','/api/method/institute_lms.materials.upload_paper')
    xhr.setRequestHeader('X-Frappe-CSRF-Token',csrf())
    xhr.timeout=120000
    xhr.upload.onprogress=e=>{if(e.lengthComputable)onProgress(Math.round(e.loaded/e.total*100))}
    xhr.onerror=()=>reject(Error('Upload failed. Check your connection and retry.'))
    xhr.ontimeout=()=>reject(Error('Upload timed out. Retry to check or complete the same upload.'))
    xhr.onload=async()=>{try{resolve(await decode(new Response(xhr.responseText,{status:xhr.status,headers:{'Content-Type':xhr.getResponseHeader('Content-Type')||''}})))}catch(e){reject(e)}}
    xhr.send(body)
  })
}
