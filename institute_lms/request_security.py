"""Shared Redis request budgets. Independent of browser controls and worker count."""
import hashlib
from urllib.parse import unquote
import frappe

class ProtectionUnavailable(Exception):
    http_status_code = 503

COUNTER = """
local count=redis.call('INCR',KEYS[1])
if count==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end
local ttl=redis.call('TTL',KEYS[1])
if ttl<0 then redis.call('EXPIRE',KEYS[1],ARGV[1]); ttl=tonumber(ARGV[1]) end
return {count,ttl}
"""


def budget(scope, identity, limit, seconds=60):
    digest=hashlib.sha256(str(identity).encode()).hexdigest()
    key=frappe.cache.make_key('il_request_budget:'+scope+':'+digest)
    try:
        count,ttl=frappe.cache.eval(COUNTER,1,key,seconds)
    except Exception:
        frappe.local.response['http_status_code']=503
        frappe.throw('Request protection is temporarily unavailable. Please try again shortly.', ProtectionUnavailable)
    if int(count)>limit:
        retry=max(1,int(ttl))
        frappe.local.il_retry_after=retry
        frappe.local.response['retry_after_seconds']=retry
        frappe.throw('Too many requests. Please wait before trying again.',frappe.TooManyRequestsError)


def before_login(login_manager=None):
    # Runs before password authentication, including attempts that fail.
    ip=str(getattr(frappe.local,'request_ip','unknown'))
    budget('login-ip',ip,20,300)
    user=str(frappe.form_dict.get('usr') or '').strip().lower()[:254]
    if user: budget('login-account',user,10,300)


def guard():
    request=getattr(frappe.local,'request',None)
    if not request or request.method=='OPTIONS':return
    path=unquote(request.path)
    cmd=str(frappe.form_dict.get('cmd') or '')
    if not path.startswith('/api/') and not cmd:return
    if '/method/' in path:cmd=path.split('/method/',1)[1].rstrip('/')
    user=frappe.session.user
    ip=str(getattr(frappe.local,'request_ip','unknown'))
    # The ingress proxy MUST overwrite X-Forwarded-For; never expose backend ports.
    budget('api-ip',ip,1200)
    budget('api-user' if user!='Guest' else 'api-guest',user if user!='Guest' else ip,600 if user!='Guest' else 120)
    if cmd=='institute_lms.cybersource.start':budget('checkout',user,12)
    elif cmd in ('institute_lms.cybersource.reconcile','institute_lms.cybersource.status'):
        budget('payment-status',user,60)
    elif cmd.startswith('institute_lms.owner_people.'):
        budget('people-reports',user,60)


def response_headers(response,request=None):
    retry=getattr(frappe.local,'il_retry_after',None)
    if retry:response.headers['Retry-After']=str(retry)
    response.headers.setdefault('X-Content-Type-Options','nosniff')
    response.headers.setdefault('Referrer-Policy','strict-origin-when-cross-origin')
