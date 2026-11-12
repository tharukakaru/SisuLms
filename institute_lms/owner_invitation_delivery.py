"""Deliver only explicitly requested, fresh control-plane access invitations.
General email suspension and payment hold remain in force.
"""
from email import policy
from email.parser import Parser
from datetime import timedelta
import frappe
from frappe.utils import now_datetime,get_datetime
SUBJECTS={'Your SISU Platform owner access':'owner','Your SISU institute billing access':'billing'}

def purpose(message):
    try:return SUBJECTS.get(str(Parser(policy=policy.default).parsestr(message or '',headersonly=True).get('Subject','')))
    except (TypeError,ValueError):return None

def permitted(recipient,kind):
    if not frappe.db.get_value('User',recipient,'enabled'):return False
    if kind=='owner':
        from .owner_access import primary_email
        return recipient==primary_email() or bool(frappe.db.exists('IL Owner Access',{'user':recipient,'enabled':1}))
    if kind=='billing':return bool(frappe.db.exists('IL Organization',{'admin_contact':recipient,'enabled':1}))
    return False

def dispatch():
    if not frappe.conf.get('il_control_plane') or not frappe.conf.get('il_owner_invitation_delivery_enabled'):return
    if not frappe.db.sql('SELECT GET_LOCK(%s,0)',('sisu_owner_invitation_delivery',))[0][0]:return
    try:
        cutoff=now_datetime()-timedelta(hours=1)
        rows=frappe.get_all('Email Queue',filters={'creation':['>=',cutoff]},fields=['name','creation'],order_by='creation desc,name desc',limit_page_length=200)
        seen=set()
        for row in rows:
            doc=frappe.get_doc('Email Queue',row.name)
            kind=purpose(doc.message)
            recipients=list(doc.recipients or [])
            if not kind or len(recipients)!=1:continue
            recipient=str(recipients[0].recipient or '').strip().lower()
            key=(recipient,kind)
            if key in seen:continue
            seen.add(key) # Never resend an older token after a newer invitation exists.
            if doc.status!='Not Sent' or get_datetime(doc.creation)<cutoff or not permitted(recipient,kind):continue
            # Only these approved invitation types bypass the general mail hold.
            doc.send(force_send=True)
            frappe.db.commit()
    finally:
        frappe.db.sql('SELECT RELEASE_LOCK(%s)',('sisu_owner_invitation_delivery',))
