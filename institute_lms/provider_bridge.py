"""Owner-only control-plane -> tenant billing commands, signed and replay protected."""
import hmac
import json
import secrets
import time
import re
import requests
import frappe
from .saas_rules import sign

ACTIONS={'provider_proof_data':{'name'},'owner_invoices':set(),'invoice_detail':{'name'},'configure':{'owner_type','plan','billing_email','owner_user','bank_instructions','reason'},
         'approve_invoice':{'name','reference','received_amount','note'}}

def checked(action,args):
    if action not in ACTIONS or not isinstance(args,dict) or set(args)-ACTIONS[action]:raise ValueError('Unsupported billing command')
    if len(json.dumps(args))>5000:raise ValueError('Billing command too large')
    return args

@frappe.whitelist(methods=['POST'])
def request(tenant,action,args=None):
    from .platform import owner,organization
    from .release import https_origin
    owner();org=organization(tenant)
    values=json.loads(args) if isinstance(args,str) else args or {}
    checked(action,values)
    key=(frappe.conf.get('il_tenant_signing_keys') or {}).get(tenant)
    if not isinstance(key,str) or len(key)<32:frappe.throw('Tenant signing key is not configured')
    origin=https_origin('https://'+org.site_hostname)
    payload={'tenant_id':tenant,'site_hostname':org.site_hostname,'action':action,'args':values,
             'issued_at':int(time.time()),'nonce':secrets.token_hex(24),'actor':frappe.session.user}
    try:
        response=requests.post(origin+'/api/method/institute_lms.provider_bridge.receive',
            json={'payload':json.dumps(payload),'signature':sign(payload,key)},timeout=(5,25),allow_redirects=False)
        response.raise_for_status();result=response.json()
        if 'message' not in result or result.get('exc'):raise ValueError('Tenant billing command rejected')
        return result['message']
    except Exception:
        frappe.throw('Tenant billing service unavailable. Refresh invoice history before retrying; an interrupted response does not confirm payment.')

@frappe.whitelist(allow_guest=True,methods=['POST'])
def receive(payload,signature):
    if frappe.conf.get('il_control_plane') or not isinstance(payload,str) or len(payload)>8000:frappe.throw('Invalid billing request',frappe.PermissionError)
    value=json.loads(payload);key=frappe.conf.get('il_control_plane_key')
    if not isinstance(key,str) or len(key)<32 or not hmac.compare_digest(sign(value,key),str(signature)):frappe.throw('Invalid signature',frappe.PermissionError)
    if (value.get('tenant_id')!=frappe.conf.get('il_tenant_id') or value.get('site_hostname')!=frappe.local.site
            or abs(time.time()-int(value.get('issued_at',0)))>60
            or value.get('actor')!=frappe.conf.get('il_owner_email')
            or not re.fullmatch(r'[a-f0-9]{48}',str(value.get('nonce','')))):
        frappe.throw('Invalid billing request scope',frappe.PermissionError)
    args=checked(value.get('action'),value.get('args'))
    token='sisu-provider-command:'+value['nonce']
    with frappe.cache.lock('sisu-provider-command-lock',timeout=30):
        if frappe.cache.get_value(token):frappe.throw('Billing command replay',frappe.PermissionError)
        frappe.cache.set_value(token,True,expires_in_sec=180)
    previous=frappe.session.user
    try:
        frappe.set_user(value['actor'])
        from . import commercial
        return getattr(commercial,value['action'])(**args)
    finally:frappe.set_user(previous)
