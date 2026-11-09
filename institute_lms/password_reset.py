"""Email-approved password changes bound to the initiating signed-in session."""
import hashlib,hmac,secrets,time
import frappe

def key(token):
    if not isinstance(token,str) or not 40<=len(token)<=90:frappe.throw('This password reset link is invalid.')
    return 'il_password_change:'+hashlib.sha256(token.encode()).hexdigest()

def session_owner():
    from .campus_context import require_user
    user=require_user()
    return user,hashlib.sha256(str(frappe.session.sid).encode()).hexdigest()

def read(token,owned=False):
    state=frappe.cache.get_value(key(token))
    if not state or state['expires']<=time.time() or state.get('consumed'):frappe.throw('This request expired. Start a new password reset from Settings.')
    if owned:
        user,sid=session_owner()
        if state['user']!=user or not hmac.compare_digest(state['session'],sid):frappe.throw('Continue in the browser where you requested the reset.',frappe.PermissionError)
    return state

def store(token,state):
    frappe.cache.set_value(key(token),state,expires_in_sec=max(1,int(state['expires']-time.time())))

def send_link(user,url):
    from email.message import EmailMessage
    from email.utils import make_msgid
    account=frappe.get_doc('Email Account','SISU Academy')
    if not account.enable_outgoing:frappe.throw('Password email is temporarily unavailable.')
    message=EmailMessage();message['From']='SISU Academy <noreply@sisuacademylk.com>';message['To']=user
    message['Subject']='Confirm your SISU password reset';message['Message-ID']=make_msgid(domain='sisuacademylk.com')
    message.set_content('You requested a new SISU password. Open this link and choose Confirm password reset:\n\n'+url+'\n\nThen return to your original Settings tab to choose your new password. This link expires in 10 minutes. If this was not you, do not confirm it; your password has not changed.')
    mail=frappe.get_doc({'doctype':'Email Queue','sender':message['From'],'email_account':account.name,'message':message.as_string(),'message_id':message['Message-ID'],'status':'Not Sent','recipients':[{'recipient':user,'status':'Not Sent'}]}).insert(ignore_permissions=True)
    frappe.db.commit()
    try:mail.send(force_send=True)
    except Exception:frappe.throw('Email delivery could not be confirmed. Wait before requesting another link.')

@frappe.whitelist(methods=['POST'])
def start():
    user,sid=session_owner()
    from .registration import limit
    limit('self-signup:password-reset:'+user)
    token=secrets.token_urlsafe(36);proof=secrets.token_urlsafe(36)
    state={'user':user,'session':sid,'expires':time.time()+600,'verified':False,'proof':hashlib.sha256(proof.encode()).hexdigest()}
    store(token,state)
    from frappe.utils import get_url
    from urllib.parse import urlsplit
    origin=get_url().rstrip('/')
    if urlsplit(origin).scheme!='https':frappe.throw('Use the secure website to reset your password.')
    send_link(user,origin+'/campus#password-confirm='+token+'.'+proof)
    return {'token':token,'email':user,'expires_in':600}

@frappe.whitelist(allow_guest=True,methods=['POST'])
def confirm(token,proof):
    if not isinstance(proof,str) or len(proof)>90:frappe.throw('Invalid confirmation link.')
    with frappe.cache.lock(key(token),timeout=15):
        state=read(token)
        if not hmac.compare_digest(state['proof'],hashlib.sha256(proof.encode()).hexdigest()):frappe.throw('Invalid confirmation link.',frappe.PermissionError)
        state['verified']=True;store(token,state)
    return {'verified':True}

@frappe.whitelist(methods=['GET'])
def status(token):
    state=read(token,True)
    return {'verified':state['verified'],'expires_in':max(0,int(state['expires']-time.time()))}

@frappe.whitelist(methods=['POST'])
def finish(token,password,confirmation):
    from .signup_rules import password as validate_password
    try:validate_password(password,confirmation)
    except ValueError as exc:frappe.throw(str(exc))
    with frappe.cache.lock(key(token),timeout=30):
        state=read(token,True)
        if not state['verified']:frappe.throw('Confirm the link in your email first.')
        # Consume before writing: a retry after an interrupted response cannot reset again.
        state['consumed']=True;store(token,state)
        from frappe.utils.password import update_password
        update_password(state['user'],password,logout_all_sessions=True)
        from .account_confirmations import queue
        queue(state['user'],'password-change:'+hashlib.sha256(token.encode()).hexdigest(),'Your SISU password was changed','Your SISU password has been changed. If this was not you, reset your password immediately and contact SISU support. Never share your password or verification codes.')
        from frappe.sessions import clear_sessions
        clear_sessions(user=state['user'],keep_current=False,force=True)
    return {'changed':True,'sign_in_required':True}
