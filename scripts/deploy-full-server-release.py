"""Pinned SISU release deployment. Run as root; app commands run as sisu.

Migration failures deliberately leave maintenance enabled and workers stopped.
Backups include databases, uploaded files, configuration and the prior app tree.
"""
import hashlib
import json
import os
import pwd
import re
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH / 'apps/institute_lms'
ARCHIVE = Path('/tmp/sisu-release-source.tgz')
CHECK = Path('/tmp/sisu-check-release.py')
SITES = ('teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com')
GROUPS = ('frappe-bench-web:', 'frappe-bench-workers:')
ARCHIVE_SHA = 'e68e76f2237290254ee7893581049b69a90d5940c08559f356853b294349f6ab'
CHECK_SHA = 'cd03a6f045af1ffff5fc3279a4d38135dc99ee45e69f6d551d2f92905f0c129e'
stage = 'preflight'
backup = None
paused = False


def user_run(args, *, cwd=BENCH, capture=False):
    command = ['sudo', '-u', 'sisu', '-H', 'env',
               'PATH=/opt/node-v24.15.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', *map(str, args)]
    if capture:
        return subprocess.check_output(command, cwd=cwd, stderr=subprocess.DEVNULL, text=True)
    with (backup / 'deployment.log').open('a') as log:
        subprocess.run(command, cwd=cwd, stdout=log, stderr=log, check=True)


def private_dir(path, uid, gid):
    path.mkdir(mode=0o700, exist_ok=True)
    if path.is_symlink() or path.stat().st_mode & 0o077:
        raise RuntimeError('Unsafe private backup directory')
    os.chown(path, uid, gid)


def main():
    global stage, backup, paused
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run with server python3 as root')
    os.umask(0o022)
    for path, expected in ((ARCHIVE, ARCHIVE_SHA), (CHECK, CHECK_SHA)):
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Release or checker checksum mismatch')
    user_run([BENCH / 'env/bin/python', CHECK], capture=True)
    account = pwd.getpwnam('sisu')
    uid, gid = account.pw_uid, account.pw_gid
    # Dependency verification occurs before any downtime, with no automatic upgrades.
    with tarfile.open(ARCHIVE) as archive:
        metadata = archive.extractfile('pyproject.toml').read().decode()
        dep_check = '''import json,sys,tomllib
from importlib.metadata import version
from packaging.requirements import Requirement
bad=[]
for text in tomllib.loads(sys.argv[1])['project']['dependencies']:
 r=Requirement(text)
 try: ok=version(r.name) in r.specifier
 except Exception: ok=False
 if not ok: bad.append(str(r))
print(json.dumps(bad))
'''
        missing = json.loads(user_run([BENCH / 'env/bin/python', '-c', dep_check, metadata], capture=True))
        if missing:
            print('Required dependency versions:', ', '.join(missing))
            raise RuntimeError('Resolve dependencies before deployment; nothing updated')
        for name in ('frontend/package.json', 'frontend/package-lock.json'):
            if name in archive.getnames() and archive.extractfile(name).read().replace(b'\r\n', b'\n') != (APP / name).read_bytes().replace(b'\r\n', b'\n'):
                raise RuntimeError('Frontend dependency changes need a staged install first')
    status = subprocess.check_output(['supervisorctl', 'status'], text=True)
    processes = [line.split() for line in status.splitlines() if line.startswith(GROUPS)]
    if not processes or any(row[1] != 'RUNNING' for row in processes):
        raise RuntimeError('Expected bench processes must be running before deployment')
    original = {}
    for site in SITES:
        config = BENCH / 'sites' / site / 'site_config.json'
        settings = json.loads(config.read_text())
        if settings.get('maintenance_mode'):
            raise RuntimeError('Site already under maintenance; review required')
        original[site] = config.read_bytes()
    if shutil.disk_usage(BENCH).free < 10 * 1024**3:
        raise RuntimeError('At least 10 GiB free space required for backups')
    root = Path('/home/sisu/.sisu-secrets')
    private_dir(root, uid, gid)
    backup = root / ('full-release-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    private_dir(backup, uid, gid)
    (backup / 'deployment.log').touch(mode=0o600)
    print('Private recovery directory:', backup, flush=True)
    stage = 'pause access and workers'
    paused = True
    for site in SITES:
        (backup / (site + '-original-config.json')).write_bytes(original[site])
        (backup / (site + '-original-config.json')).chmod(0o600)
        user_run(['/usr/local/bin/bench', '--site', site, 'set-maintenance-mode', 'on'])
    subprocess.run(['supervisorctl', 'stop', *[g + '*' for g in GROUPS]], check=True)
    stage = 'complete backups'
    for site in SITES:
        target = backup / site
        private_dir(target, uid, gid)
        user_run(['/usr/local/bin/bench', '--site', site, 'backup', '--with-files', '--backup-path', target])
        print('BACKED UP:', site, flush=True)
    with tarfile.open(backup / 'previous-app.tgz', 'w:gz') as archive:
        def include(info):
            return None if any(part in ('.git', 'node_modules', '__pycache__') for part in Path(info.name).parts) else info
        archive.add(APP, arcname='institute_lms', filter=include)
    (backup / 'previous-app.tgz').chmod(0o600)
    stage = 'install reviewed source'
    with tarfile.open(ARCHIVE) as archive:
        for entry in archive.getmembers():
            if entry.name == 'release-manifest.json':
                continue
            target = APP / entry.name
            if not entry.isfile() or not target.resolve().is_relative_to(APP.resolve()) or target.is_symlink():
                raise RuntimeError('Unsafe archive target')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(entry).read())
            target.chmod(0o644)
            os.chown(target, uid, gid)
            parent = target.parent
            while parent != APP:
                os.chown(parent, uid, gid)
                parent = parent.parent
    stage = 'database migrations'
    for site in SITES:
        user_run(['/usr/local/bin/bench', '--site', site, 'migrate'])
        print('MIGRATED:', site, flush=True)
    stage = 'frontend build'
    # Retain hashed assets for older tabs, as well as the complete private backup.
    previous = backup / 'previous-public-portal'
    shutil.copytree(APP / 'institute_lms/public/portal', previous)
    user_run(['/opt/node-v24.15.0-linux-x64/bin/npm', 'run', 'build'], cwd=APP / 'frontend')
    portal = APP / 'institute_lms/public/portal'
    for old in previous.rglob('*'):
        target = portal / old.relative_to(previous)
        if old.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(old, target)
    for path in [portal, *portal.rglob('*')]:
        if path.is_symlink():
            raise RuntimeError('Unexpected public asset symlink')
        path.chmod(0o755 if path.is_dir() else 0o644)
        os.chown(path, uid, gid)
    (APP / 'institute_lms/www/campus.html').chmod(0o644)
    stage = 'cache refresh and restart'
    for site in SITES:
        user_run(['/usr/local/bin/bench', '--site', site, 'clear-cache'])
        user_run(['/usr/local/bin/bench', '--site', site, 'clear-website-cache'])
    subprocess.run(['supervisorctl', 'start', *[g + '*' for g in GROUPS]], check=True)
    for site in SITES:
        user_run(['/usr/local/bin/bench', '--site', site, 'set-maintenance-mode', 'off'])
    paused = False
    print('DEPLOYED: merged LMS source, schemas and frontend across the three existing sites.')
    print('Public signup remains sandbox-only; email/SMS restrictions remain unchanged.')
    print('Browser acceptance is still required: profiles, quizzes, programmes, role access and live classes.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED at', stage, '[' + type(exc).__name__ + ']')
        if isinstance(exc, RuntimeError):
            print(str(exc))
        if backup:
            print('Private recovery files and log:', backup)
        if paused:
            # Keep every site closed if even one restart/maintenance toggle failed.
            for site in SITES:
                try:
                    user_run(['/usr/local/bin/bench', '--site', site, 'set-maintenance-mode', 'on'])
                except Exception:
                    pass
            subprocess.run(['supervisorctl', 'stop', *[g + '*' for g in GROUPS]], check=False)
            print('Sites held in maintenance with bench processes stopped. Do not rerun blindly or restore code without reviewing database state.')
        raise SystemExit(1) from None
