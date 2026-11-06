"""Prepare the existing, explicitly authorized staging teacher for classroom tests."""
import os
import json
import traceback
from pathlib import Path
from datetime import timedelta

SITE = 'staging.sisuacademylk.com'
EMAIL = 'sisu.student.test+hnb@gmail.com'
MARKER = 'SISU HNB SANDBOX TEST ONLY'
TITLE = '[TEST] Bank-slip enrollment practice'
STAGE = 'checking staging account'


def main():
    global STAGE
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    import frappe
    from frappe.utils import now_datetime
    os.chdir('/home/sisu/frappe-bench/sites')
    frappe.init(site=SITE, sites_path='/home/sisu/frappe-bench/sites')
    frappe.connect()
    try:
        if frappe.local.site != SITE or frappe.conf.get('il_shared_campus_enabled'):
            raise RuntimeError('Expected single-institute staging site')
        user = frappe.get_doc('User', EMAIL)
        if user.first_name != MARKER or not user.enabled:
            raise RuntimeError('Expected enabled staging fixture account')
        frappe.set_user(EMAIL)
        from institute_lms.api import identity, save_classroom, classroom_for, access
        inst, member = identity()
        if member.role != 'Teacher':
            raise RuntimeError('Expected existing teacher membership')
        frappe.set_user('Administrator')
        STAGE = 'saving staging provider profile'
        from institute_lms.profiles import write
        name = frappe.db.get_value('IL Public Profile', {'user': EMAIL}, 'name')
        if name:
            profile = frappe.get_doc('IL Public Profile', name)
            if profile.username != 'sisu_hnb_staging_teacher' or profile.kind != 'Teacher':
                raise RuntimeError('Existing profile differs from staging fixture')
        else:
            profile = frappe.get_doc(dict(doctype='IL Public Profile', user=EMAIL,
                username='sisu_hnb_staging_teacher', display_name='[TEST] Staging Teacher',
                kind='Teacher', country='Sri Lanka', bio='Staging classroom test fixture.'))
        profile.status = 'Verified'
        profile.review_reason = 'Authorized staging-only test fixture; no real-world identity verification asserted.'
        profile.reviewed_by = 'Administrator'
        write(profile)
        from institute_lms.account_billing import account, sync_provider
        STAGE = 'preparing classroom trial access'
        sub = account(inst, member, create=True)
        if sub.plan == 'Individual':
            frappe.db.set_value('IL Account Subscription', sub.name,
                {'plan': 'Gold', 'trial_until': now_datetime() + timedelta(days=30)})
            sub.reload()
            sync_provider(sub)
        frappe.set_user(EMAIL)
        STAGE = 'creating practice classroom'
        existing = frappe.get_all('IL Classroom', filters={'institute': inst.name,
            'owner_user': EMAIL, 'title': TITLE}, pluck='name', limit_page_length=2)
        if len(existing) > 1:
            raise RuntimeError('Duplicate test classrooms require review')
        if existing:
            room_name = existing[0]
        else:
            room_name = save_classroom(dict(title=TITLE, subject='Classroom testing',
                description='STAGING ONLY. Use a fictional payment proof. Do not transfer money.',
                motivation='Learn together', fee=100, fee_mode='Paid', published=1,
                public_provider=profile.name, billing_type='One-time', paid_access_kind='Month',
                access_duration_days=30))
        STAGE = 'checking teacher classroom access'
        _, _, room = classroom_for(room_name, write=True)
        decision = access(room, member)
        if not decision.get('allowed'):
            raise RuntimeError('Classroom plan access check failed; changes rolled back')
        from institute_lms.commercial import account_for, save
        account = account_for(room)
        if not account.bank_instructions:
            account.bank_instructions = 'STAGING TEST ONLY - DO NOT TRANSFER MONEY. Bank: Demo Bank. Account holder: SISU Test Teacher. Account: TEST-0000 (not a real bank account). Branch: Test. Upload a text file saying TEST PAYMENT ONLY.'
            save(account)
        frappe.db.commit()
        print('READY: ' + EMAIL + ' has a staging-only approved test provider profile.')
        print('CLASSROOM: ' + TITLE + ' (' + room_name + ')')
        print('PASS: teacher classroom creation/ownership and plan access checks.')
        try:
            from institute_lms.live_provider import settings
            settings()
            print('LiveKit configuration and server library present; live connection not yet tested.')
        except Exception:
            print('PENDING: LiveKit configuration or server library unavailable. No live session started.')
        print('Sign out/in on staging, select Teacher, then open My classrooms.')
        print('No SMS/email sent. Public accounts, payment settings and existing invoices unchanged.')
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        frames = [{'file': Path(f.filename).name, 'function': f.name, 'line': f.lineno}
                  for f in traceback.extract_tb(exc.__traceback__)]
        print(json.dumps({'stage': STAGE, 'exception': type(exc).__name__, 'frames': frames}))
        print('STOPPED: ' + type(exc).__name__ + '. No credentials displayed.')
        raise SystemExit(1) from None
