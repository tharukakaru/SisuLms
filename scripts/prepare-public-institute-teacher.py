"""Create a labelled teacher in the existing demo institute; never grant admin rights."""
import hashlib
import importlib.util
import os
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

EMAIL = 'sisu.student.test+institute.teacher@gmail.com'
USERNAME = 'sisu_test_institute_teacher'
TITLE = '[TEST] Institute teacher assigned practice'

def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    spec = importlib.util.spec_from_file_location('fixture_helpers', Path(__file__).with_name('prepare-public-test-teacher.py'))
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    import frappe, requests, smtplib
    from frappe.utils.password import update_password
    from institute_lms.signup_rules import password
    from institute_lms.profiles import write
    from institute_lms.membership_write import authorized_insert
    os.chdir('/home/sisu/frappe-bench/sites')
    frappe.init(site='sisuacademylk.com', sites_path='/home/sisu/frappe-bench/sites')
    frappe.connect()
    try:
        if not frappe.conf.get('il_shared_campus_enabled') or not frappe.conf.get('il_payments_paused'):
            raise RuntimeError('Expected public shared campus with gateway paused')
        inst = frappe.db.get_value('IL Institute', {'code': 'SISUDEMO'}, 'name')
        provider = frappe.db.get_value('IL Public Profile', {'workspace': inst, 'kind': 'Institute', 'status': 'Verified'}, 'name') if inst else None
        if not provider or not str(frappe.db.get_value('IL Public Profile', provider, 'display_name')).startswith('[DEMO]'):
            raise RuntimeError('Existing labelled demo institute required; no changes made')
        prior = frappe.db.get_value('IL Public Profile', {'user': EMAIL}, ['name', 'kind', 'username'], as_dict=True)
        if frappe.db.exists('User', EMAIL) and (not prior or prior.kind != 'Teacher' or prior.username != USERNAME):
            raise RuntimeError('Existing account conflict; no changes made')
        secret = helpers.ask_password(password)
        frappe.set_user('Administrator')
        with ExitStack() as stack:
            for obj, attr, fn in ((frappe, 'sendmail', helpers.deny), (frappe, 'enqueue', helpers.deferred),
                    (frappe, 'publish_realtime', lambda *a, **k: None),
                    (requests.sessions.Session, 'request', helpers.deny), (smtplib.SMTP, 'sendmail', helpers.deny)):
                stack.enter_context(patch.object(obj, attr, fn))
            if not frappe.db.exists('User', EMAIL):
                frappe.get_doc(dict(doctype='User', email=EMAIL, first_name='SISU Institute Test', last_name='Teacher',
                    enabled=1, user_type='Website User', send_welcome_email=0, new_password=secret)).insert(ignore_permissions=True)
            else:
                if not frappe.db.get_value('User', EMAIL, 'enabled'):
                    raise RuntimeError('Existing fixture is disabled; review required')
                update_password(EMAIL, secret, logout_all_sessions=True)
            profile = frappe.get_doc('IL Public Profile', prior.name) if prior else frappe.get_doc(dict(
                doctype='IL Public Profile', user=EMAIL, kind='Teacher', username=USERNAME,
                display_name='[TEST] Institute Teacher', country='Sri Lanka'))
            profile.status = 'Verified'
            profile.review_reason = 'Operator-approved test identity; no phone or email verification asserted.'
            profile.reviewed_by = 'Administrator'
            write(profile)
            key = hashlib.sha256(f'{EMAIL}:{provider}:Teacher membership'.encode()).hexdigest()
            existing = frappe.db.get_value('IL Profile Relationship', {'relationship_key': key}, 'name')
            if existing:
                relation = frappe.get_doc('IL Profile Relationship', existing)
                if relation.status != 'Active':
                    raise RuntimeError('Previous affiliation decision requires review')
            else:
                relation = frappe.get_doc(dict(doctype='IL Profile Relationship', relationship_key=key,
                    profile=provider, user=EMAIL, kind='Teacher membership', status='Active',
                    reviewed_by='Administrator', reason='Isolated public teacher test fixture'))
                relation.flags.community_service = True
                relation.insert(ignore_permissions=True)
            member_name = frappe.db.get_value('IL Member', {'institute': inst, 'user': EMAIL}, 'name')
            if member_name:
                member = frappe.get_doc('IL Member', member_name)
                if member.role != 'Teacher' or not member.active:
                    raise RuntimeError('Existing membership conflict')
            else:
                member = frappe.get_doc(dict(doctype='IL Member', institute=inst, user=EMAIL, role='Teacher',
                    active=1, full_name='[TEST] Institute Teacher', language='en', email_opt_in=0, whatsapp_opt_in=0))
                with authorized_insert(member):
                    member.insert(ignore_permissions=True)
            room = frappe.db.get_value('IL Classroom', {'institute': inst, 'title': TITLE}, 'name')
            if room:
                existing_room = frappe.get_doc('IL Classroom', room)
                if existing_room.teacher != member.name or existing_room.owner_type != 'Institute':
                    raise RuntimeError('Test classroom conflict')
            else:
                doc = frappe.get_doc(dict(doctype='IL Classroom', institute=inst, teacher=member.name,
                    title=TITLE, subject='Teacher testing', description='Labelled institute assignment test. No payment.',
                    owner_type='Institute', public_provider=provider, teacher_access='Teaching only',
                    teacher_assignment_active=1, published=0, fee=0, fee_mode='Free', billing_type='One-time',
                    active=1, comments_enabled=1))
                doc.insert(ignore_permissions=True)
                room = doc.name
            frappe.db.commit()
        print('READY: '+EMAIL+'; select the demo institute after Teacher email/password login.')
        print('CLASSROOM: '+room+' '+TITLE)
        print('No owner/admin privileges, OTP, SMS or email. No existing assignments or payment settings changed.')
        print('NOT PROVEN: institute-paid coverage after personal trial expiry; this setup does not extend trials or mark subscriptions paid.')
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
