(() => {
  'use strict';
  const form=document.getElementById('password-form'), button=document.getElementById('submit'), status=document.getElementById('status');
  const key=new URLSearchParams(window.location.search).get('key');
  let busy=false;
  function show(text,failure=true){status.textContent=text;status.className=failure?'error':'success';status.hidden=false;status.setAttribute('role',failure?'alert':'status');}
  function serverMessage(data){
    try{
      const messages=JSON.parse(data._server_messages||'[]');
      if(messages.length){const last=typeof messages[messages.length-1]==='string'?JSON.parse(messages[messages.length-1]):messages[messages.length-1];
        const doc=new DOMParser().parseFromString(String(last.message||''),'text/html');return doc.body.textContent||'';}
    }catch(_){}
    if(typeof data.message==='string'&&!data.message.startsWith('/'))return data.message;
    return '';
  }
  if(!key){show('This page needs the link from your latest invitation email. Open that link again.');form.hidden=true;return;}
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(busy)return;
    const password=document.getElementById('password'), confirmation=document.getElementById('confirmation');
    if(password.value!==confirmation.value){show('The passwords do not match. Please enter them again.');return;}
    if(!form.reportValidity())return;
    busy=true;button.disabled=true;button.textContent='Saving password…';status.hidden=true;
    try{
      const response=await fetch('/api/method/frappe.core.doctype.user.user.update_password',{
        method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},
        body:JSON.stringify({new_password:password.value,key,logout_all_sessions:1})
      });
      if(!response.headers.get('content-type')?.includes('application/json'))throw Error('The server returned an unexpected response. Your password change is not confirmed. Please try again.');
      const data=await response.json();
      if(!response.ok||data.exc||data.exc_type){
        const detail=serverMessage(data);
        throw Error(detail||(response.status===410?'This invitation has expired or was replaced. Ask for a fresh invitation and use its newest link.':response.status===403?'The request was rejected. Reopen the latest invitation in a private window and try again.':'The password could not be saved. Please try again.'));
      }
      // Native Frappe returns a redirect path only after updating the password.
      if(typeof data.message!=='string'||!data.message.trim())throw Error(serverMessage(data)||'The server did not confirm the password change.');
      password.value='';confirmation.value='';form.hidden=true;
      show('Your password was saved. Continue to your dashboard. If asked to sign in, use the email that received this invitation and your new password.',false);
      document.getElementById('continue').hidden=false;
      history.replaceState(null,'','/sisu_password');
    }catch(e){show(e.message||'Connection failed. Your password change is not confirmed.');}
    finally{busy=false;button.disabled=false;button.textContent='Set password';}
  });
})();
