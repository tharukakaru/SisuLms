"""Create clearly labelled test teacher and free classroom only in existing staging."""
import getpass
import hashlib
import warnings
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
SITE = 'staging.sisuacademylk.com'
TITLE = '[TEST] Mathematics practice classroom'
stage = 'preflight'


class SetupBlocked(Exception):
    """Safe operator-facing messages authored by this script only."""
    pass


def main():
    global stage
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise SetupBlocked('Run as sisu')
    os.umask(0o077)
    logging.disable(logging.CRITICAL)
    warnings.simplefilter('error', getpass.GetPassWarning)
    import frappe
    from frappe.utils import validate_email_address
    os.chdir(BENCH / 'sites')
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    frappe.set_user('Administrator')
    try:
        institutes = frappe.get_all('IL Institute', fields=['name', 'code'])
        if len(institutes) != 1 or institutes[0].code != 'SISU' or frappe.conf.get('il_control_plane'):
            raise SetupBlocked('Expected isolated staging institute')
        inst = institutes[0].name
        admins = frappe.get_all('IL Member', filters={'institute': inst, 'role': 'Admin', 'active': 1}, fields=['user'])
        admins = [a for a in admins if frappe.db.get_value('User', a.user, 'enabled')]
        if len(admins) != 1:
            raise SetupBlocked('Exactly one enabled staging admin required')
        email = getpass.getpass('NEW email you control for the TEST teacher (hidden): ').strip().lower()
        validate_email_address(email, throw=True)
        if not email:
            raise SetupBlocked('Email required')
        member_name = frappe.db.get_value('IL Member', {'user': email, 'institute': inst, 'full_name': '[TEST] SISU Teacher', 'role': 'Teacher'}, 'name')
        if frappe.db.exists('User', email) and not member_name:
            roles = frappe.get_all('IL Member', filters={'user': email, 'institute': inst}, pluck='role')
            labels = ', '.join(sorted({r for r in roles if r in ('Student', 'Teacher', 'Admin')})) or 'existing user'
            raise SetupBlocked('This email is already registered on staging (' + labels + '). Use a different email you control for the test teacher; the existing account will not be changed.')
        password = None
        if not member_name:
            stage = 'hidden test-teacher password'
            password = getpass.getpass('Choose test-teacher password (hidden, at least 12 characters): ')
            confirm = getpass.getpass('Confirm test-teacher password (hidden): ')
            if password != confirm or len(password) < 12:
                raise SetupBlocked('Passwords must match and contain at least 12 characters.')
            del confirm
        root = Path.home() / '.sisu-secrets'
        if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
            raise SetupBlocked('Private backup directory required')
        backup = root / ('test-classroom-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.mkdir(mode=0o700)
        stage = 'staging database backup'
        subprocess.run(['/usr/local/bin/bench', '--site', SITE, 'backup', '--backup-path', str(backup)], cwd=BENCH, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        stage = 'create test User with password'
        if not member_name:
            user = frappe.get_doc({'doctype': 'User', 'email': email, 'first_name': '[TEST] SISU', 'last_name': 'Teacher', 'enabled': 1, 'user_type': 'Website User', 'send_welcome_email': 0, 'new_password': password})
            user.insert(ignore_permissions=True)
            user.append_roles('Institute Teacher')
            user.save(ignore_permissions=True)
            stage = 'create test teacher membership and subscription'
            member = frappe.get_doc({'doctype': 'IL Member', 'institute': inst, 'user': email, 'role': 'Teacher', 'full_name': '[TEST] SISU Teacher', 'language': 'en', 'active': 1}).insert(ignore_permissions=True)
            member_name = member.name
        stage = 'approve test teacher relationship'
        for profile in frappe.get_all('IL Public Profile', filters={'workspace': inst, 'kind': 'Institute'}, pluck='name'):
            existing = frappe.db.get_value('IL Profile Relationship', {'profile': profile, 'user': email, 'kind': 'Teacher membership'}, 'name')
            if existing:
                if frappe.db.get_value('IL Profile Relationship', existing, 'status') != 'Active':
                    raise SetupBlocked('Existing test membership needs manual review')
            else:
                key = hashlib.sha256(f'{email}:{profile}:Teacher membership'.encode()).hexdigest()
                link = frappe.get_doc({'doctype': 'IL Profile Relationship', 'relationship_key': key, 'profile': profile, 'user': email, 'kind': 'Teacher membership', 'status': 'Active', 'reviewed_by': admins[0].user, 'reason': 'Operator-authorized staging test fixture; not a real teacher endorsement.'})
                link.flags.community_service = True
                link.insert(ignore_permissions=True)
        stage = 'free internal test classroom through normal API'
        frappe.set_user(admins[0].user)
        from institute_lms.api import create_internal_classroom
        room = frappe.db.get_value('IL Classroom', {'institute': inst, 'title': TITLE}, 'name')
        if room:
            if frappe.db.get_value('IL Classroom', room, 'teacher') != member_name:
                raise SetupBlocked('Existing test classroom has another teacher')
        else:
            room = create_internal_classroom({'title': TITLE, 'teacher': member_name,
                'subject': 'Mathematics', 'description': 'TEST DATA — practice creating lessons, materials and quizzes here. Not a real advertised class.',
                'fee_mode': 'Free', 'fee': 0, 'billing_type': 'One-time', 'access_duration_days': 30,
                'grade': 'Grade 6', 'font': 'sans', 'class_kind': 'General', 'published': 0})
        frappe.db.commit()
        print('CREATED/CONFIRMED: [TEST] SISU Teacher and one free, unpublished classroom in SISU Staging.')
        print('Test institute: https://staging.sisuacademylk.com/campus')
        print('Sign in with EMAIL AND PASSWORD using the email and password entered here. Existing test passwords are not reset.')
        print('No additional institute database, verified-contact claims, invitations or customer messages created.')
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if isinstance(exc, SetupBlocked):
            print('BLOCKED: ' + str(exc))
        print('STOPPED at ' + stage + ' [' + type(exc).__name__ + ']. Uncommitted test records rolled back; no secrets printed.')
        raise SystemExit(1) from None
