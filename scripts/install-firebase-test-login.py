"""Install a sandbox-only form using standard Frappe password authentication."""
from datetime import datetime, timezone
import os
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

os.umask(0o077)
bench = Path.home() / 'sisu-hnb-sandbox-bench'
if os.name != 'posix' or Path.cwd().resolve() != bench.resolve():
    raise SystemExit('Run inside ~/sisu-hnb-sandbox-bench only.')
site = 'hnb-checkout.localhost'
if not (bench / 'sites' / site / 'site_config.json').is_file():
    raise SystemExit('Sandbox site missing.')
source = Path(__file__).resolve().parents[1]
app = bench / 'apps/institute_lms'
names = ['institute_lms/www/sandbox_firebase_login' + suffix for suffix in ('.py', '.html')]
names.extend(['frontend/src/native/PortalRoot.vue', 'frontend/src/native/FirebasePush.vue'])
baseline = json.loads((source / 'scripts/firebase-push-baseline.json').read_text())
for name in names:
    target = app / name
    if target.exists() and target.read_text() != (source / name).read_text() and hashlib.sha256(target.read_text().strip().encode()).hexdigest() != baseline.get(name):
        raise SystemExit('Conflict in sandbox login page; no files changed.')
backup = bench / 'local-private/firebase-login-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup.mkdir(parents=True, mode=0o700)
for name in names:
    target = app / name
    if target.exists(): shutil.copy2(target, backup / target.name)
    target.write_text((source / name).read_text())
subprocess.run(['bench', 'build', '--app', 'institute_lms'], check=True)
subprocess.run(['bench', '--site', site, 'clear-cache'], check=True)
print('PASS: sandbox-only login page installed. Existing login and authentication rules unchanged.')
print('Open http://localhost:8001/sandbox_firebase_login')
