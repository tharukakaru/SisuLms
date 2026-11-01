import hashlib
import re
import frappe
from .wallet import signed_in
from .saas import managed

@frappe.whitelist(methods=['POST'])
def register(device_id,token,platform):
    signed_in()
    from .registration import limit
    limit('device-register:'+frappe.session.user)
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,120}',str(device_id)) or platform not in ('android','ios','web'):
        frappe.throw('Invalid device')
    if not isinstance(token,str) or not 20<=len(token)<=4096 or any(c.isspace() for c in token):frappe.throw('Invalid push token')
    digest=hashlib.sha256(token.encode()).hexdigest()
    # Serialize registrations for the same token; unique DB constraint is authoritative.
    with frappe.cache.lock('il_device:'+digest,timeout=10):
        name=frappe.db.get_value('IL Device Token',{'token_hash':digest},'name')
        d=frappe.get_doc('IL Device Token',name) if name else frappe.get_doc({'doctype':'IL Device Token','user':frappe.session.user,'token_hash':digest})
        if d.user!=frappe.session.user:frappe.throw('Token belongs to another account; revoke it there first',frappe.PermissionError)
        d.token=token;d.device_id=device_id;d.platform=platform;d.revoked=0;managed(d)
    return {'device':d.name}

@frappe.whitelist(methods=['POST'])
def revoke(device):
    signed_in();d=frappe.get_doc('IL Device Token',device)
    if d.user!=frappe.session.user:frappe.throw('Device unavailable',frappe.PermissionError)
    d.revoked=1;managed(d)
    return {'revoked':True}

@frappe.whitelist(methods=['GET'])
def firebase_config():
    signed_in()
    from .firebase_push import browser_config
    return browser_config()

@frappe.whitelist(methods=['POST'])
def firebase_test(device,request_id,dry_run=True):
    signed_in()
    from .firebase_push import self_test
    return self_test(device,request_id,dry_run)
