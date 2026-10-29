"""Per-user, per-site PKCE handoff from a real Frappe browser login.

Uses Frappe's auth_hooks extension. No shared API key, passwords, or Google
tokens are issued to Flutter. Browser approval remains CSRF protected.
"""
import base64
import hashlib
import hmac
import html
import re
import secrets
from datetime import timedelta
from urllib.parse import urlencode
import frappe
from frappe.utils import now_datetime, get_datetime, get_url
from .saas import managed

def parameters(challenge,state,redirect_uri):
    # AppAuth uses a 128-bit URL-safe state (22 unpadded characters).
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}',str(challenge)) or not re.fullmatch(r'[A-Za-z0-9_-]{22,128}',str(state)):
        frappe.throw('Invalid PKCE challenge or state')
    if redirect_uri not in (frappe.conf.get('il_mobile_redirect_uris') or []) or '?' in redirect_uri or '#' in redirect_uri:
        frappe.throw('Mobile redirect not registered')
    if not get_url().startswith('https://'):frappe.throw('HTTPS required')

@frappe.whitelist(allow_guest=True,methods=['GET'])
def app_authorize(code_challenge,state,redirect_uri,code_challenge_method=None,response_type=None,client_id=None,scope=None,nonce=None):
    """AppAuth parameter adapter; retains browser approval and SISU token exchange."""
    if code_challenge_method!='S256' or response_type!='code' or client_id!='sisu-mobile':
        frappe.throw('Unsupported mobile authorization request',frappe.PermissionError)
    return authorize(code_challenge,state,redirect_uri)

@frappe.whitelist(allow_guest=True,methods=['GET'])
def authorize(challenge,state,redirect_uri):
    parameters(challenge,state,redirect_uri)
    target='/api/method/institute_lms.mobile_auth.authorize?'+urlencode(dict(challenge=challenge,state=state,redirect_uri=redirect_uri))
    if frappe.session.user=='Guest':
        # Teachers/admins may use password login; the existing login hook and
        # approval guard still require real Google assurance for students.
        frappe.local.response.update(type='redirect',location='/login?'+urlencode({'redirect-to':target}));return
    from werkzeug.wrappers import Response
    values=dict(challenge=challenge,state=state,redirect_uri=redirect_uri,csrf_token=frappe.sessions.get_csrf_token())
    fields=''.join('<input type="hidden" name="'+k+'" value="'+html.escape(v,quote=True)+'">' for k,v in values.items())
    return Response('<!doctype html><title>Connect SISU mobile</title><h1>Connect your mobile app</h1><p>Signed in as '+html.escape(frappe.session.user)+
        '</p><form method="POST" action="/api/method/institute_lms.mobile_auth.approve">'+fields+'<button>Approve this device</button></form>',
        mimetype='text/html',headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY'})

@frappe.whitelist(methods=['POST'])
def approve(challenge,state,redirect_uri):
    parameters(challenge,state,redirect_uri)
    from .registration import limit
    limit('mobile-approve:'+frappe.session.user)
    google=bool(getattr(frappe.session,'data',{}).get('il_google_session'))
    student=frappe.db.exists('IL Member',{'user':frappe.session.user,'role':'Student'}) or frappe.db.exists('IL Public Profile',{'user':frappe.session.user,'kind':'Student'})
    if student and not google:frappe.throw('Students must authenticate with Google',frappe.AuthenticationError)
    code=secrets.token_urlsafe(32);key=hashlib.sha256(code.encode()).hexdigest()
    frappe.cache.set_value('il_mobile_code:'+key,dict(user=frappe.session.user,challenge=challenge,redirect_uri=redirect_uri,google=google),expires_in_sec=120)
    frappe.local.response.update(type='redirect',location=redirect_uri+'?'+urlencode(dict(code=code,state=state)))

@frappe.whitelist(allow_guest=True,methods=['POST'])
def exchange(code,verifier,redirect_uri,device_id):
    from .registration import limit
    limit('mobile-exchange:'+str(frappe.local.request_ip))
    if not re.fullmatch(r'[A-Za-z0-9._~-]{43,128}',str(verifier)) or not re.fullmatch(r'[A-Za-z0-9_-]{8,120}',str(device_id)) or len(str(code))>100:frappe.throw('Invalid exchange')
    key='il_mobile_code:'+hashlib.sha256(str(code).encode()).hexdigest()
    with frappe.cache.lock(key,timeout=10):
        d=frappe.cache.get_value(key)
        calculated=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        if not d or d['redirect_uri']!=redirect_uri or not hmac.compare_digest(d['challenge'],calculated):frappe.throw('Expired or invalid handoff',frappe.AuthenticationError)
        if not frappe.db.get_value('User',d['user'],'enabled'):frappe.throw('Account disabled')
        token=secrets.token_urlsafe(48);expires=now_datetime()+timedelta(days=7)
        managed(frappe.get_doc({'doctype':'IL Mobile Session','user':d['user'],'token_hash':hashlib.sha256(token.encode()).hexdigest(),
            'device_id':device_id,'google_authenticated':int(d['google']),'expires_at':expires,'revoked':0}))
        frappe.cache.delete_value(key)
    frappe.local.response_headers['Cache-Control']='no-store'
    return {'access_token':token,'token_type':'Sisu','expires_at':expires,'site':get_url()}

def authenticate():
    header=frappe.get_request_header('Authorization','')
    if not header.startswith('Sisu '):return
    # Native Frappe APIs are not token-scoped SISU mobile endpoints.
    path=frappe.local.request.path
    if not path.startswith('/api/method/institute_lms.') or frappe.form_dict.get('cmd'):
        frappe.throw('Mobile token is limited to SISU APIs',frappe.PermissionError)
    if frappe.session.user!='Guest':frappe.throw('Do not mix mobile tokens with browser cookies')
    token=header[5:]
    if not 40<=len(token)<=200:frappe.throw('Invalid token',frappe.AuthenticationError)
    name=frappe.db.get_value('IL Mobile Session',{'token_hash':hashlib.sha256(token.encode()).hexdigest()},'name')
    d=frappe.get_doc('IL Mobile Session',name) if name else None
    if not d or d.revoked or get_datetime(d.expires_at)<=now_datetime() or not frappe.db.get_value('User',d.user,'enabled'):
        frappe.throw('Mobile session expired or revoked',frappe.AuthenticationError)
    frappe.set_user(d.user)
    frappe.local.il_mobile_session=d.name
    frappe.local.il_mobile_google=bool(d.google_authenticated)

@frappe.whitelist(methods=['POST'])
def logout(session=None):
    if frappe.session.user=='Guest':frappe.throw('Sign in required')
    name=session or getattr(frappe.local,'il_mobile_session',None)
    if not name:frappe.throw('Mobile session required')
    d=frappe.get_doc('IL Mobile Session',name)
    if d.user!=frappe.session.user:frappe.throw('Foreign session',frappe.PermissionError)
    d.revoked=1;managed(d)
    return {'revoked':True}
