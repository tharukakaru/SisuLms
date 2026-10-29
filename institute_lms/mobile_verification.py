"""Phone ownership verification. Provider hook must be configured server-side."""
import hashlib,hmac,re,secrets,time
import frappe
from frappe.utils import now_datetime,get_url
from .wallet import signed_in
from .profiles import write
from .registration import limit

@frappe.whitelist(methods=['POST'])
def request_code(phone):
    from .otp import issue
    from .providers import sms
    return issue(phone,'SMS',lambda phone,code: sms(phone,'Your Sisu verification code is '+code+'. It expires in 10 minutes.'))

@frappe.whitelist(methods=['POST'])
def verify(code,channel='SMS',challenge=None):
    from .otp import verify as verify_challenge
    return verify_challenge(code,channel,challenge)

@frappe.whitelist(methods=['POST'])
def claim_trial():
    """Hosted-card adapter validates customer ownership, setup status and reuse."""
    signed_in()
    from .profiles import required
    required()
    hooks=frappe.get_hooks('il_verified_card_for_user')
    if not hooks:frappe.throw('Hosted card setup is not connected')
    with frappe.cache.lock('il_trial:'+frappe.session.user,timeout=20):
        if frappe.db.exists('IL Trial Claim',{'user':frappe.session.user}):frappe.throw('Trial already claimed')
        card=frappe.get_attr(hooks[0])(frappe.session.user)
        if not card or not card.get('verified') or card.get('user')!=frappe.session.user:frappe.throw('A verified card for this account is required')
        from datetime import timedelta
        end=now_datetime()+timedelta(days=3)
        doc=frappe.get_doc({'doctype':'IL Trial Claim','user':frappe.session.user,'verified_card_reference':card['reference'],'expires_at':end,'status':'Active'});write(doc)
    return {'expires_at':end,'status':'Active'}

def has_trial(user):
    row=frappe.db.get_value('IL Trial Claim',{'user':user},['expires_at','status'],as_dict=True)
    return bool(row and row.status=='Active' and row.expires_at>now_datetime())
