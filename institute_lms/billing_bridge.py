"""Signed tenant-Admin billing delegation; fixed control-plane origin, no shared API key."""
import json
import secrets
import time
import hmac
import frappe
import requests
from .saas_rules import sign

ACTIONS={'summary','quote','checkout','status','receipt','request_pricing'}

@frappe.whitelist(methods=['POST'])
def request(action='summary', args=None):
    from .api import identity,require_role
    _,member=identity();require_role(member,'Admin')
    if frappe.conf.get('il_control_plane') or action not in ACTIONS:frappe.throw('Billing action unavailable')
    from .release import https_origin
    origin=https_origin(frappe.conf.get('il_control_plane_url'))
    key=frappe.conf.get('il_control_plane_key')
    if not origin or not isinstance(key,str) or len(key)<32:frappe.throw('Organization billing connection is not configured')
    values=json.loads(args) if isinstance(args,str) else args or {}
    if not isinstance(values,dict) or len(json.dumps(values))>4000:frappe.throw('Invalid billing request')
    payload={'tenant_id':frappe.conf.il_tenant_id,'site_hostname':frappe.local.site,'action':action,
             'args':values,'actor':frappe.session.user,'issued_at':int(time.time()),'nonce':secrets.token_hex(24)}
    try:
        response=requests.post(origin+'/api/method/institute_lms.billing_bridge.receive',
            json={'payload':json.dumps(payload),'signature':sign(payload,key)},timeout=(5,25),allow_redirects=False)
        response.raise_for_status();result=response.json()
        if 'message' not in result or result.get('exc'):raise ValueError('billing_response')
        return result['message']
    except Exception:
        frappe.throw('Secure billing service unavailable. No payment is confirmed; check history before retrying checkout.')

@frappe.whitelist(allow_guest=True,methods=['POST'])
def receive(payload,signature):
    from .platform import control
    control()
    if not isinstance(payload,str) or len(payload)>8000:frappe.throw('Invalid request',frappe.PermissionError)
    value=json.loads(payload);tenant=value.get('tenant_id');key=(frappe.conf.get('il_tenant_signing_keys') or {}).get(tenant)
    if not key or not hmac.compare_digest(sign(value,key),str(signature)):frappe.throw('Invalid request',frappe.PermissionError)
    org=frappe.get_doc('IL Organization',tenant)
    if not org.enabled or value.get('site_hostname')!=org.site_hostname or abs(time.time()-int(value.get('issued_at',0)))>60:
        frappe.throw('Invalid request scope',frappe.PermissionError)
    action=value.get('action');args=value.get('args') or {};nonce=value.get('nonce')
    import re
    if action not in ACTIONS or not isinstance(args,dict) or not re.fullmatch(r'[a-f0-9]{48}',str(nonce)):frappe.throw('Invalid action')
    with frappe.cache.lock('il_billing_nonce:'+tenant,timeout=30):
        token='il_billing_nonce:'+tenant+':'+nonce
        if frappe.cache.get_value(token):frappe.throw('Billing request replay',frappe.PermissionError)
        frappe.cache.set_value(token,True,expires_in_sec=180)
    previous=frappe.session.user
    try:
        frappe.set_user(org.admin_contact)
        from . import premium,subscription_payments
        if action=='summary':return premium.summary(tenant)
        if action=='request_pricing':return premium.request_pricing(tenant)
        if action=='quote':return subscription_payments.quote(tenant,'PREMIUM AI')
        if action=='checkout':
            q=frappe.get_doc('IL Checkout Quote',args.get('quote'))
            if q.tenant_id!=tenant:frappe.throw('Foreign quote',frappe.PermissionError)
            return subscription_payments.checkout(q.name,mobile=args.get('mobile') is True)
        if action=='status':
            a=frappe.get_doc('IL Payment Attempt',args.get('attempt'))
            if a.tenant_id!=tenant:frappe.throw('Foreign attempt',frappe.PermissionError)
            return subscription_payments.status(a.name)
        if action=='receipt':
            d=frappe.get_doc('IL Premium Receipt',args.get('name'))
            if d.tenant_id!=tenant:frappe.throw('Foreign receipt',frappe.PermissionError)
            return premium.receipt(d.name)
    finally:
        frappe.set_user(previous)
