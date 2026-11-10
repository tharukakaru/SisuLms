"""Apply presentation-only data to four named demo logins and three named test classes."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

PEOPLE = {
    'sisu.student.test@gmail.com': ('Navodya', 'Galagoda', 'navodya.jpg', 'Student'),
    'sisu.student.test+teacher@gmail.com': ('Kasun', 'Madushan', 'kasun.jpg', 'Teacher'),
    'sisu.student.test+institute.teacher@gmail.com': ('Dilini', 'Fernando', 'dilini.jpg', 'Teacher'),
    'sisu.student.test+institute.admin@gmail.com': ('Ravindu', 'Senanayake', 'institute-admin.jpg', 'Admin'),
}
CLASS_STYLES = [
    ('SISUTESTTC', 'sisu.student.test+teacher@gmail.com', '[TEST] Free classroom practice', 'Biology · Learning practice', 'biology.png'),
    ('SISUTESTTC', 'sisu.student.test+teacher@gmail.com', '[TEST] Bank approval practice - DO NOT PAY', 'Economics · Payment practice', 'economics.png'),
    ('SISUDEMO', 'sisu.student.test+institute.teacher@gmail.com', '[TEST] Institute teacher assigned practice', 'Physics · Institute practice', 'physics.png'),
]
ALLOWED = {'User': {'first_name', 'last_name', 'full_name', 'user_image'},
           'IL Public Profile': {'display_name', 'profile_image'},
           'IL Member': {'full_name'}, 'IL Classroom': {'title', 'cover_image', 'profile_image'}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Commit the named demo presentation updates')
    args = parser.parse_args()
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com'); frappe.connect()
    try:
        if not frappe.conf.get('il_shared_campus_enabled'):
            raise RuntimeError('Expected shared campus')
        changes = []
        def add(doctype, name, values):
            if not set(values) <= ALLOWED[doctype]:
                raise RuntimeError('Unexpected field')
            old = frappe.db.get_value(doctype, name, list(values), as_dict=True)
            if not old:
                raise RuntimeError('Missing named fixture')
            if any(old.get(k) != v for k, v in values.items()):
                changes.append(dict(doctype=doctype, name=name, before=dict(old), after=values))
        for email, (first, last, asset, role) in PEOPLE.items():
            user = frappe.db.get_value('User', email, ['name', 'enabled', 'user_type'], as_dict=True)
            if not user or not user.enabled or user.user_type != 'Website User':
                raise RuntimeError('Expected enabled demo Website User: ' + email)
            path = Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms/public/demo') / asset
            if not path.is_file() or path.stat().st_size < 100:
                raise RuntimeError('Deploy demo assets before applying data')
            label = first + ' ' + last
            url = '/assets/institute_lms/demo/' + asset
            add('User', email, dict(first_name=first, last_name=last, full_name=label, user_image=url))
            for member in frappe.get_all('IL Member', filters={'user': email}, fields=['name', 'role', 'institute']):
                code = frappe.db.get_value('IL Institute', member.institute, 'code')
                if code in ('SISUDEMO', 'SISUTESTTC') and member.role == role:
                    add('IL Member', member.name, dict(full_name=label))
            if role != 'Admin':
                profile = frappe.db.get_value('IL Public Profile', {'user': email}, ['name', 'kind'], as_dict=True)
                if profile:
                    if profile.kind != role:
                        raise RuntimeError('Demo profile kind conflict')
                    add('IL Public Profile', profile.name, dict(display_name=label, profile_image=url))
        for code, email, old_title, title, asset in CLASS_STYLES:
            inst = frappe.db.get_value('IL Institute', {'code': code}, 'name')
            teacher = frappe.db.get_value('IL Member', {'institute': inst, 'user': email, 'role': 'Teacher'}, 'name')
            if not inst or not teacher:
                raise RuntimeError('Missing test teaching workspace')
            rows = frappe.get_all('IL Classroom', filters={'institute': inst, 'teacher': teacher, 'title': ['in', [old_title, title]]}, fields=['name', 'owner_user', 'owner_type'])
            if len(rows) != 1:
                raise RuntimeError('Named classroom missing or ambiguous: ' + old_title)
            room = rows[0]
            if code == 'SISUTESTTC' and room.owner_user != email:
                raise RuntimeError('Test classroom owner conflict')
            if code == 'SISUDEMO' and (room.name != 'fp20kd7lgd' or room.owner_type != 'Institute'):
                raise RuntimeError('Named institute assignment conflict')
            add('IL Classroom', room.name, dict(title=title, cover_image='/assets/institute_lms/demo/' + asset,
                                               profile_image='/assets/institute_lms/demo/' + PEOPLE[email][2]))
        for change in changes:
            print(json.dumps({k: change[k] for k in ('doctype', 'name', 'after')}, ensure_ascii=False))
        if not args.apply:
            print('PREVIEW ONLY: rerun with --apply for these presentation changes. No records changed.'); return
        root = Path.home() / '.sisu-secrets'
        if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
            raise RuntimeError('Private backup directory required')
        backup = root / ('demo-presentation-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        with backup.open('x', encoding='utf-8') as stream:
            os.chmod(backup, 0o600); json.dump(changes, stream, ensure_ascii=False, indent=2, default=str)
        # Exact allowlisted columns only; bypass document hooks to avoid notifications,
        # account provisioning, verification changes or classroom schedule side effects.
        for change in changes:
            frappe.db.set_value(change['doctype'], change['name'], change['after'], update_modified=False)
        for change in changes:
            actual = frappe.db.get_value(change['doctype'], change['name'], list(change['after']), as_dict=True)
            if dict(actual) != change['after']:
                raise RuntimeError('Presentation verification failed')
        frappe.db.commit()
        for email in PEOPLE:
            frappe.clear_cache(user=email)
        print('APPLIED: named demo names/photos and three classroom cards. Private backup: ' + str(backup))
        print('No credentials, roles, verification, membership access, enrolments, fees, invoices, payment settings or messages changed.')
    finally:
        frappe.db.rollback(); frappe.destroy()

if __name__ == '__main__':
    main()
