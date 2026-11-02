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
ALLOWED = {'frontend/src/commerce/ProfileEditor.vue', 'frontend/src/native/DemoLesson.vue', 'institute_lms/learning_spaces.py', 'frontend/src/native/PasswordReset.vue', 'institute_lms/account_billing.py', 'frontend/src/native/GeneralCampus.vue', 'institute_lms/storage.py', 'frontend/src/AccountControls.vue', 'institute_lms/profiles.py', 'frontend/src/native/PasswordConfirmation.vue', 'institute_lms/demo_learning.py', 'frontend/src/native/StudentClassrooms.vue', 'scripts/seed-public-demo-content.py', 'frontend/src/native/PortalRoot.vue', 'institute_lms/password_reset.py', 'institute_lms/profile_storage.py', 'institute_lms/saas.py'}


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o022)
    with tarfile.open('/tmp/sisu-student-round2.tgz') as archive:
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
    backup = root / ('student-round2-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
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
        with (backup / 'demo-seed.log').open('w') as log:
            subprocess.run([sys.executable, str(APP / 'scripts/seed-public-demo-content.py')], cwd=BENCH, stdout=log, stderr=log, check=True)
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
    print('DEPLOYED: personal profile save/uploads, password-reset overlay, spaced account buttons and follow-based demo classroom cards. Restart web AND workers before browser tests.')
    print('SEEDED: public demo institute, institute teacher, independent teacher, free/locked practice cards and provider news. Demo key: SISU-DEMO. No payment or real paid-class access granted; WhatsApp unchanged. No messages sent during deployment.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED [' + type(exc).__name__ + ']. ' + (str(exc) if isinstance(exc, RuntimeError) else 'Check private build/demo-seed logs; browser result not confirmed.'))
        raise SystemExit(1) from None
