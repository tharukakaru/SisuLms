"""Operator-only provisioning of the three explicitly authorized login accounts.

No passwords, verification claims, subscription changes or messages are generated.
"""
import argparse
import logging
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
TEEN = 'teen.sisuacademylk.com'
PLATFORM = 'platform.sisuacademylk.com'
OWNER_EMAILS = ('danu@absolx.com', 'tharukakarunarathne60@gmail.com')
ADMIN = 'gro4celk@gmail.com'
stage = 'startup'


def connect(frappe, site):
    frappe.init(site=site, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    frappe.set_user('Administrator')


def preflight(frappe, site):
    provider = frappe.get_doc('Social Login Key', 'google')
    if not provider.enable_social_login or provider.sign_ups != 'Deny':
        raise ValueError('Expected existing-account-only Google configuration')
    emails = (ADMIN,) if site == TEEN else OWNER_EMAILS
    if site == TEEN:
        institutes = frappe.get_all('IL Institute', fields=['name', 'code'])
        if len(institutes) != 1 or institutes[0].name != 'igtvc0ntd3' or institutes[0].code != 'TEEN':
            raise ValueError('Unexpected institute')
        if frappe.conf.get('il_control_plane') or not frappe.db.exists('Role', 'Institute Admin'):
            raise ValueError('Unexpected institute configuration')
    else:
        from institute_lms.owner_access import is_owner
        if not frappe.conf.get('il_control_plane') or not frappe.conf.get('il_owner_provisioned'):
            raise ValueError('Platform owner configuration missing')
        if not is_owner(frappe.conf.get('il_owner_email')):
            raise ValueError('Existing primary owner must remain active')
    for email in emails:
        if frappe.db.exists('User', email) and not frappe.db.get_value('User', email, 'enabled'):
            raise ValueError('Existing requested account disabled; review required')
        members = frappe.get_all('IL Member', filters={'user': email}, fields=['institute', 'role', 'active'])
        if site == PLATFORM and (members or frappe.db.exists('IL Public Profile', {'user': email})):
            raise ValueError('Requested owner has a provider/member profile')
        if site == TEEN:
            if any(m.institute != 'igtvc0ntd3' or m.role != 'Admin' or not m.active for m in members):
                raise ValueError('Existing membership conflicts with requested admin access')
            if frappe.db.exists('IL Owner Access', {'user': email}):
                raise ValueError('Institute admin already has owner access')
        else:
            name = frappe.db.get_value('IL Owner Access', {'user': email}, 'name')
            if name and not frappe.db.get_value('IL Owner Access', name, 'enabled'):
                raise ValueError('Previously revoked owner access requires review')


def provision(frappe, site):
    for email in ((ADMIN,) if site == TEEN else OWNER_EMAILS):
        if not frappe.db.exists('User', email):
            values = {'doctype': 'User', 'email': email, 'enabled': 1,
                      'first_name': 'Bradley' if site == TEEN else email.split('@')[0],
                      'user_type': 'Website User', 'send_welcome_email': 0}
            if site == TEEN:
                values['last_name'] = 'Emerson'
            frappe.get_doc(values).insert(ignore_permissions=True)
        if site == TEEN:
            user = frappe.get_doc('User', email)
            user.append_roles('Institute Admin')
            user.save(ignore_permissions=True)
            if not frappe.db.exists('IL Member', {'institute': 'igtvc0ntd3', 'user': email}):
                frappe.get_doc({'doctype': 'IL Member', 'institute': 'igtvc0ntd3',
                                'user': email, 'full_name': 'Bradley Emerson', 'role': 'Admin',
                                'active': 1, 'language': 'en', 'phone': '+94765849861'}).insert(ignore_permissions=True)
        elif email != str(frappe.conf.get('il_owner_email') or '').lower():
            if not frappe.db.exists('IL Owner Access', {'user': email}):
                doc = frappe.get_doc({'doctype': 'IL Owner Access', 'user': email, 'enabled': 1,
                                      'granted_by': 'Administrator',
                                      'reason': 'Explicit operator-authorized SISU launch account provisioning'})
                doc.flags.owner_access_service = True
                doc.insert(ignore_permissions=True)
            from institute_lms.owner_access import is_owner
            if not is_owner(email):
                raise ValueError('Owner authorization verification failed')
    frappe.db.commit()
    frappe.clear_cache()


def main():
    global stage
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise ValueError('Run as sisu on the authorized server')
    os.umask(0o077)
    logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH / 'sites')
    for site in (TEEN, PLATFORM):
        try:
            stage = site + ' preflight'
            connect(frappe, site)
            preflight(frappe, site)
            print('PASS: ' + site + ' account preflight.')
        finally:
            frappe.destroy()
    if not args.apply:
        print('Inspection only. Use --apply to create the authorized accounts.')
        return
    stage = 'private backups'
    root = Path.home() / '.sisu-secrets'
    folder = root / 'login-account-backups'
    for path in (root, folder):
        path.mkdir(mode=0o700, exist_ok=True)
        info = path.lstat()
        if path.is_symlink() or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError('Unsafe backup directory')
    backup = folder / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(mode=0o700)
    for site in (TEEN, PLATFORM):
        target = backup / site
        target.mkdir(mode=0o700)
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'backup', '--backup-path', str(target)],
                       cwd=BENCH, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for site in (TEEN, PLATFORM):
        try:
            stage = site + ' provision accounts'
            connect(frappe, site)
            preflight(frappe, site)
            provision(frappe, site)
            print('PROVISIONED: ' + site + ' authorized accounts; existing admins preserved.')
        finally:
            try:
                frappe.db.rollback()
            except Exception:
                pass
            frappe.destroy()
    print('No messages sent or passwords set. Phone verification unchanged. Google login still requires browser testing.')
    print('Password setup delivery and Platinum trial activation remain separate pending steps.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED at ' + stage + ' [' + type(exc).__name__ + ']. No secrets printed; targets may be partially complete.')
        raise SystemExit(1) from None
