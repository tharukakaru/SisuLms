"""Install only Firebase browser test files; preserve all other integrations."""
from datetime import datetime, timezone
import getpass
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import warnings

SITE = 'hnb-checkout.localhost'
FILES = ('institute_lms/devices.py', 'institute_lms/firebase_push.py', 'frontend/src/App.vue',
         'frontend/src/native/PortalRoot.vue', 'institute_lms/www/sandbox_firebase_login.py',
         'institute_lms/www/sandbox_firebase_login.html',
         'institute_lms/public/firebase-messaging-sw.js',
         'frontend/src/native/NotificationCenter.vue', 'frontend/src/native/FirebasePush.vue')


def backend_check(bench, tester):
    stage = 'Import Frappe'
    frappe = None
    previous_directory = Path.cwd()
    try:
        import frappe
        stage = 'Initialize sandbox site'
        # Bench commands run Frappe from sites/. Some framework logging and
        # application paths remain relative even with an absolute sites_path.
        os.chdir(bench / 'sites')
        frappe.init(site=SITE, sites_path=str(bench / 'sites'))
        stage = 'Connect to sandbox database'
        frappe.connect()
        stage = 'Find enabled sandbox test account'
        if not tester or tester == 'Guest' or not frappe.db.get_value('User', tester, 'enabled'):
            print('CHECK FAILED: test account is missing or disabled. Use Administrator with that exact capitalization.')
            raise SystemExit(1)
        print('PASS: sandbox database and test account checked.')
        stage = 'Import installed Firebase backend'
        from institute_lms.firebase_backend import get_app
        stage = 'Load protected Firebase credential and initialize SDK'
        firebase_app = get_app()
        print('PASS: protected Firebase credential loaded.')
        stage = 'Authenticate with Google OAuth'
        from google.auth.transport.requests import Request
        firebase_app.credential.get_credential().refresh(Request())
        print('PASS: Firebase Google authentication succeeded. No notifications sent.')
    except Exception as error:
        # Only fixed stages and allowlisted class names; never exception messages,
        # response bodies, tokens, SQL connection parameters or traceback locals.
        known = {'ModuleNotFoundError', 'ImportError', 'PermissionError', 'FileNotFoundError',
                 'ValueError', 'TypeError', 'AttributeError', 'OperationalError',
                 'ConnectionError', 'ConnectionRefusedError', 'AuthenticationError',
                 'RefreshError', 'TransportError', 'Timeout', 'SSLError', 'ValidationError'}
        kind = type(error).__name__
        print('CHECK FAILED: ' + stage + ' [' + (kind if kind in known else 'other error') + ']')
        if isinstance(error, FileNotFoundError):
            # Report only recognized framework files, never arbitrary paths.
            name = Path(error.filename or '').name
            if name in {'database.log', 'frappe.log', 'web.log', 'apps.txt', 'site_config.json', 'common_site_config.json'}:
                print('Missing framework file: ' + name)
        print('No deployment or configuration writes were performed by this check.')
        raise SystemExit(1) from None
    finally:
        if frappe is not None:
            try:
                frappe.destroy()
            except Exception:
                pass
        os.chdir(previous_directory)


def main():
    os.umask(0o077)
    warnings.simplefilter('error', getpass.GetPassWarning)
    logging.disable(logging.CRITICAL)
    bench = Path.home() / 'sisu-hnb-sandbox-bench'
    if os.name != 'posix' or Path.cwd().resolve() != bench.resolve():
        raise ValueError('Run only inside the Ubuntu sandbox bench.')
    if '--check-backend' in sys.argv:
        backend_check(bench, 'Administrator')
        return
    source = Path(__file__).resolve().parents[1]
    app = bench / 'apps/institute_lms'
    baseline = json.loads((source / 'scripts/firebase-push-baseline.json').read_text())
    for name in FILES:
        target = app / name
        if target.exists():
            current = target.read_text()
            if current != (source / name).read_text() and hashlib.sha256(current.strip().encode()).hexdigest() != baseline.get(name):
                raise ValueError('Source conflict in ' + name + '; nothing overwritten.')
    config_path = bench / 'sites' / SITE / 'site_config.json'
    original = config_path.read_bytes()
    config = json.loads(original)
    if config.get('il_push_adapter'):
        raise ValueError('Existing push adapter found; stop for review.')
    settings = config.get('il_firebase_sandbox') or {}
    if settings.get('project_id') != 'sisu-lms' or not settings.get('credential_path'):
        raise ValueError('Complete protected Admin credential setup first.')
    spec = importlib.util.spec_from_file_location('firebase_push_setup', source / 'institute_lms/firebase_push.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    print('Use Project settings > General > Your Web app > SDK setup and configuration.')
    web = {key: getpass.getpass('Firebase Web ' + key + ' (hidden): ').strip() for key in helper.FIELDS}
    vapid = getpass.getpass('Public VAPID key (hidden; Cloud Messaging > Web Push certificates): ').strip()
    try:
        helper.web_settings(web, vapid)
    except helper.WebConfigurationError as error:
        print('Configuration check: ' + str(error))
        print('No files changed. Re-run and paste only each value, not the field name or JavaScript line.')
        raise SystemExit(1) from None
    tester = getpass.getpass('Existing sandbox login email (or Administrator; hidden): ').strip()
    backend_check(bench, tester)
    if config_path.read_bytes() != original:
        raise ValueError('Configuration changed during setup; retry after review.')
    backup = bench / 'local-private/firebase-push-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True, mode=0o700)
    shutil.copy2(config_path, backup / 'site_config.json')
    os.chmod(backup / 'site_config.json', 0o600)
    for name in FILES:
        target = app / name
        if target.exists():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((source / name).read_text())
    # Configuration stays disabled if build fails. No dependency changes are required.
    subprocess.run(['bench', 'build', '--app', 'institute_lms'], check=True)
    if config_path.read_bytes() != original:
        raise ValueError('Configuration changed during build; source backed up, activation stopped.')
    config['il_firebase_sandbox'] = {**settings, 'web': web, 'vapid_key': vapid,
        'test_user': tester, 'self_test_enabled': True, 'push_enabled': False}
    fd, temporary = tempfile.mkstemp(dir=config_path.parent, prefix='.firebase-web-')
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(config, output, indent=2); output.flush(); os.fsync(output.fileno())
        os.replace(temporary, config_path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    subprocess.run(['bench', '--site', SITE, 'clear-cache'], check=True)
    print('PASS: Vue browser registration and single-account self-test configured in sandbox.')
    print('Customer sending remains disabled. No il_push_adapter was configured.')
    print('Private source/config backup: ' + str(backup))
    print('Restart only the sandbox bench. Open http://localhost:8001/campus?firebase_test=1 and sign in as the selected tester.')


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt):
        print('Setup stopped. Check source conflicts, Web fields, existing test account, Google authentication and build output. No secrets printed.')
        raise SystemExit(1) from None
