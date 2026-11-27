"""Real Notify SMS for the Platform owner site (admin invitation codes).

Same Notify account and sender as the public campus (notify_public). Enabled only
on platform.sisuacademylk.com with the explicit flag il_platform_sms_enabled = 1.
Credentials stay outside the repository in ~/.sisu-secrets/notify-live/<site>/.
"""
import re
import frappe

SITE = 'platform.sisuacademylk.com'


def send(phone, message, idempotency_key=None):
    site = getattr(frappe.local, 'site', None)
    if site != SITE or frappe.conf.get('il_platform_sms_enabled') != 1 or not frappe.conf.get('il_control_plane'):
        frappe.throw('Platform SMS is not enabled on this site')
    number = str(phone).strip().lstrip('+')
    if not re.fullmatch(r'947[0-9]{8}', number):
        frappe.throw('Enter a Sri Lankan mobile number, for example 0771234567')
    from .notify_live import credentials
    try:
        config = credentials(site)
    except (ValueError, OSError, TypeError):
        frappe.throw('SMS provider configuration is unavailable on the Platform site')
    from .notify_adapter import send_config
    # Caller (admin_invites.send_code) owns throttling; never retry an uncertain send.
    return send_config(config, number, message)
