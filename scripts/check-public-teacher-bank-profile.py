"""Check named independent teacher bank settings; roll back all writes."""
import hashlib
import json
import os
import secrets
import tarfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def main():
    app = Path('/home/sisu/frappe-bench/apps/institute_lms')
    with tarfile.open('/tmp/sisu-teacher-bank-profile.tgz') as archive:
        manifest = json.load(archive.extractfile('manifest.json'))
    for name, entry in manifest.items():
        assert hashlib.sha256((app/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() == entry['after'], name
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com'); frappe.connect()
    try:
        from institute_lms import class_keys, account_billing, saas
        from institute_lms.campus_context import SESSION_KEY
        user = 'sisu.student.test+teacher@gmail.com'
        inst = frappe.db.get_value('IL Institute', {'code':'SISUTESTTC'}, 'name')
        assert inst and frappe.db.get_value('User', user, 'enabled')
        frappe.set_user(user)
        frappe.session.data[SESSION_KEY] = inst
        frappe.session.data.csrf_token = secrets.token_hex(32)
        def call(method, **args):
            frappe.local.request = SimpleNamespace(path='/api/method/institute_lms.class_keys.'+method)
            frappe.local.form_dict = frappe._dict(args)
            account_billing.guard_request(); saas.guard_request()
            return getattr(class_keys, method)(**args)
        def denied(fn):
            try: fn()
            except (frappe.PermissionError, frappe.ValidationError): return
            raise AssertionError('Expected permission/validation denial')
        accounts = frappe.get_all('IL Provider Account',fields=['name','bank_instructions'])
        before = {r.name:r.bank_instructions for r in accounts}
        own = class_keys.independent_bank_account().name
        rooms = frappe.get_all('IL Classroom',filters={'owner_type':'Teacher','owner_user':user,'institute':inst},pluck='name')
        assert rooms, 'Named teacher has no classrooms to verify'
        with patch.object(frappe,'sendmail',side_effect=AssertionError('No test mail')), patch.object(frappe,'enqueue',return_value=None):
            denied(lambda:call('save_teacher_bank_details',instructions='bad'))
            for details in ('ROLLBACK TEST / Test bank / 000000000 / Test branch','ROLLBACK UPDATED / Test bank / 111111111 / Test branch'):
                call('save_teacher_bank_details',instructions=details)
                assert call('teacher_bank_details')['instructions'] == details
                for room in rooms:
                    assert call('bank_details',classroom=room)['instructions'] == details
                after = frappe.get_all('IL Provider Account',fields=['name','bank_instructions'])
                assert all(r.bank_instructions == before[r.name] for r in after if r.name != own)
            denied(lambda:call('save_institute_bank_details',instructions='Unauthorized institute account'))
            print('PASS: shared teacher account updates all owned classrooms; other receiving accounts unchanged; institute writes denied.')
            student = 'sisu.student.test@gmail.com'
            assert frappe.db.exists('IL Member',{'user':student,'institute':inst,'active':1,'role':'Student'})
            frappe.set_user(student);frappe.session.data[SESSION_KEY]=inst
            denied(lambda:call('save_teacher_bank_details',instructions='Unauthorized student account'))
            print('PASS: student cannot change teacher bank details.')
    finally:
        frappe.db.rollback();frappe.destroy()
        print('ROLLED BACK: no bank details or payment changes retained. No message sent. Browser acceptance remains separate.')


if __name__ == '__main__': main()
