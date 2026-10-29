"""Bench-only tenant initialization. Intentionally not whitelisted."""
import frappe
from .saas_rules import hostname

def initialize(tenant_id,site_hostname,title,code,admin_email,**unused):
    import re
    if not re.fullmatch(r'org-[a-f0-9]{32}',tenant_id):frappe.throw('Invalid registry identity')
    if frappe.conf.get('il_control_plane') or hostname(site_hostname)!=frappe.local.site:frappe.throw('Wrong target site')
    if frappe.conf.get('il_tenant_id') not in (None,'',tenant_id):frappe.throw('Site belongs to another organization')
    from .domain import institute_code
    from .contact import email_address
    code=institute_code(code);admin_email=email_address(admin_email)
    from frappe.installer import update_site_config
    update_site_config('il_tenant_id',tenant_id)
    frappe.conf.il_tenant_id=tenant_id
    if not frappe.db.exists('User',admin_email):
        frappe.get_doc({'doctype':'User','email':admin_email,'first_name':title[:100],
            'enabled':1,'user_type':'Website User','send_welcome_email':0}).insert(ignore_permissions=True)
    rows=frappe.get_all('IL Institute',fields=['name','code'])
    if rows:
        if len(rows)!=1 or rows[0].code!=code:frappe.throw('Existing institute identity differs')
        member=frappe.db.exists('IL Member',{'institute':rows[0].name,'user':admin_email,'role':'Admin','active':1})
        if not member:frappe.throw('Existing site admin differs; operator review required')
    else:
        from .setup import configure
        configure(code,title,admin_email)
    from .patches.final_build import execute
    execute()
    from .patches.release_v2 import execute as release_v2
    release_v2()
    from .saas import audit
    audit('Initialize tenant',tenant_id,'Site initialized; signed plan manifest still required')
    frappe.db.commit()
    return {'tenant_id':tenant_id,'initialized':True,'requires_signed_manifest':True,'requires_admin_invitation':True}

def invite_admin(admin_email):
    """Explicit operator step after outgoing mail is configured. No fixed passwords."""
    if not frappe.db.exists('IL Member',{'user':admin_email,'role':'Admin','active':1}):frappe.throw('Named institute admin required')
    if not frappe.db.exists('Email Account',{'enable_outgoing':1}):frappe.throw('Configure outgoing email before invitation')
    frappe.get_doc('User',admin_email).reset_password(send_email=True)
    from .saas import audit
    audit('Invite tenant admin',admin_email,'Password setup email queued')
    frappe.db.commit()
    return {'queued':True}
