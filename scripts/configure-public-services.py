"""Configure public verification services while keeping maintenance and signup closed."""
import json
import logging
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
SITE = 'sisuacademylk.com'


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    logging.disable(logging.CRITICAL)
    os.umask(0o077)
    os.chdir(BENCH/'sites')
    import frappe
    config = BENCH/'sites'/SITE/'site_config.json'
    info = config.lstat()
    if config.is_symlink() or info.st_uid != os.getuid():
        raise RuntimeError('Unexpected configuration ownership')
    original = config.read_bytes()
    settings = json.loads(original)
    if not settings.get('maintenance_mode') or settings.get('il_public_signup_enabled') or settings.get('il_control_plane'):
        raise RuntimeError('Expected closed public site')
    if settings.get('il_sms_adapter') not in (None, '', 'institute_lms.notify_public.send'):
        raise RuntimeError('Unexpected existing SMS adapter')
    if settings.get('il_whatsapp_token') or settings.get('il_whatsapp_phone_id'):
        raise RuntimeError('Unexpected WhatsApp configuration')
    try:
        frappe.init(site=SITE, sites_path=str(BENCH/'sites'));frappe.connect()
        from institute_lms.notify_public import credentials
        credentials(SITE)
        if not frappe.conf.get('encryption_key'):
            raise RuntimeError('Site encryption key missing')
        policy = frappe.get_single('IL Portal Settings')
        if policy.privacy_policy_url != 'https://www.sisuacademylk.com/privacy/' or not policy.privacy_policy_version:
            raise RuntimeError('Published policy not registered')
        account = frappe.get_doc('Email Account', 'SISU Academy')
        if not account.enable_outgoing or not account.get_password('password'):
            raise RuntimeError('Outgoing email credentials unavailable')
        google = frappe.get_doc('Social Login Key', 'google')
        if not google.enable_social_login or not google.get_password('client_secret'):
            raise RuntimeError('Google credentials unavailable')
        if google.redirect_url != 'https://www.sisuacademylk.com/api/method/frappe.integrations.oauth2_logins.login_via_google':
            raise RuntimeError('Google redirect mismatch')
        # Exercise configuration checks without saving public signup activation.
        proposed = dict(settings, host_name='https://www.sisuacademylk.com',
            il_shared_campus_enabled=1, il_public_sms_enabled=1,
            il_sms_adapter='institute_lms.notify_public.send', il_self_signup_phone_channel='SMS',
            il_public_signup_enabled=0, il_self_signup_enabled=0, il_payments_paused=1,
            maintenance_mode=1, pause_scheduler=1, mute_emails=0)
        frappe.conf.update(proposed)
        frappe.conf.il_public_signup_enabled = 1
        from institute_lms.public_signup import ready
        ready()
        frappe.conf.il_public_signup_enabled = 0
        root = Path.home()/'.sisu-secrets'
        if root.is_symlink() or root.stat().st_uid != os.getuid() or stat.S_IMODE(root.stat().st_mode)&0o077:
            raise RuntimeError('Private backup directory required')
        backup = root/('public-services-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
        with backup.open('xb') as out:
            out.write(original)
        if config.read_bytes() != original:
            raise RuntimeError('Configuration changed during preflight')
        fd, temporary = tempfile.mkstemp(dir=config.parent, prefix='.services-')
        with os.fdopen(fd, 'w') as out:
            json.dump(proposed, out, indent=2)
        os.chmod(temporary, 0o600)
        os.replace(temporary, config)
        frappe.clear_cache()
        print('CONFIGURED: public SMS adapter, email verification settings and shared-campus mode.')
        print('PASS: public signup configuration checks; no email, SMS or Google requests sent.')
        print('Maintenance ON; public signup OFF; general email queue remains suspended; scheduler paused.')
        print('Payments paused; WhatsApp unconfigured. Delivery and browser tests still required.')
    finally:
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__)+'. No credentials printed.')
        raise SystemExit(1)
