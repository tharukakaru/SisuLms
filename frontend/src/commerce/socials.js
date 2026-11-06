export const socialNetworks={linkedin:'LinkedIn',youtube:'YouTube',instagram:'Instagram',facebook:'Facebook',twitter:'X / Twitter',tiktok:'TikTok'}
export function providerSocials(kind,value){
 if(!['Teacher','Institute'].includes(kind))return {}
 try{if(typeof value==='string')value=JSON.parse(value)}catch{return {}}
 if(!value||typeof value!=='object'||Array.isArray(value))return {}
 return Object.fromEntries(Object.keys(socialNetworks).flatMap(key=>{try{const url=new URL(value[key]);return url.protocol==='https:'&&!url.username&&!url.password?[[key,url.href]]:[]}catch{return []}}))
}

// Forms need every supported key even when older profiles store null or JSON null.
export function editableSocials(value){
 try{if(typeof value==='string')value=JSON.parse(value)}catch{value=null}
 const source=value && typeof value==='object' && !Array.isArray(value)?value:{}
 return Object.fromEntries(Object.keys(socialNetworks).map(key=>[key,typeof source[key]==='string'?source[key]:'']))
}
