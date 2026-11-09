"""Named SISUDEMO administrator fixture; password is entered only in the remote TTY."""
import os
import sys
import secrets
from getpass import getpass
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch

EMAIL = 'sisu.student.test+institute.admin@gmail.com'
OLD_OWNER = 'sisu-public-demo-admin@example.invalid'
LABEL = '[TEST] Institute Admin'


def deny(*args, **kwargs):
    raise RuntimeError('Unexpected external delivery; setup rolled back')


def deferred(*args, **kwargs):
    if kwargs.get('enqueue_after_commit') and not kwargs.get('now'):
        return
    deny()


def ask_password(validate):
    if not sys.stdin.isatty():
        raise RuntimeError('Use ssh -t for private password entry')
    for _ in range(5):
        secret = getpass('New institute-admin test password (12-128 characters, hidden): ')
        confirmation = getpass('Confirm password (hidden): ')
        try:
            validate(secret, confirmation)
            return secret
        except ValueError:
            print('Use matching passwords of 12-128 characters. Try again.')
    raise RuntimeError('Password not accepted; no changes made')


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    import frappe, requests, smtplib
    from frappe.utils.password import update_password
    from institute_lms.signup_rules import password
    from institute_lms.profiles import write
    from institute_lms.membership_write import authorized_insert
    from institute_lms.campus_context import SESSION_KEY
    from institute_lms import api, portal_session, account_billing
    os.chdir('/home/sisu/frappe-bench/sites')
    frappe.init(site='sisuacademylk.com'); frappe.connect()
    try:
        if frappe.conf.get('il_shared_campus_enabled') != 1 or not frappe.conf.get('il_payments_paused'):
            raise RuntimeError('Public shared campus with gateway paused required')
        inst_name = frappe.db.get_value('IL Institute', {'code': 'SISUDEMO',
            'title': '[DEMO] SISU Practice Institute'}, 'name')
        if not inst_name:
            raise RuntimeError('Named demo institute missing')
        profiles = frappe.get_all('IL Public Profile', filters={'workspace': inst_name, 'kind': 'Institute'}, pluck='name')
        if len(profiles) != 1:
            raise RuntimeError('Expected exactly one existing demo institute profile')
        profile = frappe.get_doc('IL Public Profile', profiles[0], for_update=True)
        if profile.status != 'Verified' or not profile.display_name.startswith('[DEMO]') or profile.user not in (OLD_OWNER, EMAIL):
            raise RuntimeError('Demo profile ownership conflict')
        if profile.user == OLD_OWNER and frappe.db.get_value('User', OLD_OWNER, 'enabled'):
            raise RuntimeError('Original display owner is enabled; review required')
        existing = frappe.db.get_value('IL Member', {'institute': inst_name, 'user': EMAIL}, 'name')
        if frappe.db.exists('User', EMAIL):
            user = frappe.get_doc('User', EMAIL)
            if (profile.user != EMAIL or not existing or not user.enabled or user.user_type != 'Website User'
                    or set(frappe.get_roles(EMAIL)) & {'System Manager', 'Institute Owner'}):
                raise RuntimeError('Existing account is not the expected test fixture')
        if frappe.db.exists('IL Member', {'user': EMAIL, 'institute': ['!=', inst_name]}):
            raise RuntimeError('Test account has another membership; no changes made')
        if existing:
            member = frappe.get_doc('IL Member', existing)
            if member.role != 'Admin' or not member.active or member.full_name != LABEL:
                raise RuntimeError('Existing demo membership conflict')
        secret = ask_password(password)
        frappe.set_user('Administrator')
        with ExitStack() as stack:
            for obj, attr, fn in ((frappe, 'sendmail', deny), (frappe, 'enqueue', deferred),
                    (frappe, 'publish_realtime', lambda *a, **k: None),
                    (requests.sessions.Session, 'request', deny), (smtplib.SMTP, 'sendmail', deny)):
                stack.enter_context(patch.object(obj, attr, fn))
            if not frappe.db.exists('User', EMAIL):
                frappe.get_doc(dict(doctype='User', email=EMAIL, first_name='SISU Institute Test',
                    last_name='Admin', enabled=1, user_type='Website User', send_welcome_email=0,
                    new_password=secret)).insert(ignore_permissions=True)
            else:
                update_password(EMAIL, secret, logout_all_sessions=True)
            # Preserve the existing profile ID and all classroom/relationship links.
            if profile.user != EMAIL:
                profile.user = EMAIL
                write(profile)
                profile.add_comment('Info', 'Named institute-admin test login attached at operator request; original display owner remains disabled.')
            if not existing:
                member = frappe.get_doc(dict(doctype='IL Member', institute=inst_name, user=EMAIL,
                    role='Admin', active=1, full_name=LABEL, language='en', email_opt_in=0, whatsapp_opt_in=0))
                with authorized_insert(member):
                    member.insert(ignore_permissions=True)
            frappe.set_user(EMAIL)
            frappe.session.data[SESSION_KEY] = inst_name
            frappe.session.data.csrf_token = secrets.token_hex(32)
            # Verify actual portal role and scope before committing the fixture.
            assert portal_session.current()['role'] == 'Admin'
            inst, actor = api.identity()
            assert inst.name == inst_name and actor.role == 'Admin'
            assert api.bootstrap()['member']['provider_profile']['kind'] == 'Institute'
            subscription = account_billing.account(inst, actor)
            status = account_billing.state(subscription)
            if not status['available']:
                raise RuntimeError('Existing demo institute subscription is unavailable; no trial or payment changed')
            frappe.db.commit()
        print('READY: ' + EMAIL)
        print('ROLE: Institute admin; workspace SISUDEMO ([DEMO] SISU Practice Institute).')
        print('PASSWORD: the password you entered privately. No password was printed or stored in a file.')
        print('PASS: portal Admin routing, scoped membership, institute profile and existing subscription access.')
        print('No platform-admin roles, contact verification claims, messages, payment changes or classroom reassignment.')
        print('Rerunning this script resets only this named test login password.')
    finally:
        frappe.db.rollback(); frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        import traceback
        print('STOPPED: ' + (str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__))
        print([{'file': Path(f.filename).name, 'function': f.name, 'line': f.lineno}
            for f in traceback.extract_tb(exc.__traceback__)[-6:]])
        raise SystemExit(1) from None
