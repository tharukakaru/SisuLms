"""Shared phone issuance lock, separate channel challenges, no plaintext persistence."""
import hashlib
import hmac
import re
import secrets
import time
import frappe
from frappe.utils import get_url, now_datetime
from .wallet import signed_in

def digest(challenge, phone, code):
    return hmac.new(str(frappe.conf.encryption_key).encode(),(challenge+':'+phone+':'+code).encode(),hashlib.sha256).hexdigest()

def issue(phone, channel, sender):
    signed_in()
    if channel not in ('SMS','WHATSAPP') or not re.fullmatch(r'\+[1-9][0-9]{7,14}',str(phone)):frappe.throw('Invalid phone or channel')
    from urllib.parse import urlsplit
    origin=urlsplit(get_url())
    request=getattr(frappe.local,'request',None)
    request_host=str(getattr(request,'host','')).split(':')[0].lower()
    local_dev=(frappe.conf.get('il_local_http_otp') == 1
               and getattr(frappe.local,'site',None)=='localhost'
               and origin.scheme=='http' and origin.hostname=='localhost'
               and request_host=='localhost')
    if (origin.scheme!='https' and not local_dev) or not frappe.conf.get('encryption_key'):
        frappe.throw('Secure OTP configuration required')
    from .registration import limit
    user=frappe.session.user;lock='il_phone_issue:'+user
    with frappe.cache.lock(lock,timeout=45):
        now=time.time();last=frappe.cache.get_value(lock+':last')
        if last and now-last<60:frappe.throw('Wait one minute before requesting another code')
        limit('phone-user:'+user);limit('phone-number:'+phone);limit('phone-ip:'+str(frappe.local.request_ip))
        # Record cooldown before external send, including ambiguous/failing sends.
        frappe.cache.set_value(lock+':last',now,expires_in_sec=60)
        code=f'{secrets.randbelow(1000000):06d}';challenge=secrets.token_urlsafe(24)
        sender(phone,code)
        key='il_phone:'+user+':'+channel
        frappe.cache.set_value(key,{'phone':phone,'challenge':challenge,'digest':digest(challenge,phone,code),
            'created':now,'attempts':0},expires_in_sec=600)
    return {'sent':True,'channel':channel,'challenge':challenge,'expires_in_seconds':600}

def verify(code,channel='SMS',challenge=None):
    signed_in()
    if channel not in ('SMS','WHATSAPP') or not re.fullmatch(r'[0-9]{6}',str(code)):frappe.throw('Invalid verification request')
    user=frappe.session.user;key='il_phone:'+user+':'+channel
    with frappe.cache.lock('il_phone_issue:'+user,timeout=45):
        d=frappe.cache.get_value(key);now=time.time()
        if not d or now-d['created']>=600 or d['attempts']>=5:frappe.throw('Code expired')
        if challenge is not None and challenge!=d['challenge']:frappe.throw('Challenge changed')
        d['attempts']+=1;frappe.cache.set_value(key,d,expires_in_sec=max(1,600-int(now-d['created'])))
        if not hmac.compare_digest(d['digest'],digest(d['challenge'],d['phone'],code)):frappe.throw('Code did not match')
        from .profiles import write
        name=frappe.db.get_value('IL Verified Phone',{'user':user},'name')
        doc=frappe.get_doc('IL Verified Phone',name) if name else frappe.get_doc({'doctype':'IL Verified Phone','user':user})
        doc.phone=d['phone'];doc.verified_at=now_datetime();write(doc)
        # A successful verification consumes both channels so an old code cannot revert ownership.
        for c in ('SMS','WHATSAPP'):frappe.cache.delete_value('il_phone:'+user+':'+c)
    return {'verified':True}
