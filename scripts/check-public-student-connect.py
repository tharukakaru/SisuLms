"""Read-only public student bridge acceptance with both production request guards."""
import os
from pathlib import Path
from types import SimpleNamespace

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com')
    frappe.connect()
    try:
        frappe.set_user('sisu.student.test@gmail.com')
        from institute_lms import public_student, account_billing, saas
        from institute_lms.campus_context import SESSION_KEY
        # Request-local only: exercise None/overall without updating the session.
        frappe.session.data.pop(SESSION_KEY,None)
        from frappe.utils import today, add_days
        operations={
            'choices':lambda:public_student.choices(),
            'classes':lambda:public_student.classes(profile='',page=0),
            'billing':lambda:public_student.billing(),
            'schedule':lambda:public_student.schedule(starts_on=today(),ends_on=add_days(today(),31)),
        }
        for name,run in operations.items():
            frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.public_student.'+name)
            frappe.local.form_dict=frappe._dict()
            account_billing.guard_request()
            saas.guard_request()
            result=run()
            assert result is not None
            print('PASS: public student '+name+' through both request guards, with no selected institute.')
        print('READ ONLY: rolled back; no payments, messages, enrollment or persistent session changes. Browser acceptance still required.')
    finally:
        frappe.db.rollback()
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED:',type(exc).__name__,'during public student acceptance; private details withheld.')
        raise SystemExit(1) from None
