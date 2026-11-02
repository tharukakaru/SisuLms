"""One reserved public-site SMS to a user-entered authorized test mobile."""
import getpass
import json
import logging
import os
import re
import stat
import warnings
from pathlib import Path


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o077)
    logging.disable(logging.CRITICAL)
    warnings.simplefilter('error', getpass.GetPassWarning)
    root = Path.home()/'.sisu-secrets'
    if root.is_symlink() or root.stat().st_uid != os.getuid() or stat.S_IMODE(root.stat().st_mode)&0o077:
        raise RuntimeError('Private marker directory required')
    marker = root/'public-sms-delivery-test.json'
    if marker.exists() or marker.is_symlink():
        raise RuntimeError('Public SMS test already reserved; check phone and provider log before any resend')
    phone = getpass.getpass('Your authorized SMS test mobile, 07XXXXXXXX or +947XXXXXXXX (hidden): ').strip()
    if re.fullmatch(r'07\d{8}', phone):
        phone = '+94'+phone[1:]
    if not re.fullmatch(r'\+947\d{8}', phone):
        raise RuntimeError('Use 07XXXXXXXX or +947XXXXXXXX')
    import frappe
    os.chdir('/home/sisu/frappe-bench/sites')
    try:
        frappe.init(site='sisuacademylk.com',sites_path='/home/sisu/frappe-bench/sites');frappe.connect()
        if not frappe.conf.get('maintenance_mode') or frappe.conf.get('il_public_signup_enabled'):
            raise RuntimeError('Expected public site still closed for this deployment test')
        if frappe.conf.get('il_sms_adapter') != 'institute_lms.notify_public.send':
            raise RuntimeError('Unexpected SMS adapter')
        from institute_lms.notify_public import credentials, send
        credentials('sisuacademylk.com')
        with marker.open('x') as out:
            json.dump({'state':'reserved'},out);out.flush();os.fsync(out.fileno())
        result = send(phone,'Public SISU website delivery test. This is not a login code.')
        if not result.get('accepted'):
            raise RuntimeError('SMS acceptance not confirmed')
        with marker.open('w') as out:
            json.dump({'state':'accepted'},out)
        print('PASS: Notify accepted one public-site test SMS. Confirm receipt on your phone.')
        print('No account or signup settings changed. No automatic resend.')
    finally:
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__)+'. No phone or credentials displayed.')
        raise SystemExit(1)
