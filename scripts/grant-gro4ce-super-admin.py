"""Grant the explicitly requested account delegated owner access on the control plane."""
import logging
import os
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
SITE='platform.sisuacademylk.com'
EMAIL='gro4celk@gmail.com'

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):
        raise RuntimeError('Run as sisu on the SISU server')
    logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH/'sites')
    frappe.init(site=SITE,sites_path=str(BENCH/'sites'))
    try:
        frappe.connect();frappe.set_user('Administrator')
        from institute_lms.owner_access import is_owner,primary_email
        if not frappe.conf.get('il_control_plane') or not frappe.conf.get('il_owner_provisioned') or not is_owner(primary_email()):
            raise RuntimeError('Existing control-plane owner configuration required')
        if not frappe.db.exists('Social Login Key',{'name':'google','enable_social_login':1}):
            raise RuntimeError('Google login must be configured first')
        if frappe.db.exists('IL Member',{'user':EMAIL}) or frappe.db.exists('IL Public Profile',{'user':EMAIL}):
            raise RuntimeError('This email has a learner/provider profile on the control plane; access was not changed')
        frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(primary_email(),))
        if frappe.db.exists('User',EMAIL):
            if not frappe.db.get_value('User',EMAIL,'enabled'):
                raise RuntimeError('Existing user is disabled; access was not changed')
        else:
            frappe.get_doc({'doctype':'User','email':EMAIL,'first_name':'Gro4ce','enabled':1,
                'user_type':'Website User','send_welcome_email':0}).insert(ignore_permissions=True)
        name=frappe.db.get_value('IL Owner Access',{'user':EMAIL},'name')
        if EMAIL!=primary_email():
            doc=frappe.get_doc('IL Owner Access',name) if name else frappe.get_doc({'doctype':'IL Owner Access','user':EMAIL})
            if not name or not doc.enabled:
                doc.enabled=1;doc.granted_by='Administrator'
                doc.reason='Explicit user request: grant gro4celk@gmail.com Super Admin panel access using Google login.'
                doc.flags.owner_access_service=True;doc.save(ignore_permissions=True)
                from institute_lms.wallet import audit
                audit('Super Admin access granted',EMAIL,doc.reason)
        if not is_owner(EMAIL):raise RuntimeError('Owner access check failed')
        frappe.db.commit()
        print('GRANTED: '+EMAIL+' Super Admin access on '+SITE)
        print('Open https://platform.sisuacademylk.com/campus and sign in with Google using this exact email.')
        print('No passwords set, messages sent, primary owner changed or Teen account modified. No restart required.')
    except Exception:
        frappe.db.rollback();raise
    finally:
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__)+'. No credentials displayed.')
        raise SystemExit(1) from None
