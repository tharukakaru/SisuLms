"""Rollback-only validation of owner billing invitation queueing; no email delivery."""
import os,secrets,traceback,json
from types import SimpleNamespace
from unittest.mock import patch

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='platform.sisuacademylk.com');frappe.connect()
    try:
        from institute_lms import platform,owner_access
        from frappe.email.doctype.email_queue.email_queue import EmailQueue
        frappe.set_user('sisu.student.test+platform.owner@gmail.com')
        frappe.session.data.csrf_token=secrets.token_hex(32)
        assert owner_access.is_owner()
        tenant=frappe.db.get_value('IL Organization',{'site_hostname':'abc.sisuacademylk.com'},'name')
        assert tenant,'ABC test institute not found'
        frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.platform.invite_billing_contact')
        frappe.local.form_dict=frappe._dict(tenant=tenant)
        with patch.object(frappe,'enqueue',return_value=None),patch.object(EmailQueue,'send',side_effect=AssertionError('Diagnostic must not send email')):
            result=platform.invite_billing_contact(tenant)
            assert result['queued']
            print('PASS: owner billing invitation prepared and queued using the configured mail account. No signing key required.')
        frappe.set_user('Guest')
        try:platform.invite_billing_contact(tenant)
        except frappe.PermissionError:print('PASS: guest invitation request denied.')
        else:raise AssertionError('Guest was not denied')
    except Exception as exc:
        print(json.dumps({'exception':type(exc).__name__,'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
        raise SystemExit(1) from None
    finally:
        frappe.db.rollback();frappe.destroy()
        print('ROLLED BACK: no password-setup token, email queue or audit changes retained. No email sent. Inbox delivery requires the browser test.')
if __name__=='__main__':main()
