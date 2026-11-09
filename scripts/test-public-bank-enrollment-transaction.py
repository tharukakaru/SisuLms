"""Public-site API acceptance in a rollback-only transaction, not a real payment.

No browser authentication is simulated as evidence. An operator temporarily
uses demo identities inside this uncommittable transaction. No credentials,
account activation, invoice, entitlement or message survives it.
"""
import io
import logging
import os
import time
import uuid
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

BENCH = Path('/home/sisu/frappe-bench')
ADMIN = 'sisu-public-demo-admin@example.invalid'
STUDENT = 'sisu.student.test@gmail.com'
STAGE = 'preflight'


def deny(*a, **kw):
    raise RuntimeError('Commit or external delivery attempted during rollback test')


def deferred(*a, **kw):
    if kw.get('enqueue_after_commit') is True and not kw.get('now'):
        return
    deny()


def refresh(event=None, *a, **kw):
    # Never publish realtime notifications from an uncommitted test, including
    # Frappe's immediate attachment-comment updates.
    return None


def main():
    global STAGE
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    logging.disable(logging.CRITICAL)
    import frappe
    import requests
    import smtplib
    from werkzeug.datastructures import FileStorage
    from frappe.utils import today
    from institute_lms import api, catalog, commercial, class_keys, account_confirmations
    from institute_lms.membership_write import authorized_insert
    os.chdir(BENCH / 'sites')
    frappe.init(site='sisuacademylk.com', sites_path=str(BENCH / 'sites'))
    frappe.connect()
    token = uuid.uuid4().hex
    proof = None
    proof_path = None
    proof_url = None
    room = None
    throttle = None
    try:
        inst_name = frappe.db.get_value('IL Institute', {'code': 'SISUDEMO'}, 'name')
        if not inst_name or not frappe.conf.get('il_payments_paused'):
            raise RuntimeError('Public demo institute and gateway payment pause required')
        if frappe.db.get_value('User', ADMIN, 'enabled'):
            raise RuntimeError('Expected disabled demo administrator')
        student = frappe.db.get_value('IL Member', {'institute': inst_name, 'user': STUDENT, 'active': 1, 'role': 'Student'}, 'name')
        if not student:
            raise RuntimeError('Registered public test student required')
        inst = frappe.get_doc('IL Institute', inst_name)
        with ExitStack() as stack:
            for obj, attr, fn in ((frappe.db, 'commit', deny), (frappe, 'sendmail', deny),
                    (frappe, 'enqueue', deferred), (frappe, 'publish_realtime', refresh),
                    (requests.sessions.Session, 'request', deny), (smtplib.SMTP, 'sendmail', deny)):
                stack.enter_context(patch.object(obj, attr, fn))
            frappe.set_user('Administrator')
            # These changes are uncommittable and invisible to other DB sessions.
            frappe.db.set_value('User', ADMIN, 'enabled', 1, update_modified=False)
            other_user = 'rollback-'+token+'@example.invalid'
            frappe.get_doc(dict(doctype='User', email=other_user, first_name='Rollback test', enabled=1,
                user_type='Website User', send_welcome_email=0)).insert(ignore_permissions=True)
            other = frappe.get_doc(dict(doctype='IL Member', institute=inst_name, user=other_user,
                full_name='[ROLLBACK TEST] Other student', role='Student', active=1, language='en',
                email_opt_in=0, whatsapp_opt_in=0))
            with authorized_insert(other):
                other.insert(ignore_permissions=True)
            template = frappe.get_doc('IL Classroom', frappe.db.get_value('IL Classroom',
                {'institute': inst_name, 'title': '[DEMO] Locked class - do not pay'}, 'name'))
            room = frappe.copy_doc(template)
            room.title = '[ROLLBACK TEST] Bank payment ' + token
            room.fee = 100
            room.billing_type = 'One-time'
            room.access_duration_days = 30
            room.insert(ignore_permissions=True)

            def actor(user):
                frappe.set_user(user)
                frappe.local.student_request_institute = inst_name
                # CLI-only operator test context; never persisted to a web session.
                frappe.session.data.il_google_session = True

            def rejected(call):
                try:
                    call()
                except (frappe.ValidationError, frappe.PermissionError):
                    return
                raise RuntimeError('Expected invalid operation to be rejected')

            STAGE = 'class selection and automatic invoice'
            actor(STUDENT)
            joined = catalog.join_class(room.name)
            invoice = frappe.db.get_value('IL Invoice', {'enrollment': joined['enrollment']}, 'name')
            if not invoice:
                raise RuntimeError('Class selection did not create its invoice')
            assert float(frappe.db.get_value('IL Invoice', invoice, 'amount')) == 100
            print('PASS: class selection creates its LKR 100 invoice automatically.')
            STAGE = 'private slip upload and pending status'
            frappe.local.request = frappe._dict(files={'file': FileStorage(
                stream=io.BytesIO(('DEMO ONLY - no transfer made - '+token).encode()), filename='demo-slip.txt')})
            proof = commercial.upload_proof()['name']
            proof_doc = frappe.get_doc('File', proof)
            proof_path = Path(proof_doc.get_full_path())
            proof_url = proof_doc.file_url
            slip = commercial.submit_slip(invoice, proof, 'ROLLBACK-'+token, 100, today())
            assert slip['status'] == 'Pending'
            assert any(x.name == slip['name'] and x.status == 'Pending' for x in commercial.slips())
            rejected(lambda: commercial.review_slip(slip['name'], 'Approved', 'Operator rollback test'))
            print('PASS: uploaded slip appears Pending; student cannot approve their own slip.')
            STAGE = 'provider approval and personal key'
            keys = []
            original_send = class_keys.send_key

            def capture(user, reference, classroom, key):
                keys.append(key)
                return original_send(user, reference, classroom, key)

            stack.enter_context(patch.object(class_keys, 'send_key', capture))
            actor(ADMIN)
            assert commercial.review_slip(slip['name'], 'Approved', 'ROLLBACK TEST - no actual bank transfer')['status'] == 'Approved'
            assert frappe.db.get_value('IL Invoice', invoice, 'status') == 'Paid'
            access = frappe.db.get_value('IL Paid Access', {'invoice': invoice}, 'name')
            assert frappe.db.get_value('IL Paid Access', access, 'status') == 'Awaiting key'
            assert keys
            actor(STUDENT)
            assert class_keys.key_status(room.name)['payment_approved']
            assert any(x.name == slip['name'] and x.status == 'Approved' for x in commercial.slips())
            print('PASS: provider approval updates student history and requires a personal key before access.')
            STAGE = 'foreign student and expired key rejection'
            actor(other_user)
            rejected(lambda: class_keys.redeem(room.name, keys[-1]))
            actor(STUDENT)
            expired = str(int(time.time())-901)+'-'+('A'*16)
            frappe.db.set_value('IL Paid Access', access, 'enrollment_key_hash', class_keys.digest(expired))
            rejected(lambda: class_keys.redeem(room.name, expired))
            throttle = 'il_class_key_resend:'+access
            assert class_keys.resend(room.name)['expires_in_seconds'] == 900
            rejected(lambda: class_keys.redeem(room.name, expired))
            assert class_keys.redeem(room.name, keys[-1])['enrolled']
            rejected(lambda: class_keys.redeem(room.name, keys[-1]))
            assert commercial.access_granted(room, frappe.get_doc('IL Member', student))
            print('PASS: other students and expired/used keys rejected; resend and one-time redemption grant access.')
    finally:
        frappe.db.rollback()
        # The rolled-back File and slip must not be deleted through document hooks.
        # Remove only this run's exact local payload, with no surviving references.
        if proof_path and proof_path.exists():
            root = Path(frappe.get_site_path('private', 'files')).resolve()
            expected = ('DEMO ONLY - no transfer made - '+token).encode()
            if (proof_path.is_symlink() or proof_path.resolve().parent != root
                    or proof_path.read_bytes() != expected
                    or frappe.db.exists('File', {'file_url': proof_url})
                    or frappe.db.exists('IL Stored Object', {'storage_key': proof_url})):
                raise RuntimeError('Temporary proof retained: cleanup safety check failed')
            proof_path.unlink()
            print('PASS: exact temporary proof removed after database rollback.')
        if throttle:
            frappe.cache.delete_value(throttle)
        # Avoid retaining the CLI operator Google-session flag.
        if getattr(frappe, 'session', None):
            frappe.session.data.pop('il_google_session', None)
        assert not frappe.db.get_value('User', ADMIN, 'enabled')
        if room:
            assert not frappe.db.exists('IL Classroom', room.name)
        frappe.destroy()
    print('ROLLED BACK: no test invoice, approval, account activation, access or message retained.')
    print('NOT TESTED: browser teacher login, SMS/email delivery or a real bank transfer.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        import json, traceback
        print(json.dumps({'failure_frames': [{'file': Path(f.filename).name, 'function': f.name, 'line': f.lineno}
            for f in traceback.extract_tb(exc.__traceback__)[-6:]]}))
        print('STOPPED at '+STAGE+': '+type(exc).__name__+'. '+(str(exc) if isinstance(exc, RuntimeError) else 'Raw details withheld.'))
        raise SystemExit(1) from None
