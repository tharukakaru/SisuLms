"""Guarded root-operated deployment. Never restore a database automatically."""
import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH / 'apps/institute_lms'
ARCHIVE = Path('/tmp/sisu-targeted-production.tgz')
MANIFEST_DIGEST = '750a7e69e32931083eb19a399cd9a46db4233661d31f03f375e0a7ed98d28a3f'
SITES = ('staging.sisuacademylk.com', 'sisuacademylk.com',
         'platform.sisuacademylk.com')
SERVICES = ('frappe-bench-web:frappe-bench-frappe-web', 'frappe-bench-workers:')
TEXT = {'.py', '.json', '.vue', '.js', '.mjs', '.css', '.html', '.toml', '.txt'}
DATABASE_PREFLIGHT = '''
import frappe, sys, os
from pathlib import Path
bench_root = Path.cwd()
os.chdir(bench_root / 'sites')
frappe.init(site=sys.argv[1], sites_path=str(bench_root / 'sites'))
frappe.connect()
try:
    if 'institute_lms' not in frappe.get_installed_apps():
        raise RuntimeError('Institute LMS is not installed on this site')
    for line in (bench_root / 'apps/institute_lms/institute_lms/patches.txt').read_text().splitlines():
        patch = line.strip()
        if patch and not patch.startswith(('#', '[')) and not frappe.db.exists('Patch Log', {'patch': patch}):
            raise RuntimeError('Historical patch is pending; review before this deployment: ' + patch)
    rows = frappe.db.sql("SELECT COUNT(*) FROM `tabIL Account Invoice` WHERE receipt_number IS NOT NULL AND receipt_number != '' GROUP BY receipt_number HAVING COUNT(*) > 1 LIMIT 1")
    if rows:
        raise RuntimeError('Duplicate invoice numbers require review before migration')
finally:
    frappe.destroy()
'''
SCHEMA_CHECK = '''
import frappe, sys, os
from pathlib import Path
bench_root = Path.cwd()
os.chdir(bench_root / 'sites')
frappe.init(site=sys.argv[1], sites_path=str(bench_root / 'sites'))
frappe.connect()
try:
    for name in ('IL Admin Invite', 'IL Subscription SMS', 'IL Session Reminder', 'IL Renewal Notice', 'IL Student Count Bill', 'IL Student Count Policy'):
        if not frappe.db.table_exists(name):
            raise RuntimeError('Required table missing: ' + name)
    for doctype, column in (('IL Organization', 'removal_request_id'), ('IL Organization', 'removal_progress'), ('IL Organization', 'retired')):
        if not frappe.db.has_column(doctype, column):
            raise RuntimeError('Required database column missing')
finally:
    frappe.destroy()
'''


BACKUP_SITE = '''
import frappe, sys, os
from pathlib import Path
bench_root = Path.cwd()
os.chdir(bench_root / 'sites')
frappe.init(site=sys.argv[1], sites_path=str(bench_root / 'sites'))
frappe.connect()
try:
    from frappe.utils.backups import BackupGenerator
    # Direct generator preserves historic backups: new_backup() first runs
    # retention cleanup, which can fail on manually created directories.
    conf = frappe.conf
    backup = BackupGenerator(conf.db_name, conf.db_user, conf.db_password,
        db_socket=conf.db_socket, db_host=conf.db_host, db_port=conf.db_port,
        db_type=conf.db_type, backup_path=sys.argv[2], ignore_conf=True)
    backup.get_backup(ignore_files=False, force=True)
    for attr in ('backup_path_db', 'backup_path_files',
                 'backup_path_private_files', 'backup_path_conf'):
        path = Path(getattr(backup, attr))
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError('Required backup artifact missing: ' + attr)
    print('Full database, uploads and configuration backup verified: ' + sys.argv[1])
finally:
    frappe.destroy()
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(name, data):
    return sha(data.replace(b'\r\n', b'\n') if Path(name).suffix in TEXT else data)


def safe_path(root, name):
    p = PurePosixPath(name)
    if (not name or '\\' in name or p.is_absolute() or '..' in p.parts
            or str(p) != name or not (name.startswith(('institute_lms/', 'frontend/'))
                                      or name == 'pyproject.toml')):
        raise RuntimeError('Invalid release path')
    path = root / name
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise RuntimeError('Symlink in release path: ' + name)
    if root.resolve() not in path.resolve().parents:
        raise RuntimeError('Release path escapes app')
    return path


def inspect_release(archive, app, expected):
    with tarfile.open(archive) as bundle:
        members = bundle.getmembers()
        names = [m.name for m in members]
        if len(names) != len(set(names)) or any(not m.isfile() for m in members):
            raise RuntimeError('Duplicate or non-file archive entry')
        if sum(m.size for m in members) > 150_000_000:
            raise RuntimeError('Release payload is too large')
        raw = bundle.extractfile('manifest.json').read()
        if sha(raw) != expected:
            raise RuntimeError('Archive and installer do not match')
        manifest = json.loads(raw)
        files = manifest['files']
        if set(names) != {'manifest.json', *files}:
            raise RuntimeError('Unexpected archive files')
        payload = {}
        for name, record in files.items():
            path = safe_path(app, name)
            data = bundle.extractfile(name).read()
            if sha(data) != record['sha256']:
                raise RuntimeError('Payload checksum mismatch: ' + name)
            if name.endswith('.py'):
                ast.parse(data.decode('utf-8-sig'), filename=name)
            if not record['generated']:
                actual = fingerprint(name, path.read_bytes()) if path.exists() else None
                if actual not in (record['before'], fingerprint(name, data)):
                    raise RuntimeError('Source conflict; nothing installed: ' + name)
            payload[name] = data
        for name, digest in manifest['required_assets'].items():
            path = safe_path(app, name)
            data = payload.get(name)
            if data is None:
                if not path.is_file():
                    raise RuntimeError('Required existing asset is missing: ' + name)
                data = path.read_bytes()
            if sha(data) != digest:
                raise RuntimeError('Required asset mismatch: ' + name)
    return manifest, payload


def run(command, log, as_sisu=False):
    if as_sisu:
        command = ['sudo', '-H', '-u', 'sisu', '--', *command]
    subprocess.run(command, cwd=BENCH, stdout=log, stderr=log, check=True)


def bench(site, *args):
    return ['/usr/local/bin/bench', '--site', site, *args]


def maintenance(enabled, log):
    for site in SITES:
        run(bench(site, 'set-maintenance-mode', 'on' if enabled else 'off'), log, True)


def get_url(url):
    print('Checking: ' + url, flush=True)
    with urllib.request.urlopen(url, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError('HTTPS status check failed')
        return response.read()


def check_owner_entry(site):
    from urllib.parse import urlsplit, parse_qs
    url = 'https://' + site + '/campus'
    print('Checking protected owner entry: ' + url, flush=True)
    with urllib.request.urlopen(url, timeout=30) as response:
        target = urlsplit(response.geturl())
        html = response.read().decode()
        if (response.status != 200 or target.scheme != 'https' or target.hostname != site
                or target.path != '/login' or parse_qs(target.query).get('redirect-to') != ['/campus']
                or 'sisu-owner-login' not in html):
            raise RuntimeError('Owner entry did not reach the expected protected sign-in page')


def health(manifest, catalog_before):
    entry = APP / 'institute_lms/www/campus.html'
    assets = re.findall(r'(?:src|href)="(/assets/institute_lms/portal/assets/index-[^"]+\.(?:js|css))"',
                        entry.read_text())
    if len(assets) != 2:
        raise RuntimeError('Unexpected campus entry assets')
    for site in SITES:
        response = json.loads(get_url('https://' + site + '/api/method/institute_lms.plan_catalog.public_catalog'))
        catalog = response.get('message', {})
        if not isinstance(catalog, dict) or not isinstance(catalog.get('plans'), dict) or catalog.get('currency') != 'LKR':
            raise RuntimeError('API health check failed: ' + site)
        if site == 'platform.sisuacademylk.com':
            check_owner_entry(site)
            continue
        html = get_url('https://' + site + '/campus').decode()
        if not all(asset in html for asset in assets):
            raise RuntimeError('Campus is not serving the new release: ' + site)
    for asset in assets:
        path = 'institute_lms/public/' + asset.removeprefix('/assets/institute_lms/')
        if sha(get_url('https://sisuacademylk.com' + asset)) != manifest['required_assets'][path]:
            raise RuntimeError('Served asset hash mismatch')
    catalog = json.loads(get_url('https://sisuacademylk.com/api/method/institute_lms.plan_catalog.public_catalog'))
    if catalog != catalog_before:
        raise RuntimeError('Public plan catalogue changed; review before reopening')


def apply_release(manifest, payload, backup, log, uid, gid):
    changed = False
    migration_started = False
    maintenance_started = False
    try:
        maintenance_started = True
        maintenance(True, log)
        run(['supervisorctl', 'stop', *SERVICES], log)
        print('Maintenance enabled. Taking private database and upload backups...', flush=True)
        for site in SITES:
            folder = backup / site
            folder.mkdir(mode=0o700)
            os.chown(folder, uid, gid)
            shutil.copy2(BENCH / 'sites' / site / 'site_config.json', folder / 'site_config.private.json')
            run([str(BENCH / 'env/bin/python'), '-c', BACKUP_SITE, site, str(folder)], log, True)
            if not any(p.stat().st_size for p in folder.glob('*.sql*')):
                raise RuntimeError('Database backup file missing: ' + site)
        shutil.copy2(BENCH / 'sites/common_site_config.json', backup / 'common_site_config.private.json')
        # Every destination is backed up before the first source write.
        for name in payload:
            src = safe_path(APP, name)
            if src.exists():
                dst = backup / 'source' / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        (backup / 'release.json').write_text(json.dumps(manifest, indent=2))
        changed = True
        for name, data in payload.items():
            dst = safe_path(APP, name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Give newly created package directories the app user's ownership.
            for parent in (dst.parent, *dst.parent.parents):
                if parent == APP:
                    break
                os.chown(parent, uid, gid)
                parent.chmod(0o755)
            tmp = dst.with_name(dst.name + '.sisu-release-tmp')
            if tmp.exists() or tmp.is_symlink():
                raise RuntimeError('Unexpected temporary destination: ' + name)
            with tmp.open('xb') as stream:
                stream.write(data)
            os.chown(tmp, uid, gid)
            tmp.chmod(0o644)
            os.replace(tmp, dst)
        for site in SITES:
            migration_started = True
            print('Migrating ' + site + '...', flush=True)
            run(bench(site, 'migrate'), log, True)
            run([str(BENCH / 'env/bin/python'), '-c', SCHEMA_CHECK, site], log, True)
            run(bench(site, 'clear-cache'), log, True)
            run(bench(site, 'clear-website-cache'), log, True)
        # API smoke checks require web access; workers remain stopped until these pass.
        maintenance(False, log)
        run(['supervisorctl', 'start', SERVICES[0]], log)
        for attempt in range(6):
            try:
                health(manifest, json.loads((backup / 'catalog-before.json').read_text()))
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(5)
        run(['supervisorctl', 'start', SERVICES[1]], log)
        print('DEPLOYED: ' + manifest['commit'] + '. All three active sites migrated; HTTPS and asset checks passed.', flush=True)
        print('Application web/workers started. Root removal worker is NOT installed or enabled by this release. Private backups: ' + str(backup))
    except Exception:
        if maintenance_started:
            if not migration_started:
                if changed:
                    for name in payload:
                        dst = safe_path(APP, name)
                        src = backup / 'source' / name
                        if src.is_file():
                            shutil.copy2(src, dst)
                            os.chown(dst, uid, gid)
                        elif dst.is_file():
                            dst.unlink()
                maintenance(False, log)
                run(['supervisorctl', 'start', *SERVICES], log)
            else:
                # Some schema changes may have committed. Never auto-restore old financial data.
                maintenance(True, log)
                subprocess.run(['supervisorctl', 'stop', *SERVICES], cwd=BENCH, stdout=log, stderr=log)
                print('STOPPED after migration began. Maintenance remains enabled; web/workers stopped. Do not rerun an old installer.', flush=True)
        raise


def resume_checks(manifest, payload, backup):
    recorded = json.loads((backup / 'release.json').read_text())
    if recorded != manifest:
        raise RuntimeError('Recovery backup does not match this release')
    for name, data in payload.items():
        path = safe_path(APP, name)
        if not path.is_file() or fingerprint(name, path.read_bytes()) != fingerprint(name, data):
            raise RuntimeError('Installed release mismatch: ' + name)
    with (backup / 'recovery.log').open('a') as log:
        try:
            for site in SITES:
                run([str(BENCH / 'env/bin/python'), '-c', SCHEMA_CHECK, site], log, True)
            health(manifest, json.loads((backup / 'catalog-before.json').read_text()))
            run(['supervisorctl', 'start', SERVICES[1]], log)
            run(['supervisorctl', 'status', *SERVICES], log)
        except Exception:
            traceback.print_exc(file=log)
            print('Recovery failed; inspect ' + str(backup / 'recovery.log'), flush=True)
            raise
    print('VERIFIED: installed release, three site schemas, HTTPS campus/assets and unchanged public catalogue. Web/workers running. No migrations repeated.', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--resume-checks', metavar='BACKUP_DIRECTORY_NAME')
    args = parser.parse_args()
    if args.apply and args.resume_checks:
        raise RuntimeError('Choose apply or resume-checks, not both')
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run with root SSH using python3')
    import pwd
    import fcntl
    lock_fd = os.open('/var/lock/sisu-merged-deployment.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock_fd)
        raise RuntimeError('Another SISU deployment is already running') from None
    # The process owns this lock until exit, including failure handling.
    os.umask(0o077)
    if ARCHIVE.is_symlink() or ARCHIVE.stat().st_uid != 0 or ARCHIVE.stat().st_mode & 0o022:
        raise RuntimeError('Release archive must be a root-owned, non-writable regular file')
    if APP.is_symlink() or not (APP / 'institute_lms/provision_verification.py').is_file():
        raise RuntimeError('Unexpected app layout or missing hosting verification module')
    for site in SITES:
        config_path = BENCH / 'sites' / site / 'site_config.json'
        config = json.loads(config_path.read_text())
        if config.get('maintenance_mode'):
            raise RuntimeError('A site is already in maintenance mode: ' + site)
    manifest, payload = inspect_release(ARCHIVE, APP, MANIFEST_DIGEST)
    print('PREFLIGHT PASS: ' + manifest['commit'] + '; ' + str(len(payload)) + ' files. Source hashes and asset dependencies verified.', flush=True)
    if args.resume_checks:
        if not re.fullmatch(r'merged-production-[0-9]{8}T[0-9]{12}Z', args.resume_checks):
            raise RuntimeError('Invalid backup directory name')
        backup = Path('/home/sisu/.sisu-secrets') / args.resume_checks
        if backup.is_symlink() or not backup.is_dir():
            raise RuntimeError('Private backup directory missing')
        resume_checks(manifest, payload, backup)
        return
    if not args.apply:
        return
    account = pwd.getpwnam('sisu')
    root = Path('/home/sisu/.sisu-secrets')
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise RuntimeError('Existing private backup directory is required')
    backup = root / ('merged-production-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700)
    os.chown(backup, account.pw_uid, account.pw_gid)
    print('Private release log: ' + str(backup / 'deployment.log'), flush=True)
    with (backup / 'deployment.log').open('w') as log:
        try:
            # Install only the new declared dependency, before any downtime.
            run([str(BENCH / 'env/bin/python'), '-m', 'pip', 'check'], log, True)
            run([str(BENCH / 'env/bin/python'), '-c', 'import pyotp, reportlab, pypdf, cryptography'], log, True)
            run(['supervisorctl', 'status', *SERVICES], log)
            for command in ('backup', 'migrate', 'set-maintenance-mode'):
                run(bench(SITES[0], command, '--help'), log, True)
            for site in SITES:
                run([str(BENCH / 'env/bin/python'), '-c', DATABASE_PREFLIGHT, site], log, True)
            catalog = json.loads(get_url('https://sisuacademylk.com/api/method/institute_lms.plan_catalog.public_catalog'))
            (backup / 'catalog-before.json').write_text(json.dumps(catalog))
            apply_release(manifest, payload, backup, log, account.pw_uid, account.pw_gid)
        except Exception as exc:
            traceback.print_exc(file=log)
            print('Release failed [' + type(exc).__name__ + ']. Inspect the private log: ' + str(backup / 'deployment.log'), flush=True)
            raise


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: ' + (str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__))
        raise SystemExit(1) from None
