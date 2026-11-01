"""Sandbox browser self-tests. Customer outbox delivery stays disabled."""
import base64
import hashlib
import re

SITE = 'hnb-checkout.localhost'
FIELDS = ('apiKey', 'projectId', 'messagingSenderId', 'appId')


class WebConfigurationError(ValueError):
    """Fixed messages only; safe for local setup diagnostics."""


def web_settings(config, vapid):
    if not isinstance(config, dict) or set(config) - set(FIELDS):
        raise WebConfigurationError('Only the four public Firebase Web fields are accepted.')
    for field in FIELDS:
        if not isinstance(config.get(field), str) or not config[field] or len(config[field]) > 256:
            raise WebConfigurationError('Missing or invalid field: ' + field + '. Paste only its value.')
    if config['projectId'] != 'sisu-lms':
        raise WebConfigurationError('projectId must be sisu-lms, without quotes or a trailing comma.')
    if not re.fullmatch(r'\d+', config['messagingSenderId']):
        raise WebConfigurationError('messagingSenderId must contain digits only, without quotes or a trailing comma.')
    if not config['appId'].startswith('1:' + config['messagingSenderId'] + ':web:'):
        raise WebConfigurationError('appId must be the Web App ID from the same app, beginning with 1:<messagingSenderId>:web:. Paste only its value.')
    if not isinstance(vapid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{87}', vapid):
        raise WebConfigurationError('VAPID key must be the 87-character public key from Web Push certificates, without quotes, spaces or a trailing comma.')
    raw = base64.urlsafe_b64decode(vapid + '=')
    if len(raw) != 65 or raw[0] != 4:
        raise WebConfigurationError('VAPID key is not a valid uncompressed public key.')
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey, SECP256R1
    try:
        EllipticCurvePublicKey.from_encoded_point(SECP256R1(), raw)
    except ValueError:
        raise WebConfigurationError('VAPID key is not a valid P-256 public key. Copy it again from Web Push certificates.') from None
    return {'config': {k: config[k] for k in FIELDS}, 'vapidKey': vapid}


def settings():
    import frappe
    value = frappe.conf.get('il_firebase_sandbox') or {}
    if (frappe.local.site != SITE or frappe.session.user in ('Guest', None)
            or frappe.session.user != value.get('test_user') or not value.get('self_test_enabled')):
        raise PermissionError('Firebase browser testing is restricted to the configured sandbox tester.')
    return value


def browser_config():
    try:
        value = settings()
    except PermissionError:
        return {'available': False}
    return {'available': True, **web_settings(value.get('web'), value.get('vapid_key'))}


def self_test(device, request_id, dry_run=True):
    import frappe
    settings()
    if not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9-]{36}', request_id):
        raise ValueError('Invalid test request ID.')
    dry_run = dry_run in (True, 1, '1', 'true')
    row = frappe.get_doc('IL Device Token', device)
    if row.user != frappe.session.user or row.revoked or row.platform != 'web':
        raise PermissionError('Select your own active browser registration.')
    validated_key = 'firebase-validated:' + hashlib.sha256((frappe.session.user + row.token_hash).encode()).hexdigest()
    if not dry_run and not frappe.cache.get_value(validated_key):
        raise ValueError('Validate this device with Firebase before sending a test.')
    key = 'firebase-self-test:' + hashlib.sha256((frappe.session.user + request_id).encode()).hexdigest()
    with frappe.cache.lock(key, timeout=60):
        if frappe.cache.get_value(key):
            raise ValueError('This test was already attempted. Check its result before starting another.')
        from .registration import limit
        limit('firebase-self-test:' + frappe.session.user)
        # Reserve before network I/O: an uncertain response must never cause an automatic resend.
        frappe.cache.set_value(key, True, expires_in_sec=86400)
        try:
            from firebase_admin import messaging
            from .firebase_backend import get_app
            message = messaging.Message(token=row.get_password('token'),
                notification=messaging.Notification(title='SISU sandbox test', body='Your browser push notification is working.'),
                data={'test_id': request_id},
                webpush=messaging.WebpushConfig(headers={'TTL': '120'}))
            result = messaging.send(message, dry_run=dry_run, app=get_app())
        except Exception:
            # Provider exceptions can include tokens. Do not propagate or log them.
            raise ValueError('Firebase test failed or its outcome is uncertain. No automatic retry was made.') from None
        if dry_run:
            frappe.cache.set_value(validated_key, True, expires_in_sec=3600)
    return {'status': 'validated' if dry_run else 'accepted', 'test_id': request_id,
            'provider_id': result}
