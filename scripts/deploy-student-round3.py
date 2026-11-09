"""Deploy the reviewed owner panel update; retain old assets for open tabs."""
import hashlib
import json
import os
import sys
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH / 'apps/institute_lms'
ALLOWED = {'institute_lms/institute_lms/doctype/il_paid_access/il_paid_access.json', 'frontend/src/native/AccountReceipts.vue', 'frontend/src/native/InstituteRegistration.vue', 'institute_lms/commercial.py', 'institute_lms/registration.py', 'institute_lms/demo_learning.py', 'institute_lms/learning_spaces.py', 'frontend/src/native/StudentClassrooms.vue', 'institute_lms/api.py', 'frontend/src/native/CampusSwitcher.vue', 'frontend/src/native/DemoLesson.vue', 'institute_lms/campus_join.py', 'institute_lms/class_keys.py', 'frontend/src/App.vue', 'frontend/src/native/BankPayments.vue'}


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o022)
    if not Path('/tmp/sisu-student-round3.tgz').is_file():
        raise RuntimeError('Missing release archive /tmp/sisu-student-round3.tgz. Upload it before running this installer. No changes made.')
    with tarfile.open('/tmp/sisu-student-round3.tgz') as archive:
        manifest = json.load(archive.extractfile('manifest.json'))
        if set(manifest) != ALLOWED or len(archive.getmembers()) != len(ALLOWED) + 1:
            raise RuntimeError('Unexpected UI payload')
        payload = {}
        for name in ALLOWED:
            entry = archive.getmember(name)
            if not entry.isfile():
                raise RuntimeError('Unexpected archive member')
            payload[name] = archive.extractfile(entry).read()
            path = APP / name
            if path.is_symlink() or digest(payload[name]) != manifest[name]['after']:
                raise RuntimeError('UI payload mismatch')
            actual = digest(path.read_bytes()) if path.exists() else None
            if actual not in (manifest[name]['before'], manifest[name]['after']) and not (name == 'scripts/seed-public-demo-content.py' and actual is None):
                raise RuntimeError('Source conflict: ' + name)
    root = Path.home() / '.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise RuntimeError('Private backup directory required')
    backup = root / ('student-round3-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700)
    paths = [*ALLOWED, 'institute_lms/www/campus.html', 'institute_lms/public/portal']
    absent = []
    for name in paths:
        src, dst = APP / name, backup / name
        if not src.exists():
            absent.append(name)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    print('Private recovery directory:', backup)
    with (backup / 'database-backup.log').open('w') as log:
        subprocess.run(['/usr/local/bin/bench', '--site', 'sisuacademylk.com', 'backup'], cwd=BENCH, stdout=log, stderr=log, check=True)
    try:
        for name, data in payload.items():
            (APP / name).parent.mkdir(parents=True, exist_ok=True)
            (APP / name).write_bytes(data)
            (APP / name).chmod(0o644)
        with (backup / 'schema.log').open('w') as log:
            subprocess.run(['/usr/local/bin/bench','--site','sisuacademylk.com','execute','frappe.reload_doc','--args',json.dumps(['institute_lms','doctype','il_paid_access']),'--kwargs',json.dumps({'force':True})],cwd=BENCH,stdout=log,stderr=log,check=True)
        env = os.environ.copy()
        env['PATH'] = '/opt/node-v24.15.0-linux-x64/bin:' + env.get('PATH', '')
        with (backup / 'build.log').open('w') as log:
            subprocess.run(['npm', 'run', 'build'], cwd=APP / 'frontend', env=env, stdout=log, stderr=log, check=True)
        portal = APP / 'institute_lms/public/portal'
        old = backup / 'institute_lms/public/portal'
        for file in old.rglob('*'):
            target = portal / file.relative_to(old)
            if file.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file, target)
        for path in [portal, *portal.rglob('*')]:
            path.chmod(0o755 if path.is_dir() else 0o644)
        (APP / 'institute_lms/www/campus.html').chmod(0o644)
    except Exception:
        for name in paths:
            src, dst = backup / name, APP / name
            if name in absent:
                if dst.is_file():
                    dst.unlink()
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        print('Previous UI restored. Private build log:', backup / 'build.log')
        raise
    for site in ('sisuacademylk.com', 'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-website-cache'], cwd=BENCH, check=True)
    print('DEPLOYED: unread account notifications, institute selector refresh/autofollow, bank details and single-use student enrollment keys. Restart web AND workers.')
    print('Public paid-access schema updated. Existing active access preserved. No payments collected or WhatsApp enabled. Live bank review and classroom acceptance still required.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED [' + type(exc).__name__ + ']. ' + (str(exc) if isinstance(exc, RuntimeError) else 'Check private build/schema logs; browser result not confirmed.'))
        raise SystemExit(1) from None
