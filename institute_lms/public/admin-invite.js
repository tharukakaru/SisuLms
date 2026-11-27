(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const form=$('invite-form'), status=$('status'), token=new URLSearchParams(location.search).get('token');
  const csrf=document.querySelector('meta[name="csrf-token"]')?.content||'';
  if(document.body.dataset.signedIn==='1'){
    $('title').textContent='Use your own account';
    $('sign-out-continue').addEventListener('click',async()=>{
      const button=$('sign-out-continue');button.disabled=true;button.textContent='Signing out…';
      try{
        const response=await fetch('/api/method/logout',{method:'POST',credentials:'same-origin',headers:{'X-Frappe-CSRF-Token':csrf,Accept:'application/json'}});
        if(!response.ok)throw new Error('Could not sign out. Please try again.');
        location.reload();
      }catch(e){$('session-status').hidden=false;$('session-status').textContent=e.message;button.disabled=false;button.textContent='Sign out and continue invitation';}
    });
    return;
  }
  const passwordDialog=$('password-dialog'), passwordForm=$('password-form');
  let busy=false, verifiedDetails=null;
  function show(text,failure=true){const target=passwordDialog.open?$('password-status'):status;target.textContent=text;target.className=failure?'error':'success';target.hidden=false;target.setAttribute('role',failure?'alert':'status');}
  function closePassword(){if(busy)return;passwordDialog.close();$('verify-code').focus();}
  $('password-close').addEventListener('click',closePassword);
  // Only the X closes this step. Clicking the backdrop or pressing Escape keeps it open.
  passwordDialog.addEventListener('cancel',event=>event.preventDefault());
  const contactDetails=()=>({token,email:$('email').value,phone:$('phone').value,code:$('code').value});
  ['email','phone','code'].forEach(id=>$(id).addEventListener('input',()=>{verifiedDetails=null;$('verify-code').textContent='Verify code';}));
  function serverMessage(data){
    try{const m=JSON.parse(data._server_messages||'[]');if(m.length){const last=typeof m[m.length-1]==='string'?JSON.parse(m[m.length-1]):m[m.length-1];
      return new DOMParser().parseFromString(String(last.message||''),'text/html').body.textContent||'';}}catch(_){}
    return data.exception?'Something went wrong. Please try again.':'';
  }
  async function call(method,params,get=false){
    const url='/api/method/institute_lms.admin_invites.'+method;
    const body=new URLSearchParams(params);
    const r=await fetch(get?url+'?'+body:url,{method:get?'GET':'POST',credentials:'same-origin',
      headers:get?{Accept:'application/json'}:{Accept:'application/json','Content-Type':'application/x-www-form-urlencoded','X-Frappe-CSRF-Token':csrf},body:get?undefined:body});
    let data={};try{data=await r.json()}catch(_){}
    if(!r.ok)throw new Error(serverMessage(data)||'Request failed. Please try again.');
    return data.message;
  }
  async function guard(button,label,fn){if(busy)return;busy=true;const old=button.textContent;button.disabled=true;button.textContent=label;
    try{await fn()}catch(e){show(e.message)}finally{busy=false;button.disabled=false;button.textContent=old}}
  // Live countdown of the remaining link time (server-provided seconds, so the PC clock doesn't matter).
  function startTimer(seconds){
    const box=document.createElement('p');box.className='timer';box.setAttribute('aria-live','off');
    const label=document.createElement('span');label.textContent='Link expires in';
    const clock=document.createElement('strong');box.append(label,clock);$('intro').after(box);
    const end=Date.now()+Number(seconds||0)*1000,pad=n=>String(n).padStart(2,'0');
    const tick=()=>{const left=Math.max(0,Math.round((end-Date.now())/1000));
      const h=Math.floor(left/3600),m=Math.floor(left%3600/60),s=left%60;
      clock.textContent=`${pad(h)}h ${pad(m)}m ${pad(s)}s`;
      box.classList.toggle('urgent',left<3600);
      if(!left){clearInterval(timer);box.classList.add('expired');label.textContent='This link has expired.';clock.textContent='';
        passwordDialog.close();form.hidden=true;verifiedDetails=null;show('Ask an Administrator to send you a new invitation.');}};
    const timer=setInterval(tick,1000);tick();
  }
  if(!token){$('intro').textContent='This page needs the link from your invitation email. Open that link again.';return;}
  call('details',{token},true).then(d=>{
    $('title').textContent='Welcome, '+d.full_name;
    const p=$('intro');p.textContent='You’re invited to join SISU as ';
    const b=document.createElement('span');b.className='badge';b.textContent=d.access_level==='Administrator'?'Administrator · full authority':'Admin';p.append(b);
    p.append('. Confirm your details below to get started.');
    startTimer(d.seconds_left);
    $('email-hint').textContent='Use the email that received the invitation ('+d.email_hint+').';
    form.hidden=Number(d.seconds_left)<=0;
  }).catch(e=>{$('title').textContent='Invitation unavailable';$('intro').textContent=e.message;});
  document.querySelectorAll('[data-password]').forEach(button=>{
    button.addEventListener('click',()=>{
      const input=$(button.dataset.password), visible=input.type==='password';
      input.type=visible?'text':'password';button.textContent=visible?'Hide':'Show';
      button.setAttribute('aria-pressed',String(visible));
      button.setAttribute('aria-label',(visible?'Hide ':'Show ')+(input.id==='confirm'?'confirm password':'password'));
    });
  });
  function passwordFeedback(){
    const password=$('password').value, confirm=$('confirm').value, feedback=$('password-feedback');
    const mismatch=confirm.length>0&&password!==confirm;
    feedback.textContent=mismatch?'Passwords don’t match yet.':confirm.length>0&&password.length>=12?'Passwords match.':'';
    feedback.classList.toggle('error',mismatch);
  }
  $('password').addEventListener('input',passwordFeedback);
  $('confirm').addEventListener('input',passwordFeedback);
  $('send-code').addEventListener('click',()=>{
    const email=$('email'),phone=$('phone');
    if(!email.reportValidity()||!phone.reportValidity())return;
    guard($('send-code'),'Sending…',async()=>{
      const r=await call('send_code',{token,email:email.value,phone:phone.value});
      if(!r.sent)throw new Error('SMS sending was not confirmed. Please try again later.');
      verifiedDetails=null;$('code').value='';$('verify-code').textContent='Verify code';
      show('SMS submitted to '+r.phone_hint+'. Check your phone for the code. It expires in 10 minutes.',false);$('code').focus();
    });
  });
  form.addEventListener('submit',e=>{
    e.preventDefault();
    if(!$('code').value.trim()){show('Enter the 6-digit code from the SMS. No code yet? Press “Send code”.');$('code').focus();return;}
    if(!form.reportValidity())return;
    guard($('verify-code'),'Verifying…',async()=>{
      const details=contactDetails();
      const r=await call('verify_code',details);
      if(r.verified!==true)throw new Error('Mobile verification was not confirmed. Please try again.');
      verifiedDetails=details;status.hidden=true;$('password-status').hidden=true;
      passwordDialog.showModal();$('password').focus();
    }).then(()=>{if(verifiedDetails)$('verify-code').textContent='Continue to password';});
  });
  passwordForm.addEventListener('submit',e=>{
    e.preventDefault();
    if(!verifiedDetails){show('Verify your mobile number before setting a password.');return;}
    if($('password').value.length<12){show('Use a password with at least 12 characters.');$('password').focus();return;}
    if($('password').value!==$('confirm').value){show('The two passwords do not match.');return;}
    if(!passwordForm.reportValidity())return;
    guard($('submit'),'Creating your account…',async()=>{
      const r=await call('accept',{...verifiedDetails,password:$('password').value,confirm:$('confirm').value});
      passwordDialog.close();passwordForm.reset();verifiedDetails=null;form.hidden=true;status.hidden=true;
      const role=r.access_level==='Administrator'?'Administrator (full authority)':'Admin';
      $('welcome-title').textContent='Welcome, '+r.full_name+'!';
      $('welcome-text').textContent='Your SISU LMS '+role+' account is ready. A welcome email has been sent to '+r.email+'.';
      $('welcome').hidden=false;$('welcome-ok').focus();
      loginUrl=r.redirect||'/login?redirect-to=/campus';
    });
  });
  // Both the X and OK buttons (and Escape) take the new admin to the platform sign-in page.
  let loginUrl='/login?redirect-to=/campus';
  const toLogin=()=>{location.href=loginUrl};
  $('welcome-close').addEventListener('click',toLogin);
  $('welcome-ok').addEventListener('click',toLogin);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('welcome').hidden)toLogin()});
})();
