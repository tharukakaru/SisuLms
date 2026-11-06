"""Deploy explicit personal-workspace registration and bind the isolated test fixture."""
import hashlib
import json
import os
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path

APP = Path('/home/sisu/frappe-bench/apps/institute_lms')
FILES = {'institute_lms/profiles.py', 'institute_lms/campus_join.py', 'institute_lms/independent_teacher.py'}
EMAIL = 'sisu.student.test+teacher@gmail.com'


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    with tarfile.open('/tmp/sisu-independent-registration.tgz') as archive:
        manifest = json.load(archive.extractfile('manifest.json'))
        if set(manifest) != FILES or len(archive.getmembers()) != len(FILES) + 1:
            raise RuntimeError('Unexpected payload')
        payload = {}
        for name in FILES:
            item = archive.getmember(name)
            if not item.isfile():
                raise RuntimeError('Invalid archive member')
            data = archive.extractfile(item).read()
            target = APP / name
            if target.is_symlink() or digest(data) != manifest[name]['after']:
                raise RuntimeError('Invalid payload: ' + name)
            before = digest(target.read_bytes()) if target.exists() else None
            if before not in (manifest[name]['before'], manifest[name]['after']):
                raise RuntimeError('Source conflict: ' + name)
            compile(data, name, 'exec')
            payload[name] = data
    import frappe
    os.chdir('/home/sisu/frappe-bench/sites')
    frappe.init(site='sisuacademylk.com', sites_path='/home/sisu/frappe-bench/sites')
    frappe.connect()
    backup = None
    written = []
    try:
        if not frappe.conf.get('il_shared_campus_enabled') or not frappe.conf.get('il_payments_paused'):
            raise RuntimeError('Expected shared public campus with gateway paused')
        inst = frappe.db.get_value('IL Institute', {'code': 'SISUTESTTC'}, ['name', 'title'], as_dict=True)
        profile = frappe.db.get_value('IL Public Profile', {'user': EMAIL}, ['name', 'kind', 'status', 'workspace'], as_dict=True)
        if not inst or inst.title != '[TEST] Independent teacher workspace' or not profile or profile.kind != 'Teacher' or profile.status != 'Verified':
            raise RuntimeError('Expected approved test teacher fixture')
        if profile.workspace and profile.workspace != inst.name:
            raise RuntimeError('Existing workspace conflict')
        if frappe.db.exists('IL Public Profile', {'kind': 'Institute', 'workspace': inst.name}):
            raise RuntimeError('Workspace belongs to an institute')
        staff = frappe.get_all('IL Member', filters={'institute': inst.name, 'active': 1, 'role': ['in', ['Teacher', 'Admin']]}, fields=['user', 'role'])
        if len(staff) != 1 or staff[0].user != EMAIL or staff[0].role != 'Teacher':
            raise RuntimeError('Test workspace staff conflict')
        rooms = frappe.get_all('IL Classroom', filters={'institute': inst.name}, fields=['owner_user', 'owner_type', 'public_provider'])
        if not rooms or any(r.owner_user != EMAIL or r.owner_type != 'Teacher' or r.public_provider != profile.name for r in rooms):
            raise RuntimeError('Test workspace classroom conflict')
        root = Path.home() / '.sisu-secrets'
        if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
            raise RuntimeError('Private backup directory required')
        backup = root / ('independent-registration-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.mkdir(mode=0o700)
        (backup / 'binding.json').write_text(json.dumps({'profile': profile.name, 'workspace': profile.workspace}))
        for name, data in payload.items():
            target = APP / name
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.copy2(target, saved)
            written.append(name)
            target.write_bytes(data)
            target.chmod(0o644)
        # This is an operator-only binding, never a client-supplied workspace.
        frappe.db.set_value('IL Public Profile', profile.name, 'workspace', inst.name)
        frappe.db.commit()
        print('DEPLOYED: independent teacher registration and personal student membership.')
        print('BOUND: isolated public test teacher workspace. No passwords, contact verification, paid access or payment settings changed. No messages sent.')
        print('Restart web AND workers, then refresh Teachers & institutes.')
    except Exception:
        frappe.db.rollback()
        for name in written:
            saved, target = backup / name, APP / name
            if saved.exists():
                shutil.copy2(saved, target)
            else:
                target.unlink(missing_ok=True)
        raise
    finally:
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: ' + (str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__))
        raise SystemExit(1) from None
