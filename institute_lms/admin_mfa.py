"""Opt-in platform SMS MFA, using Frappe's password/OTP login flow.

Enable only with il_admin_sms_mfa_enabled on the control-plane site. No OTP or
provider credentials are returned to the browser. Existing sessions are retained.
"""
from .message_templates import verification_sms
import hashlib
import hmac
import re

import frappe
import pyotp

ROLE = 'SISU Admin SMS MFA'
TTL = 300


def enabled():
    return bool(frappe.conf.get('il_control_plane') and frappe.conf.get('il_admin_sms_mfa_enabled'))


def required(user):
    if not enabled() or not user or user == 'Guest':
        return False
    from .owner_access import access_level
    # Full Administrators and the primary owner use password authentication.
    # Only delegated Admin access requires the SMS second factor.
    return user != 'Administrator' and access_level(user) == 'Admin'


def raw_key(value):
    return frappe.cache.make_key('il_admin_mfa:' + value)


def proof_key(user, secret, otp):
    digest = hmac.new(str(secret).encode(), (user + ':' + str(otp)).encode(), hashlib.sha256).hexdigest()
    return raw_key('proof:' + digest)


def fail(message='Sign in again with your password and a new SMS code.'):
    frappe.throw(message, frappe.AuthenticationError)


def send_token(otpsecret, token=None, phone_no=None):
    """Frappe calls this only after successful password authentication."""
    if not enabled():
        return framework_sms(otpsecret, token, phone_no)
    # LoginManager is still inside its constructor on /api/method/login, so
    # frappe.local.login_manager is not assigned yet. Use the trusted hook object.
    manager = frappe.flags.get('il_admin_mfa_login_manager')
    user = getattr(manager, 'user', None)
    if not required(user):
        fail('SMS admin verification is not available for this account.')
    if not re.fullmatch(r'\+?947\d{8}', str(phone_no or '')):
        fail('An administrator must register your mobile number before you can sign in.')
    def cooldown():
        frappe.local.response['mfa_retry_after_seconds'] = max(1, frappe.cache.ttl(raw_key('send:' + user)))
        raise frappe.AuthenticationError('Please wait one minute before requesting another sign-in code.')
    if frappe.cache.get(raw_key('send:' + user)):
        cooldown()
    from .admin_invites import throttle
    throttle('mfa-send-user:' + user, 3600, 5)
    throttle('mfa-send-ip:' + str(frappe.local.request_ip), 3600, 15)
    # Keep the cooldown even after an uncertain provider response: do not double-send.
    if not frappe.cache.set(raw_key('send:' + user), '1', nx=True, ex=60):
        # An expected cooldown is an inline login state, not a message dialog.
        cooldown()
    otp = pyotp.HOTP(otpsecret).at(int(token))
    from .notify_platform import send
    result = send(phone_no, verification_sms(otp, purpose='Admin sign-in', minutes=5))
    if not result or not result.get('accepted'):
        fail('SMS delivery could not be confirmed. Please wait before trying again.')
    frappe.cache.set(proof_key(user, otpsecret, otp), user, ex=TTL)
    return True


def framework_sms(secret, token, phone):
    """Preserve the framework's SMS behavior on sites without the SISU opt-in."""
    if not phone:
        return False
    settings = frappe.get_doc('SMS Settings', 'SMS Settings')
    if not settings.sms_gateway_url:
        return False
    from frappe.twofactor import get_rendered_otp_message
    from frappe.core.doctype.sms_settings.sms_settings import send_request
    args = {settings.message_parameter: get_rendered_otp_message(pyotp.HOTP(secret).at(int(token)))}
    for parameter in settings.get('parameters'):
        args[parameter.parameter] = parameter.value
    args[settings.receiver_parameter] = phone
    frappe.enqueue(method=send_request, queue='short', timeout=300, is_async=True,
                   params=args, gateway_url=settings.sms_gateway_url, use_post=settings.use_post)
    return True


def before_login(login_manager=None):
    """Limit guesses and reject expired/consumed challenges before native OTP work."""
    if not enabled():
        return
    frappe.flags.il_admin_mfa_login_manager = login_manager
    tmp = str(frappe.form_dict.get('tmp_id') or '')
    if not tmp:
        return
    user = frappe.safe_decode(frappe.cache.get(tmp + '_usr'))
    if not required(user):
        # Missing credentials must never fall back to a different login path.
        if not user:
            fail()
        return
    secret = frappe.safe_decode(frappe.cache.get(tmp + '_otp_secret'))
    counter = frappe.safe_decode(frappe.cache.get(tmp + '_token'))
    with frappe.cache.pipeline(transaction=True) as pipe:
        attempts, _ = pipe.incr(raw_key('attempt:' + tmp)).expire(raw_key('attempt:' + tmp), TTL).execute()
    if attempts > 5 or not secret or counter is None:
        clear_challenge(tmp)
        fail('Your sign-in code expired or has too many attempts. Sign in again.')
    otp = str(frappe.form_dict.get('otp') or '')
    expected = pyotp.HOTP(secret).at(int(counter))
    key = proof_key(user, secret, expected)
    if not frappe.cache.get(key):
        clear_challenge(tmp)
        fail()
    if not re.fullmatch(r'\d{6}', otp) or not hmac.compare_digest(expected, otp):
        if attempts >= 5:
            frappe.cache.delete(key)
            clear_challenge(tmp)
        fail('The SMS code did not match. Check the six digits and try again.')
    # Request-local state, never accepted from request parameters or cookies.
    frappe.flags.il_admin_mfa_proof = (key, user, tmp)


def clear_challenge(tmp):
    frappe.cache.delete(*(tmp + suffix for suffix in ('_usr', '_pwd', '_otp_secret', '_token')))


def validate_login(login_manager=None):
    """Delegated Admin sessions need a delivered, one-use SMS proof.

    This also blocks password-only OAuth/email-link/login_as paths for admins.
    Native Frappe has already verified the password and OTP before this hook.
    """
    if not required(login_manager.user):
        return
    proof = frappe.flags.get('il_admin_mfa_proof')
    if not proof or proof[1] != login_manager.user:
        fail('Admin sign-in requires your password and SMS verification. Use the platform sign-in page.')
    key, user, tmp = proof
    # Atomic consumption prevents concurrent requests from replaying a valid code.
    consumed = frappe.cache.eval("local v=redis.call('GET',KEYS[1]); redis.call('DEL',KEYS[1]); return v", 1, key)
    if frappe.safe_decode(consumed) != user:
        fail()
    clear_challenge(tmp)
    frappe.flags.il_admin_mfa_verified = True


def sync_access(doc, method=None):
    """New invitation recipients inherit MFA and their verified mobile number."""
    if not enabled() or not doc.enabled:
        return
    enroll(doc.user, doc.phone if doc.get('accepted_at') else None)


def enroll(user, phone=None):
    """Synchronize the dedicated MFA role with server-authoritative access."""
    needs_sms = required(user)
    if needs_sms and not frappe.db.exists('Role', ROLE):
        frappe.get_doc({'doctype': 'Role', 'role_name': ROLE, 'desk_access': 0,
                        'two_factor_auth': 1}).insert(ignore_permissions=True)
    doc = frappe.get_doc('User', user)
    if phone:
        # Frappe also reads phone for SMS. mobile_no is a unique login identifier;
        # the local QA admins intentionally share one verification handset.
        doc.phone = phone
    if needs_sms and ROLE not in [r.role for r in doc.roles]:
        doc.append('roles', {'role': ROLE})
    elif not needs_sms:
        doc.set('roles', [r for r in doc.roles if r.role != ROLE])
    doc.save(ignore_permissions=True)
    frappe.clear_cache(user=user)


def sync_all():
    """Deployment migration; never change other sites or other MFA roles."""
    if not enabled():
        return
    users = set(frappe.get_all('IL Owner Access', pluck='user'))
    users.update(frappe.get_all('Has Role', filters={'role': ROLE, 'parenttype': 'User'}, pluck='parent'))
    for user in sorted(users):
        if frappe.db.exists('User', user):
            enroll(user)
