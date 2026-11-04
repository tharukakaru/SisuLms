"""Operator-created, isolated public teacher fixture. No contact verification claims."""
import os
from pathlib import Path
from getpass import getpass
from datetime import timedelta
from contextlib import ExitStack
from unittest.mock import patch

EMAIL = 'sisu.student.test+teacher@gmail.com'
SITE = 'sisuacademylk.com'
CODE = 'SISUTESTTC'
LABEL = '[TEST] Independent teacher workspace'

def deny(*args, **kwargs):
    raise RuntimeError('Unexpected external delivery; setup rolled back')

def deferred(*args, **kwargs):
    if kwargs.get('enqueue_after_commit') and not kwargs.get('now'):
        return
    deny()

def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    import frappe, requests, smtplib
    from frappe.utils import now_datetime
    from frappe.utils.password import update_password
    from institute_lms.signup_rules import password as validate_password
    from institute_lms.domain import institute_code
    from institute_lms.campus_provisioning import institute_insert
    from institute_lms.membership_write import authorized_insert
    from institute_lms.profiles import write
    from institute_lms.account_billing import account, sync_provider
    from institute_lms.api import save_classroom, classroom_for
    os.chdir('/home/sisu/frappe-bench/sites')
    frappe.init(site=SITE, sites_path='/home/sisu/frappe-bench/sites')
    frappe.connect()
    try:
        if not frappe.conf.get('il_shared_campus_enabled') or not frappe.conf.get('il_payments_paused'):
            raise RuntimeError('Expected public shared campus with gateway paused')
        institute_code(CODE)  # Validate fixture identifiers before any account writes.
        secret = getpass('New public test teacher password (12+ characters, hidden): ')
        validate_password(secret, getpass('Confirm password (hidden): '))
        frappe.set_user('Administrator')
        with ExitStack() as stack:
            for obj, attr, fn in ((frappe, 'sendmail', deny), (frappe, 'enqueue', deferred),
                    (frappe, 'publish_realtime', lambda *a, **k: None),
                    (requests.sessions.Session, 'request', deny), (smtplib.SMTP, 'sendmail', deny)):
                stack.enter_context(patch.object(obj, attr, fn))
            name = frappe.db.get_value('IL Public Profile', {'user': EMAIL}, 'name')
            if name and frappe.db.get_value('IL Public Profile', name, 'kind') != 'Teacher':
                raise RuntimeError('Existing account is not a teacher; no changes made')
            if not frappe.db.exists('User', EMAIL):
                frappe.get_doc(dict(doctype='User', email=EMAIL, first_name='SISU Test',
                    last_name='Teacher', enabled=1, user_type='Website User', send_welcome_email=0,
                    new_password=secret)).insert(ignore_permissions=True)
            else:
                if not frappe.db.get_value('User', EMAIL, 'enabled'):
                    raise RuntimeError('Existing account disabled; review required')
                update_password(EMAIL, secret, logout_all_sessions=True)
            profile = frappe.get_doc('IL Public Profile', name) if name else frappe.get_doc(dict(
                doctype='IL Public Profile', user=EMAIL, kind='Teacher', username='sisu_test_teacher',
                display_name='[TEST] SISU Independent Teacher', country='Sri Lanka'))
            profile.status = 'Verified'
            profile.review_reason = 'Operator-approved test provider only; no email/phone verification asserted.'
            profile.reviewed_by = 'Administrator'
            profile.bio = 'Labelled test teacher. No real payments or teaching service.'
            write(profile)
            name = frappe.db.get_value('IL Institute', {'code': CODE}, 'name')
            inst = frappe.get_doc('IL Institute', name) if name else frappe.get_doc(dict(
                doctype='IL Institute', code=CODE, title=LABEL, language='en', billing_day=1))
            if name and inst.title != LABEL:
                raise RuntimeError('Test workspace conflict')
            if not name:
                with institute_insert(inst):
                    inst.insert(ignore_permissions=True)
            name = frappe.db.get_value('IL Member', {'institute': inst.name, 'user': EMAIL}, 'name')
            member = frappe.get_doc('IL Member', name) if name else frappe.get_doc(dict(
                doctype='IL Member', institute=inst.name, user=EMAIL, role='Teacher', active=1,
                full_name='[TEST] SISU Independent Teacher', language='en', email_opt_in=0, whatsapp_opt_in=0))
            if name and (member.role != 'Teacher' or not member.active):
                raise RuntimeError('Test membership conflict')
            if not name:
                with authorized_insert(member):
                    member.insert(ignore_permissions=True)
            sub = account(inst, member, create=True)
            if sub.plan == 'Individual':
                frappe.db.set_value('IL Account Subscription', sub.name,
                    {'plan': 'Gold', 'trial_until': now_datetime()+timedelta(days=30)})
                sub.reload()
                sync_provider(sub)
            frappe.set_user(EMAIL)
            frappe.local.student_request_institute = inst.name
            for fee, title in ((0, '[TEST] Free classroom practice'), (100, '[TEST] Bank approval practice - DO NOT PAY')):
                room = frappe.db.get_value('IL Classroom', {'institute': inst.name, 'owner_user': EMAIL, 'title': title}, 'name')
                if not room:
                    room = save_classroom(dict(title=title, subject='Testing',
                        description='Test fixture only. Do not transfer real money.', motivation='Practice only',
                        fee=fee, fee_mode='Paid' if fee else 'Free', published=1,
                        public_provider=profile.name, billing_type='One-time', access_duration_days=30))
                classroom_for(room, write=True)
                print('CLASSROOM: '+room+' '+title)
            frappe.db.commit()
        print('READY: '+EMAIL+'; Teacher email/password login on public campus.')
        print('Select '+LABEL+'. Teacher-owned classes only; no owner/admin privileges.')
        print('No OTP, SMS or email sent. Contact verification unchanged. Payments/WhatsApp unchanged.')
    finally:
        frappe.db.rollback()
        frappe.destroy()

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        import traceback
        print('STOPPED: '+type(exc).__name__)
        print([{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-6:]])
        raise SystemExit(1) from None
