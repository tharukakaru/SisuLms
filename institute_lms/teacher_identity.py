"""Identity checks for a public teacher applying to an institute, not endorsement."""
import json
import frappe

def eligible(user):
    from .public_signup import enabled
    if not enabled() or not frappe.db.get_value('User',user,'enabled'):return False
    profile=frappe.db.get_value('IL Public Profile',{'user':user,'kind':'Teacher'},['name','status'],as_dict=True)
    if not profile or profile.status not in ('Pending','Verified'):return False
    phone=frappe.db.get_value('IL Verified Phone',{'user':user},['phone','verified_at'],as_dict=True)
    if not phone or not phone.phone or not phone.verified_at:return False
    rows=frappe.get_all('IL Registration Request',filters={'email':user,'account_type':'Individual Teacher','status':'Approved','email_verified':1},fields=['details'],limit_page_length=10)
    for row in rows:
        try:data=json.loads(row.details or '{}')
        except (ValueError,TypeError):continue
        if (isinstance(data,dict) and data.get('flow')=='public-account-v1'
            and data.get('kind')=='Individual Teacher' and data.get('email')==user and data.get('phone')==phone.phone):return True
    return False
