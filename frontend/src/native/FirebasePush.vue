<script setup>
import {onMounted,onUnmounted,ref} from 'vue'
import {request} from './client'
const setup=ref(null),device=ref(''),busy=ref(false),note=ref(''),error=ref(''),validated=ref(false)
let messaging, sdk, unsubscribe, timer, stage='operation'
async function run(fn){busy.value=true;error.value='';try{await fn()}catch(e){const codes=['AbortError','NotAllowedError','SecurityError','TypeError','messaging/unsupported-browser','messaging/token-subscribe-failed','messaging/permission-blocked','installations/request-failed'];const code=codes.includes(e?.code)?e.code:codes.includes(e?.name)?e.name:'request failed';error.value='Failed at '+stage+' ('+code+'). No credentials or tokens are shown.'}finally{busy.value=false}}
onMounted(async()=>{try{setup.value=await request('devices','firebase_config',{},'GET')}catch{setup.value=null}})
onUnmounted(()=>{unsubscribe?.();clearTimeout(timer)})
async function register(){await run(async()=>{
  stage='browser support check'
  if(!window.isSecureContext||!('serviceWorker' in navigator)||!('Notification' in window))throw Error()
  if(await Notification.requestPermission()!=='granted'){note.value='Allow notifications in browser site settings, then try again.';return}
  stage='loading Firebase SDK'
  const base='https://www.gstatic.com/firebasejs/13.0.0/'
  const appSDK=await import(/* @vite-ignore */ base+'firebase-app.js')
  sdk=await import(/* @vite-ignore */ base+'firebase-messaging.js')
  stage='Firebase browser support check'
  if(!await sdk.isSupported())throw Error()
  const app=appSDK.getApps().find(a=>a.name==='sisu-push')||appSDK.initializeApp(setup.value.config,'sisu-push')
  messaging=sdk.getMessaging(app)
  stage='service worker registration'
  const registration=await navigator.serviceWorker.register('/assets/institute_lms/firebase-messaging-sw.js?config='+encodeURIComponent(JSON.stringify(setup.value.config)),{scope:'/assets/institute_lms/'})
  if(!registration.active)await new Promise((resolve,reject)=>{const worker=registration.installing||registration.waiting;if(!worker)return reject();const timeout=setTimeout(reject,20000);worker.addEventListener('statechange',()=>{if(worker.state==='activated'){clearTimeout(timeout);resolve()}else if(worker.state==='redundant'){clearTimeout(timeout);reject()}})})
  // Use existing token-based IL Device Token contract, not installation IDs.
  stage='Firebase push token registration; in Brave check Use Google services for push messaging'
  const token=await sdk.getToken(messaging,{vapidKey:setup.value.vapidKey,serviceWorkerRegistration:registration})
  let id=localStorage.getItem('sisu-firebase-device');if(!id){id=crypto.randomUUID();localStorage.setItem('sisu-firebase-device',id)}
  stage='saving device in SISU'
  const saved=await request('devices','register',{device_id:id,token,platform:'web'})
  device.value=saved.device;validated.value=false
  unsubscribe?.();unsubscribe=sdk.onMessage(messaging,()=>{note.value='Received: your browser push notification is working.'})
  note.value='Browser registered. Next validate with Firebase without sending a notification.'
})}
async function test(dry){stage=dry?'Firebase validation':'sending Firebase test';await run(async()=>{const result=await request('devices','firebase_test',{device:device.value,request_id:crypto.randomUUID(),dry_run:dry});if(dry){validated.value=result.status==='validated';note.value='Firebase validation passed. You can now send a test to this browser.'}else{note.value='Firebase accepted the test. Receipt is confirmed only when the notification appears.'}})}
function background(){note.value='Switch to another tab now. A test will be sent in 10 seconds.';busy.value=true;timer=setTimeout(()=>test(false),10000)}
async function revoke(){stage='revoking browser registration';await run(async()=>{await request('devices','revoke',{device:device.value});device.value='';validated.value=false;await sdk.deleteToken(messaging);unsubscribe?.();note.value='Browser registration revoked.'})}
</script>
<template><section v-if="setup?.available" class="panel"><h2>Browser notifications · sandbox</h2><p>Only your configured test account can use this panel. Customer notifications remain disabled.</p><p v-if="note" role="status">{{note}}</p><p v-if="error" role="alert" class="error">{{error}}</p><button class="button subtle" :disabled="busy" @click="register">Enable this browser</button> <button v-if="device" class="button subtle" :disabled="busy" @click="test(true)">Validate without sending</button> <button v-if="validated" class="button primary" :disabled="busy" @click="test(false)">Send me a test</button> <button v-if="validated" class="button subtle" :disabled="busy" @click="background">Test in background</button> <button v-if="device" class="button subtle" :disabled="busy" @click="revoke">Disable this browser</button></section></template>
