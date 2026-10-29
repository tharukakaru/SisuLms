"""Self-service personal details; never part of public profiles/search."""
import json
import frappe
from frappe.utils import now_datetime,getdate
from .wallet import signed_in
from .private_contact_rules import normalize,age_on,FIELDS,guardian_updates_without_otp

def own():
    signed_in()
    name=frappe.db.get_value('IL Private Contact',{'user':frappe.session.user},'name')
    return frappe.get_doc('IL Private Contact',name) if name else None

@frappe.whitelist(methods=['POST'])
def get_details():
    d=own()
    data={k:d.get(k) for k in FIELDS} if d else {'notification_language':'en'}
    data['age']=age_on(str(d.date_of_birth),getdate()) if d and d.date_of_birth else None
    return {'data':data,'verified_phone':frappe.db.get_value('IL Verified Phone',{'user':frappe.session.user},'phone') or '',
            'login_email':frappe.session.user}

@frappe.whitelist(methods=['POST'])
def save_details(data):
    signed_in()
    from .onboarding import account_kind
    if isinstance(data,str):data=json.loads(data)
    kind=account_kind()
    try:values=normalize(data,kind,getdate())
    except ValueError as e:frappe.throw(str(e))
    if values['whatsapp_opt_in'] and not guardian_updates_without_otp(values,kind,getdate()) and not frappe.db.exists('IL Verified Phone',{'user':frappe.session.user,'phone':values['whatsapp_phone']}):frappe.throw('Verify this WhatsApp number before enabling updates')
    d=own() or frappe.get_doc({'doctype':'IL Private Contact','user':frappe.session.user})
    if bool(d.get('whatsapp_opt_in'))!=bool(values['whatsapp_opt_in']) or d.get('whatsapp_phone')!=values['whatsapp_phone']:d.consent_at=now_datetime()
    d.update(values);d.flags.contact_service=True;d.save(ignore_permissions=True)
    for name in frappe.get_all('IL Member',filters={'user':frappe.session.user,'active':1},pluck='name'):
        frappe.db.set_value('IL Member',name,{'phone':values['whatsapp_phone'],'whatsapp_opt_in':values['whatsapp_opt_in'],'language':values['notification_language']})
    return {'saved':True,'age':age_on(values['date_of_birth'],getdate())}

@frappe.whitelist(methods=['POST'])
def request_whatsapp_code(phone):
    from .otp import issue
    from .providers import whatsapp_code
    return issue(phone,'WHATSAPP',whatsapp_code)
