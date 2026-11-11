"""Opt-in public account signup. Account creation does not grant a workspace."""
import hashlib,json,secrets,time
import frappe
from . import self_signup as challenges, signup_rules as rules

def enabled(config=None):
    config=frappe.conf if config is None else config
    return (config.get('il_public_signup_enabled')==1
            and config.get('il_shared_campus_enabled')==1
            and not config.get('il_control_plane'))

def google_identity(email):
    return (enabled() and frappe.session.user==email and email not in ('Guest','Administrator')
            and bool(getattr(frappe.session,'data',{}).get('il_google_session'))
            and bool(frappe.db.get_value('User',email,'enabled')))


def ready():
    from frappe.utils import get_url
    from urllib.parse import urlsplit
    if not enabled() or urlsplit(get_url()).scheme!='https':frappe.throw('Public signup is not available yet.')
    if not frappe.conf.get('encryption_key') or not frappe.db.exists('Email Account',{'enable_outgoing':1}):frappe.throw('Email verification is not ready.')
    if not frappe.conf.get('il_sms_adapter') or (frappe.conf.get('il_notify_live') or {}).get('test_mode'):
        frappe.throw('Public SMS verification is not ready.')
    if frappe.conf.get('il_self_signup_phone_channel')!='SMS':frappe.throw('SMS verification is not ready.')

def read(token):
    state=challenges.read(token)
    if state.get('flow')!='public-account-v1':frappe.throw('Start public signup again.')
    return state

def start(data):
    ready()
    if isinstance(data,str):
        if len(data)>8000:frappe.throw('Form is too large.')
        data=json.loads(data)
    try:fields=rules.details(data)
    except ValueError as error:frappe.throw(str(error))
    google=google_identity(fields['email'])
    if google and fields['kind'] != 'Student':
        frappe.throw('Learner Google signup creates a Student account. Use provider signup for a teaching account.')
    if frappe.session.user!='Guest' and not google:frappe.throw('Use the Google account you just signed in with, or sign out.')
    from .portal_policy import public
    policy=public()
    if not policy['privacy_policy_url'] or data.get('privacy_policy_version')!=policy['privacy_policy_version']:frappe.throw('Review the current privacy policy.')
    existing=frappe.db.get_value('IL Public Profile',{'user':fields['email']},['name','kind'],as_dict=True) if google else None
    if existing and existing.kind!='Student':frappe.throw('Your provider profile already exists. Update it through your account settings.')
    username_owner=frappe.db.get_value('IL Public Profile',{'username':fields['username']},'user')
    if existing and fields['kind'] != {'Teacher':'Individual Teacher'}.get(existing.kind,existing.kind):frappe.throw('Your existing account type cannot be changed during verification.')
    if (frappe.db.exists('User',fields['email']) and not google) or (username_owner and username_owner!=fields['email']):
        frappe.throw('Account details are unavailable. Sign in if you already registered.')
    fields.update(privacy_policy_url=policy['privacy_policy_url'],privacy_policy_version=policy['privacy_policy_version'])
    token=secrets.token_urlsafe(32)
    state={'flow':'public-account-v1','details':fields,'google_user':fields['email'] if google else None,
        'expires':time.time()+1800,'email_verified':False,'phone_verified':False}
    challenges.issue(token,state,'email')
    return {'challenge':token}

def send_phone(token):
    ready()
    with frappe.cache.lock(challenges.key(token),timeout=60):
        state=read(token)
        if not state['email_verified']:frappe.throw('Verify your email first.')
        challenges.issue(token,state,'phone')
    return {'sent':True}

def verify(token,channel,code):
    ready()
    if channel not in ('email','phone') or not isinstance(code,str) or len(code)!=6 or not code.isascii() or not code.isdigit():frappe.throw('Enter the six-digit code.')
    import hmac
    with frappe.cache.lock(challenges.key(token),timeout=20):
        state=read(token)
        if state.get(channel+'_verified'):return {'verified':True}
        if time.time()>=state.get(channel+'_expires',0) or state.get(channel+'_attempts',0)>=5:frappe.throw('Code expired. Start again.')
        state[channel+'_attempts']+=1;challenges.store(token,state)
        if not hmac.compare_digest(state[channel+'_digest'],challenges.digest(token,channel,code)):frappe.throw('Code did not match.')
        state[channel+'_verified']=True;challenges.store(token,state)
    return {'verified':True}

def complete(token,password,confirmation):
    ready()
    with frappe.cache.lock(challenges.key(token),timeout=60):
        state=read(token)
        if not rules.account_creation_ready(state,time.time()):frappe.throw('Complete the required verification before saving.')
        data=state['details'];email=data['email']
        google=state.get('google_user')==email and google_identity(email)
        if state.get('google_user') and not google:frappe.throw('Google session changed. Start again.')
        try:rules.password(password,confirmation)
        except ValueError as error:frappe.throw(str(error))
        if not google and frappe.session.user!='Guest':frappe.throw('Sign out before creating another account.')
        from .portal_policy import public
        policy=public()
        if any(data[k]!=policy[k] for k in ('privacy_policy_url','privacy_policy_version')):frappe.throw('Privacy policy changed. Start again.')
        with frappe.cache.lock('il_signup_account:'+hashlib.sha256(email.encode()).hexdigest(),timeout=60):
            if frappe.db.exists('User',email) and not google:frappe.throw('Account already exists. Please sign in.')
            if google:
                user=frappe.get_doc('User',email);user.first_name=data['first_name'];user.last_name=data['last_name'];user.save(ignore_permissions=True)
                from frappe.utils.password import update_password
                update_password(email,password,logout_all_sessions=False)
            else:
                frappe.get_doc({'doctype':'User','email':email,'first_name':data['first_name'],'last_name':data['last_name'],
                    'enabled':1,'user_type':'Website User','send_welcome_email':0,'new_password':password}).insert(ignore_permissions=True)
            from .profiles import write
            from frappe.utils import now_datetime
            if state.get('phone_verified') is True:
                phone_name=frappe.db.get_value('IL Verified Phone',{'user':email},'name')
                phone_doc=frappe.get_doc('IL Verified Phone',phone_name) if phone_name else frappe.get_doc({'doctype':'IL Verified Phone','user':email})
                phone_doc.phone=data['phone'];phone_doc.verified_at=now_datetime();write(phone_doc)
            kind={'Individual Teacher':'Teacher','Institute':'Institute','Student':'Student'}[data['kind']]
            profile_name=frappe.db.get_value('IL Public Profile',{'user':email},'name')
            profile=frappe.get_doc('IL Public Profile',profile_name) if profile_name else frappe.get_doc({'doctype':'IL Public Profile','user':email,'kind':kind})
            if profile.kind!=kind:frappe.throw('Account type changed. Start verification again.')
            profile.update({'username':data['username'],
                'display_name':data.get('organization') or data['first_name']+' '+data['last_name'],
                'country':data['country'],'bio':data['bio'],'qualifications':data['qualifications']})
            if kind=='Student':profile.grades=data.get('grade','')
            if not profile_name or kind=='Student':profile.status='Verified' if kind=='Student' else 'Pending'
            write(profile)
            # No membership, global role, subscription, paid grant or institute
            # ownership is created by this identity-verification transaction.
            frappe.get_doc({'doctype':'IL Registration Request','email':email,'account_type':data['kind'],
                'status':'Approved','email_verified':1,'details':json.dumps({**data,'flow':'public-account-v1','onboarding_version':2}),
                'review_reason':'Email verified; phone verification '+('complete' if state.get('phone_verified') is True else 'required on first login')+'; no workspace permissions or provider endorsement granted.'}).insert(ignore_permissions=True)
            from .account_confirmations import queue
            queue(email,'account-verified','Account created','Your SISU account has been created. Sign in to complete any remaining profile and mobile verification steps.')
            frappe.db.commit()
            state['consumed']=True;challenges.store(token,state)
    return {'created':True,'message':'Your account is ready. Sign in to your SISU space.'}
