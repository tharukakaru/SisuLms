"""Opt-in sandbox self signup; immutable contact proofs, no client-selected roles."""
import hashlib
import hmac
import json
import secrets
import time
import frappe
from . import signup_rules as rules


def enabled():
    return frappe.local.site=='hnb-checkout.localhost' and frappe.conf.get('il_self_signup_enabled')==1


def require_ready():
    if not enabled() or not frappe.conf.get('encryption_key'):
        frappe.throw('Self signup is not enabled on this sandbox.')
    from frappe.utils import get_url
    from urllib.parse import urlparse
    origin=urlparse(get_url())
    if origin.scheme!='https' and origin.hostname not in ('localhost','127.0.0.1','hnb-checkout.localhost'):
        frappe.throw('Use HTTPS or the local sandbox address.')
    from .api import institute
    institute()  # Fail before OTP delivery if no isolated workspace exists.
    if not frappe.conf.get('il_self_signup_test_email') or not frappe.conf.get('il_self_signup_test_phone'):
        frappe.throw('Configure the approved sandbox test contacts first.')


def test_contact(data):
    expected=(frappe.conf.get('il_self_signup_role_emails') or {}).get(data['kind'])
    if not expected and data['kind']=='Student':expected=frappe.conf.get('il_self_signup_test_email')
    return data['email']==expected and data['phone']==frappe.conf.get('il_self_signup_test_phone')


def google_identity(email):
    return (frappe.session.user==email and bool(getattr(frappe.session,'data',{}).get('il_google_session'))
            and not frappe.db.exists('IL Public Profile',{'user':email})
            and not frappe.db.exists('IL Member',{'user':email}))


def marker(user):
    if frappe.local.site!='hnb-checkout.localhost':return False
    names=frappe.get_all('IL Registration Request',filters={'email':user,'status':'Approved','email_verified':1},pluck='name',limit_page_length=10)
    for name in names:
        data=json.loads(frappe.db.get_value('IL Registration Request',name,'details') or '{}')
        if data.get('flow')=='verified-self-signup-v1' and frappe.db.exists('IL Verified Phone',{'user':user,'phone':data.get('phone')}):return True
    return False


def key(token):
    if not isinstance(token,str) or not 30<=len(token)<=80:frappe.throw('Invalid signup session.')
    return 'il_self_signup:'+token


def digest(token,channel,code):
    return hmac.new(str(frappe.conf.encryption_key).encode(),(token+channel+code).encode(),hashlib.sha256).hexdigest()


def read(token):
    state=frappe.cache.get_value(key(token))
    if not state or state['expires']<=time.time() or state.get('consumed'):frappe.throw('Signup session expired. Start again.')
    return state


def store(token,state):
    frappe.cache.set_value(key(token),state,expires_in_sec=max(1,int(state['expires']-time.time())))


def send_email(address,code):
    # Only the explicitly configured test contact can receive an OTP. General
    # queue remains suspended; force-send only this newly created OTP record.
    from email.message import EmailMessage
    from email.utils import make_msgid
    account=frappe.get_doc('Email Account','SISU Academy')
    if account.smtp_server!='smtp-relay.brevo.com' or not account.enable_outgoing:frappe.throw('Sandbox email is not ready.')
    message=EmailMessage();message['From']='SISU Academy <noreply@sisuacademylk.com>'
    message['To']=address;message['Subject']='Your SISU signup verification code';message['Message-ID']=make_msgid(domain='sisuacademylk.com')
    message.set_content('Your SISU verification code is '+code+'. It expires in 10 minutes. Ignore this email if you did not request it.')
    queue=frappe.get_doc({'doctype':'Email Queue','sender':message['From'],'email_account':account.name,
        'message':message.as_string(),'message_id':message['Message-ID'],'status':'Not Sent',
        'recipients':[{'recipient':address,'status':'Not Sent'}]}).insert(ignore_permissions=True)
    frappe.db.commit()
    try:queue.send(force_send=True)
    except Exception:frappe.throw('Email delivery was not confirmed. Wait before retrying.')


def issue(token,state,channel):
    from .registration import limit
    now=time.time()
    if now-state.get(channel+'_last',0)<60:frappe.throw('Wait one minute before requesting another code.')
    limit('self-signup:'+channel+':'+state['details']['email'])
    limit('self-signup-ip:'+str(frappe.local.request_ip))
    code=f'{secrets.randbelow(1000000):06d}'
    state.update({channel+'_last':now,channel+'_expires':now+600,channel+'_attempts':0,
                  channel+'_digest':digest(token,channel,code),channel+'_verified':False})
    store(token,state)  # Preserve cooldown before external effects; no automatic retry.
    if channel=='email':send_email(state['details']['email'],code)
    else:
        from .providers import sms
        channel_name=frappe.conf.get('il_self_signup_phone_channel')
        if channel_name=='SMS':sms(state['details']['phone'],'Your SISU code is '+code+'. Expires in 10 minutes.')
        else:frappe.throw('Phone OTP delivery is not configured. No account can be created yet.')


def start(data):
    require_ready()

    if isinstance(data,str):
        if len(data)>8000:frappe.throw('Form is too large.')
        data=json.loads(data)
    try:fields=rules.details(data)
    except ValueError as error:frappe.throw(str(error))
    is_google=google_identity(fields['email'])
    if frappe.session.user!='Guest' and not is_google:frappe.throw('Sign out or use the Google account you just authenticated.')
    if not fields['phone'].startswith('+94'):
        frappe.throw('For this Sri Lankan SMS test, enter +94 followed by the nine-digit number, without the leading 0. Example: 0761234567 becomes +94761234567.')
    if fields['phone']!=frappe.conf.get('il_self_signup_test_phone'):
        frappe.throw('This phone does not match the authorized sandbox test phone. Use the exact +94 number entered in setup.')
    if not test_contact(fields):
        frappe.throw('This email is not configured for the selected sandbox role. Check the account type and the teacher/institute test email entered in setup.')
    from .portal_policy import public
    policy=public()
    if not policy['privacy_policy_url'] or data.get('privacy_policy_version')!=policy['privacy_policy_version']:
        frappe.throw('Review the current privacy policy.')
    if (frappe.db.exists('User',fields['email']) and not is_google) or frappe.db.exists('IL Public Profile',{'username':fields['username']}):
        frappe.throw('Account details are unavailable. Sign in or use password reset if you already registered.')
    if not (frappe.conf.get('il_self_signup_phone_channel')=='SMS' and (frappe.conf.get('il_sms_adapter') or frappe.get_hooks('il_send_verification_sms'))):
        frappe.throw('Configure and test the sandbox SMS provider before signup. WhatsApp sending remains disabled.')
    if fields['kind']=='Institute' and fields['email']!=frappe.conf.get('il_self_signup_institute_email'):
        frappe.throw('An isolated institute workspace must be assigned before this account can be created.')
    fields.update(privacy_policy_url=policy['privacy_policy_url'],privacy_policy_version=policy['privacy_policy_version'])
    token=secrets.token_urlsafe(32)
    state={'details':fields,'google_user':fields['email'] if is_google else None,'expires':time.time()+1800,'email_verified':False,'phone_verified':False}
    issue(token,state,'email')
    return {'challenge':token}


def send_phone(token):
    require_ready()
    with frappe.cache.lock(key(token),timeout=60):
        state=read(token)
        if not state['email_verified']:frappe.throw('Verify your email first.')
        issue(token,state,'phone')
    return {'sent':True}


def verify(token,channel,code):
    require_ready()
    if channel not in ('email','phone') or not isinstance(code,str) or len(code)!=6 or not code.isascii() or not code.isdigit():frappe.throw('Enter the six-digit code.')
    with frappe.cache.lock(key(token),timeout=20):
        state=read(token)
        if state.get(channel+'_verified'):return {'verified':True}
        if time.time()>=state.get(channel+'_expires',0) or state.get(channel+'_attempts',0)>=5:frappe.throw('Code expired. Start again.')
        state[channel+'_attempts']+=1;store(token,state)
        if not hmac.compare_digest(state[channel+'_digest'],digest(token,channel,code)):frappe.throw('Code did not match.')
        state[channel+'_verified']=True;store(token,state)
    return {'verified':True}


def complete(token,password,confirmation):
    require_ready()

    try:rules.password(password,confirmation)
    except ValueError as error:frappe.throw(str(error))
    with frappe.cache.lock(key(token),timeout=60):
        state=read(token)
        if not rules.verified(state,time.time()):frappe.throw('Verify both email and phone before saving.')
        data=state['details'];email=data['email']
        is_google=state.get('google_user')==email and google_identity(email)
        if state.get('google_user') and not is_google:frappe.throw('Google session changed. Start again.')
        if not is_google and frappe.session.user!='Guest':frappe.throw('Sign out before creating another account.')
        from .portal_policy import public
        policy=public()
        if data['privacy_policy_url']!=policy['privacy_policy_url'] or data['privacy_policy_version']!=policy['privacy_policy_version']:
            frappe.throw('Privacy policy changed. Review it and start again.')
        if not test_contact(data):
            frappe.throw('Sandbox test contact configuration changed. Start again.')
        with frappe.cache.lock('il_signup_account:'+hashlib.sha256(email.encode()).hexdigest(),timeout=60):
            if frappe.db.exists('User',email) and not is_google:frappe.throw('Account already exists. Please sign in.')
            from .api import institute
            inst=institute()
            if data['kind']=='Institute':
                frappe.db.sql('SELECT name FROM `tabIL Institute` WHERE name=%s FOR UPDATE',(inst.name,))
                if email!=frappe.conf.get('il_self_signup_institute_email') or frappe.db.exists('IL Member',{'institute':inst.name,'role':'Admin'}):
                    frappe.throw('Institute workspace assignment requires review.')
            # User.new_password follows Frappe strength checks and password hashing.
            if is_google:
                user=frappe.get_doc('User',email);user.first_name=data['first_name'];user.last_name=data['last_name'];user.new_password=password;user.save(ignore_permissions=True)
            else:
                user=frappe.get_doc({'doctype':'User','email':email,'first_name':data['first_name'],'last_name':data['last_name'],
                    'enabled':1,'user_type':'Website User','send_welcome_email':0,'new_password':password}).insert(ignore_permissions=True)
            from .profiles import write
            from frappe.utils import now_datetime
            write(frappe.get_doc({'doctype':'IL Verified Phone','user':email,'phone':data['phone'],'verified_at':now_datetime()}))
            role={'Individual Teacher':'Teacher','Institute':'Institute','Student':'Student'}[data['kind']]
            profile=frappe.get_doc({'doctype':'IL Public Profile','user':email,'username':data['username'],
                'display_name':data['first_name']+' '+data['last_name'],'kind':role,'country':data['country'],
                'status':'Verified' if role=='Student' else 'Pending','bio':data['bio'],'qualifications':data['qualifications'],
                'workspace':inst.name if role=='Institute' else None})
            write(profile)
            frappe.get_doc({'doctype':'IL Registration Request','email':email,'account_type':data['kind'],
                'status':'Approved','email_verified':1,'details':json.dumps({**data,'flow':'verified-self-signup-v1'}),
                'review_reason':'Identity verified by email and phone; not a provider endorsement.'}).insert(ignore_permissions=True)
            from .onboarding import activate
            member=activate(profile,inst.name if role=='Institute' else None)
            if role!='Student':
                from .account_billing import account,save
                billing=account(inst,frappe.get_doc('IL Member',member),create=True)
                billing.trial_until=now_datetime();save(billing)
            from .sandbox_notices import welcome
            welcome(email,data['kind'])
            frappe.db.commit()
            state['consumed']=True;store(token,state)
    if is_google:
        frappe.local.login_manager.logout()
    return {'created':True,'message':'Account created successfully. Your details have been saved. Please sign in.'}
