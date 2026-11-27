"""Admin access invitations: Administrator invites, invitee accepts once within 24 hours.

Flow: an Administrator enters name + email + level -> a single-use link is emailed.
The invitee opens /admin-invite, confirms the same email, verifies a mobile number
by SMS code and sets a password. Access is granted, they are signed in and a
welcome email is sent. The link stops working once accepted, when a newer invite
replaces it, when it is cancelled, or 24 hours after it was sent.
Only the token's SHA-256 is stored; the code is kept as an HMAC in cache.
"""
from .message_templates import verification_sms
import hashlib
import hmac
import re
import secrets
import time
from html import escape

import frappe
from .message_templates import sendmail
from frappe.utils import add_to_date, get_datetime, now_datetime

from .owner_access import LEVELS, primary_email, require_manager, can_manage

INVITE_HOURS = 24
CODE_SECONDS = 600
INVALID = 'This invitation link is invalid, already used or has expired. Ask an Administrator to send a new invitation.'


def token_hash(token):
    return hashlib.sha256(str(token or '').encode()).hexdigest()


def clean_email(email):
    return str(email or '').strip().lower()


def base_url():
    configured = frappe.conf.get('il_admin_invite_base_url')
    if configured:
        return str(configured).rstrip('/')
    request = getattr(frappe.local, 'request', None)
    if request is not None and getattr(request, 'host_url', None):
        return request.host_url.rstrip('/')
    from frappe.utils import get_url
    return get_url().rstrip('/')


def audit(action, reference, details=''):
    from .wallet import audit as write
    write(action, reference, details)


# ---------------------------------------------------------------- Administrator side

@frappe.whitelist(methods=['POST'])
def invite(full_name, email, access_level='Admin'):
    require_manager()
    from frappe.utils import validate_email_address
    full_name = re.sub(r'\s+', ' ', str(full_name or '')).strip()[:140]
    email = clean_email(email)
    if not full_name:
        frappe.throw('Enter the admin\'s name')
    validate_email_address(email, throw=True)
    if access_level not in LEVELS:
        frappe.throw('Choose Admin or Administrator')
    if email in (primary_email(), 'administrator'):
        frappe.throw('This account already has full access')
    if frappe.db.get_value('IL Owner Access', {'user': email, 'enabled': 1}):
        frappe.throw('This person already has admin access')
    if frappe.db.exists('IL Member', {'user': email}) or frappe.db.exists('IL Public Profile', {'user': email}):
        frappe.throw('Use a dedicated admin email, separate from a student, teacher or institute account')
    if frappe.db.exists('User', email) and not frappe.db.get_value('User', email, 'enabled'):
        frappe.throw('This user account is disabled. Ask the site operator to review it first')
    if not frappe.db.exists('Email Account', {'enable_outgoing': 1}):
        frappe.throw('Configure outgoing email before sending invitations')

    # Only the newest invitation for an address can be used.
    for old in frappe.get_all('IL Admin Invite', filters={'email': email, 'status': 'Pending'}, pluck='name'):
        doc = frappe.get_doc('IL Admin Invite', old)
        doc.status = 'Cancelled'
        doc.flags.admin_invite_service = True
        doc.save(ignore_permissions=True)

    token = secrets.token_urlsafe(32)
    doc = frappe.get_doc({'doctype': 'IL Admin Invite', 'full_name': full_name, 'email': email,
                          'access_level': access_level, 'status': 'Pending', 'token_hash': token_hash(token),
                          'expires_at': add_to_date(now_datetime(), hours=INVITE_HOURS),
                          'invited_by': frappe.session.user})
    doc.flags.admin_invite_service = True
    doc.insert(ignore_permissions=True)

    link = f'{base_url()}/admin-invite?token={token}'
    role = 'Administrator (full authority)' if access_level == 'Administrator' else 'Admin'
    sendmail(frappe,
        recipients=[email], subject='You are invited to manage SISU LMS', now=True,
        message=(f'<p>Hello {escape(full_name)},</p>'
                 f'<p>You have been invited to join the SISU LMS platform as <strong>{escape(role)}</strong>.</p>'
                 f'<p><a href="{escape(link, quote=True)}">Accept the invitation and set up your account</a></p>'
                 f'<p>Use this email address ({escape(email)}) when you open the link. You will verify your '
                 f'mobile number and choose a password.</p>'
                 f'<p>This link works once and expires in {INVITE_HOURS} hours.</p>'
                 '<p>If you did not expect this invitation, you can ignore this email.</p>'),
        redact_message_after_send=True)
    audit('Admin invitation sent', email, f'{access_level} · {full_name}')
    return {'status': f'Invitation sent to {email}. The link expires in {INVITE_HOURS} hours.', 'invite': doc.name}


@frappe.whitelist(methods=['POST'])
def cancel(invite_name):
    require_manager()
    doc = frappe.get_doc('IL Admin Invite', invite_name)
    if doc.status != 'Pending':
        return {'status': 'This invitation is no longer pending'}
    doc.status = 'Cancelled'
    doc.flags.admin_invite_service = True
    doc.save(ignore_permissions=True)
    audit('Admin invitation cancelled', doc.email, doc.full_name)
    return {'status': 'Invitation cancelled; the link no longer works'}


# ---------------------------------------------------------------- Invitee side (guest)

def pending(token, lock=False):
    if not token or len(str(token)) > 200:
        frappe.throw(INVALID)
    name = frappe.db.get_value('IL Admin Invite', {'token_hash': token_hash(token)}, 'name')
    if not name:
        frappe.throw(INVALID)
    if lock:
        frappe.db.sql('SELECT name FROM `tabIL Admin Invite` WHERE name=%s FOR UPDATE', (name,))
    doc = frappe.get_doc('IL Admin Invite', name)
    if doc.status != 'Pending' or get_datetime(doc.expires_at) <= now_datetime():
        frappe.throw(INVALID)
    if not can_manage(doc.invited_by):
        frappe.throw('This invitation is no longer authorized. Ask a current Administrator for a new invitation.')
    return doc


def mask_email(email):
    user, _, domain = email.partition('@')
    return (user[:2] + '•' * max(1, len(user) - 2)) + '@' + domain


def check_email(doc, email):
    if not hmac.compare_digest(clean_email(email), doc.email):
        frappe.throw('Use the same email address that received this invitation')


def throttle(key, seconds, max_count):
    now = int(time.time())
    # Atomic increments prevent concurrent requests from bypassing the limit.
    bucket = frappe.cache.make_key(f'il_admin_invite_rl_v2:{key}:{now // seconds}')
    with frappe.cache.pipeline(transaction=True) as pipe:
        count, _ = pipe.incr(bucket).expire(bucket, seconds).execute()
    if count > max_count:
        frappe.throw('Too many attempts. Wait a few minutes and try again.')


def require_invitee_session():
    if frappe.session.user != 'Guest':
        frappe.throw('Sign out of your current account before accepting an admin invitation.', frappe.PermissionError)


def code_digest(doc, phone, code):
    key = str(frappe.conf.get('encryption_key') or '')
    return hmac.new(key.encode(), f'{doc.token_hash}:{phone}:{code}'.encode(), hashlib.sha256).hexdigest()


def code_key(doc):
    return 'il_admin_invite_code:' + doc.token_hash


@frappe.whitelist(allow_guest=True, methods=['GET'])
def details(token):
    require_invitee_session()
    throttle('details:' + str(frappe.local.request_ip), 300, 60)
    doc = pending(token)
    return {'full_name': doc.full_name, 'email_hint': mask_email(doc.email), 'access_level': doc.access_level,
            'expires_at': str(doc.expires_at),
            'seconds_left': max(0, int((get_datetime(doc.expires_at) - now_datetime()).total_seconds()))}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def send_code(token, email, phone):
    require_invitee_session()
    throttle('send-ip:' + str(frappe.local.request_ip), 600, 10)
    doc = pending(token, lock=True)
    check_email(doc, email)
    phone = normalize_phone(phone)
    if not frappe.conf.get('encryption_key'):
        frappe.throw('Secure verification is not configured on this site')
    key = code_key(doc)
    last = frappe.cache.get_value(key + ':last')
    if last and time.time() - last < 60:
        frappe.throw('Wait one minute before requesting another code')
    throttle('send-invite:' + doc.name, 3600, 5)
    # Record the cooldown before the external send, including failed sends.
    frappe.cache.set_value(key + ':last', time.time(), expires_in_sec=60)
    code = f'{secrets.randbelow(1000000):06d}'
    from .providers import sms
    sms(phone, verification_sms(code, purpose='Admin verification'))
    frappe.cache.set_value(key, {'phone': phone, 'digest': code_digest(doc, phone, code), 'created': time.time(),
                                 'attempts': 0}, expires_in_sec=CODE_SECONDS)
    return {'sent': True, 'phone_hint': phone[:3] + '•' * (len(phone) - 6) + phone[-3:], 'expires_in_seconds': CODE_SECONDS}


def normalize_phone(phone):
    phone = re.sub(r'[\s\-()]', '', str(phone or ''))
    if re.fullmatch(r'0[0-9]{9}', phone):  # Sri Lankan local format 07XXXXXXXX
        phone = '+94' + phone[1:]
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', phone):
        frappe.throw('Enter a valid mobile number, for example 0771234567 or +94771234567')
    return phone


def check_password(password, confirm, doc):
    password = str(password or '')
    if password != str(confirm or ''):
        frappe.throw('The two passwords do not match')
    if len(password) < 12 or len(password) > 128:
        frappe.throw('Use a password with at least 12 characters')
    from frappe.core.doctype.user.user import test_password_strength
    result = test_password_strength(password, user_data=(doc.full_name, '', '', doc.email, None)) or {}
    feedback = result.get('feedback') or {}
    if feedback and not feedback.get('password_policy_validation_passed'):
        hint = (feedback.get('warning') or '') + ' ' + ' '.join(feedback.get('suggestions') or [])
        frappe.throw(('This password is too weak. ' + hint).strip())


def check_code(doc, phone, code):
    """Validate against the current SMS challenge; failed guesses share one limit."""
    key = code_key(doc)
    saved = frappe.cache.get_value(key)
    if not re.fullmatch(r'[0-9]{6}', str(code or '')):
        frappe.throw('Enter the 6-digit code sent to your mobile')
    if not saved or time.time() - saved['created'] >= CODE_SECONDS or saved['attempts'] >= 5:
        frappe.throw('The code expired. Request a new code.')
    if saved['phone'] != phone:
        frappe.throw('Use the same mobile number the code was sent to')
    if not hmac.compare_digest(saved['digest'], code_digest(doc, phone, str(code))):
        saved['attempts'] += 1
        frappe.cache.set_value(key, saved, expires_in_sec=max(1, CODE_SECONDS - int(time.time() - saved['created'])))
        frappe.throw('The code did not match')


@frappe.whitelist(allow_guest=True, methods=['POST'])
def verify_code(token, email, phone, code):
    require_invitee_session()
    throttle('verify-ip:' + str(frappe.local.request_ip), 600, 20)
    doc = pending(token, lock=True)
    check_email(doc, email)
    phone = normalize_phone(phone)
    check_code(doc, phone, code)
    # No account or access is created here. accept revalidates the same challenge.
    return {'verified': True, 'phone_hint': phone[:3] + '•' * (len(phone) - 6) + phone[-3:]}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def accept(token, email, phone, code, password, confirm):
    require_invitee_session()
    throttle('accept-ip:' + str(frappe.local.request_ip), 600, 20)
    doc = pending(token, lock=True)
    check_email(doc, email)
    phone = normalize_phone(phone)
    check_password(password, confirm, doc)

    key = code_key(doc)
    check_code(doc, phone, code)

    # Re-check: access state may have changed after the invitation was sent.
    if frappe.db.exists('IL Owner Access', {'user': doc.email, 'enabled': 1}):
        frappe.throw('This account already has admin access. Sign in normally; this invitation cannot change its password or permissions.')
    if frappe.db.exists('IL Member', {'user': doc.email}) or frappe.db.exists('IL Public Profile', {'user': doc.email}):
        frappe.throw('This email is now used by a student, teacher or institute account. Ask for a new invitation with a dedicated email.')

    from frappe.utils.password import update_password
    if frappe.db.exists('User', doc.email):
        user = frappe.get_doc('User', doc.email)
        if not user.enabled:
            frappe.throw('This user account is disabled. Ask the site operator to review it first')
    else:
        first, _, last = doc.full_name.partition(' ')
        user = frappe.get_doc({'doctype': 'User', 'email': doc.email, 'first_name': first or doc.full_name,
                               'last_name': last, 'enabled': 1, 'user_type': 'Website User',
                               'send_welcome_email': 0})
        user.flags.no_welcome_mail = True
        user.insert(ignore_permissions=True)
    update_password(doc.email, str(password), logout_all_sessions=True)

    name = frappe.db.get_value('IL Owner Access', {'user': doc.email}, 'name')
    access = frappe.get_doc('IL Owner Access', name) if name else frappe.get_doc({'doctype': 'IL Owner Access', 'user': doc.email})
    access.update({'enabled': 1, 'full_name': doc.full_name, 'access_level': doc.access_level, 'phone': phone,
                   'accepted_at': now_datetime(), 'granted_by': doc.invited_by,
                   'reason': f'Accepted admin invitation from {doc.invited_by}'})
    access.flags.owner_access_service = True
    access.save(ignore_permissions=True)

    doc.status = 'Accepted'
    doc.accepted_at = now_datetime()
    doc.flags.admin_invite_service = True
    doc.save(ignore_permissions=True)
    frappe.cache.delete_value(key)

    # Invitee signs in themselves on the platform login page with the new password.
    from .wallet import insert
    insert('IL Payout Audit', action='Admin invitation accepted', reference=doc.email,
           actor=doc.email, details=f'{doc.access_level} · {doc.full_name}')
    send_welcome(doc)
    return {'status': 'Your admin account is ready', 'full_name': doc.full_name, 'email': doc.email,
            'access_level': doc.access_level, 'redirect': '/login?redirect-to=/campus'}


def send_welcome(doc):
    role = 'Administrator (full authority)' if doc.access_level == 'Administrator' else 'Admin'
    link = base_url() + '/login?redirect-to=/campus'
    try:
        sendmail(frappe,
            recipients=[doc.email], subject=f'Welcome to SISU LMS, {doc.full_name}', now=True,
            message=(f'<p>Welcome {escape(doc.full_name)},</p>'
                     f'<p>Your SISU LMS admin account is ready. You can now monitor and manage the platform as '
                     f'<strong>{escape(role)}</strong>.</p>'
                     f'<p><a href="{escape(link, quote=True)}">Sign in to SISU LMS</a></p>'
                     f'<p>Sign in with {escape(doc.email)} and the password you just created.</p>'))
    except Exception:
        # The account is already active; a failed welcome email must not undo it.
        frappe.log_error(title='SISU admin welcome email failed')
