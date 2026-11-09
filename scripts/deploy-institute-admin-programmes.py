"""Deploy institute teacher controls; retain old assets for open tabs."""
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH / 'apps/institute_lms'
ALLOWED = {'frontend/src/native/ProviderMetrics.vue', 'institute_lms/institute_lms/doctype/il_account_subscription/il_account_subscription.json', 'institute_lms/learning_spaces.py', 'institute_lms/programme_grading.py', 'frontend/src/native/Programmes.vue', 'frontend/src/native/MembershipMail.vue', 'institute_lms/institute_lms/doctype/il_programme_module/il_programme_module.json', 'institute_lms/institute_lms/doctype/il_programme/il_programme.json', 'institute_lms/portal_session.py', 'frontend/src/native/ProviderHome.vue', 'institute_lms/programme_courses.py', 'institute_lms/programme_learning.py', 'institute_lms/public_student.py', 'institute_lms/teaching.py', 'institute_lms/notification_service.py', 'institute_lms/institute_lms/doctype/il_programme_progress/il_programme_progress.py', 'institute_lms/profiles.py', 'institute_lms/programme_certificates.py', 'frontend/src/commerce/Connections.vue', 'institute_lms/institute_lms/doctype/il_programme_progress/__init__.py', 'institute_lms/saas.py', 'frontend/src/native/SubscriptionBilling.vue', 'frontend/src/native/StudentClassrooms.vue', 'frontend/src/App.vue', 'institute_lms/institute_lms/doctype/il_programme_progress/il_programme_progress.json', 'institute_lms/account_billing.py', 'frontend/src/native/ModuleProgress.vue', 'institute_lms/api.py', 'institute_lms/invitations.py', 'frontend/src/native/PortalRoot.vue', 'institute_lms/commercial.py'}


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o022)
    with tarfile.open('/tmp/sisu-institute-admin-programmes.tgz') as archive:
        manifest = json.load(archive.extractfile('manifest.json'))
        if set(manifest) != ALLOWED or len(archive.getmembers()) != len(ALLOWED)+1:
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
            if actual not in (manifest[name]['before'], manifest[name]['after']):
                raise RuntimeError('Source conflict: ' + name)
    root = Path.home() / '.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise RuntimeError('Private backup directory required')
    backup = root / ('institute-admin-programmes-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
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
    try:
        for name, data in payload.items():
            (APP / name).parent.mkdir(parents=True, exist_ok=True)
            (APP / name).write_bytes(data)
            (APP / name).chmod(0o644)
        for site in ('sisuacademylk.com', 'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
            for schema in ('il_account_subscription','il_programme_module','il_programme','il_programme_progress'):
                subprocess.run(['/usr/local/bin/bench', '--site', site, 'reload-doc', 'institute_lms', 'doctype', schema], cwd=BENCH, check=True)
            subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-cache'], cwd=BENCH, check=True)
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
        print('Previous sources/UI restored; additive programme schema may remain. Private build log:', backup / 'build.log')
        raise
    for site in ('sisuacademylk.com', 'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-cache'], cwd=BENCH, check=True)
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-website-cache'], cwd=BENCH, check=True)
    print('DEPLOYED: institute admin controls and programme learning across roles; restart web/workers and run checks. Hard-refresh before testing.')
    print('Added programme progress and grading schema. Existing enrollments/payments unchanged. Run rollback checks, then hard-refresh. Gateway remains held.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED [' + type(exc).__name__ + ']. ' + (str(exc) if isinstance(exc, RuntimeError) else 'Check private build log; browser result not confirmed.'))
        raise SystemExit(1) from None
