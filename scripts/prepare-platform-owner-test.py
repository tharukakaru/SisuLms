"""Create a dedicated Platform owner test login; password is entered in the SSH TTY."""
import os
import sys
import secrets
from pathlib import Path
from getpass import getpass
from contextlib import ExitStack
from unittest.mock import patch

SITE='platform.sisuacademylk.com'
EMAIL='sisu.student.test+platform.owner@gmail.com'
LABEL='[TEST] Platform Owner'

def deny(*args,**kwargs):
    raise RuntimeError('Unexpected outgoing message; setup rolled back')

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu') or not sys.stdin.isatty():
        raise RuntimeError('Run as sisu with ssh -t for private password entry')
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    from frappe.utils.password import update_password,check_password
    from institute_lms.signup_rules import password as validate_password
    frappe.init(site=SITE);frappe.connect()
    try:
        from institute_lms import owner_access,portal_session,portal_policy,release
        from institute_lms.wallet import audit
        if not frappe.conf.get('il_control_plane') or not owner_access.is_owner(owner_access.primary_email()):
            raise RuntimeError('Existing configured platform owner required')
        if EMAIL==owner_access.primary_email():raise RuntimeError('Test login must not replace the primary owner')
        if frappe.db.exists('IL Member',{'user':EMAIL}) or frappe.db.exists('IL Public Profile',{'user':EMAIL}):
            raise RuntimeError('This address already has a learner/provider profile; no changes made')
        if frappe.db.exists('User',EMAIL) and frappe.db.get_value('User',EMAIL,'first_name')!=LABEL:
            raise RuntimeError('An unrelated account already uses this address; no changes made')
        secret=getpass('New Platform owner test password (12-128 characters, hidden): ')
        confirmation=getpass('Confirm password (hidden): ')
        validate_password(secret,confirmation)
        with ExitStack() as stack:
            stack.enter_context(patch.object(frappe,'sendmail',side_effect=deny))
            stack.enter_context(patch.object(frappe,'enqueue',return_value=None))
            stack.enter_context(patch.object(frappe,'publish_realtime',return_value=None))
            frappe.set_user('Administrator')
            frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(owner_access.primary_email(),))
            if not frappe.db.exists('User',EMAIL):
                frappe.get_doc({'doctype':'User','email':EMAIL,'first_name':LABEL,'enabled':1,'user_type':'Website User','send_welcome_email':0}).insert(ignore_permissions=True)
            elif not frappe.db.get_value('User',EMAIL,'enabled'):
                raise RuntimeError('Test account is disabled; no changes made')
            name=frappe.db.get_value('IL Owner Access',{'user':EMAIL},'name')
            access=frappe.get_doc('IL Owner Access',name) if name else frappe.get_doc({'doctype':'IL Owner Access','user':EMAIL})
            access.enabled=1;access.granted_by='Administrator'
            access.reason='User-authorized dedicated Platform owner test login for client acceptance.'
            access.flags.owner_access_service=True;access.save(ignore_permissions=True)
            update_password(EMAIL,secret,logout_all_sessions=True)
            assert check_password(EMAIL,secret)==EMAIL
            audit('Platform owner test login prepared',EMAIL,access.reason)
            frappe.set_user(EMAIL);frappe.session.data.csrf_token=secrets.token_hex(32)
            portal_policy.validate_login(type('Login',(),{'user':EMAIL})())
            assert owner_access.is_owner()
            assert portal_session.current()['role']=='Super Admin'
            assert isinstance(release.control_room()['organizations'],list)
            assert not owner_access.access_list()['can_manage']
            frappe.db.commit()
        print('READY: '+EMAIL)
        print('SIGN IN: https://platform.sisuacademylk.com/campus using email and the password you entered.')
        print('PASS: password verification, Platform owner routing and owner panel access.')
        print('Primary-owner access administration remains with the existing primary owner. Personal login unchanged.')
        print('No email/SMS sent, payment settings changed or learner/institute roles added. No restart required.')
        print('Rerunning resets only this named test login password. Password was not printed or saved to a file.')
    finally:
        frappe.db.rollback();frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,(RuntimeError,ValueError)) else type(exc).__name__)+'. No password displayed.')
        raise SystemExit(1) from None
