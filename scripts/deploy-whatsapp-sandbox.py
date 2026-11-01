"""Conflict-checked WhatsApp-only deployment into the dedicated sandbox."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

SITE = 'hnb-checkout.localhost'
OLD_HANDLER = 'da3f072afd92b55f6c25ec4368485118febc33b4771abb36b2be32929822ae09'
HANDLER = 'def whatsapp_webhook(**kwargs):\n    from .whatsapp_webhook import handle\n    return handle()\n'
HOOK = 'scheduler_events["cron"]["*/5 * * * *"].append("institute_lms.whatsapp_webhook.reconcile")'


def main():
    os.umask(0o077)
    bench = Path.home() / 'sisu-hnb-sandbox-bench'
    if Path.cwd().resolve() != bench.resolve():
        raise SystemExit('Run only from ~/sisu-hnb-sandbox-bench')
    source = Path(__file__).resolve().parents[1]
    app = bench / 'apps/institute_lms'
    site = bench / 'sites' / SITE
    if not (site / 'site_config.json').is_file():
        raise SystemExit('Expected sandbox site missing.')
    plans = {}
    module = app / 'institute_lms/notification_service.py'
    original = module.read_text()
    index = original.index('def whatsapp_webhook(')
    old = original[index:].strip()
    if old != HANDLER.strip() and hashlib.sha256(old.encode()).hexdigest() != OLD_HANDLER:
        raise SystemExit('CONFLICT: webhook handler changed; no files modified.')
    plans[module] = original[:index] + HANDLER
    hooks = app / 'institute_lms/hooks.py'
    text = hooks.read_text()
    plans[hooks] = text if HOOK in text else text.rstrip() + '\n\n' + HOOK + '\n'
    files = ['institute_lms/whatsapp_webhook.py',
             'scripts/configure-whatsapp-webhook.py', 'scripts/whatsapp-webhook-gateway.py',
             'scripts/verify-whatsapp-endpoint.py']
    folder = 'institute_lms/institute_lms/doctype/il_whatsapp_receipt'
    files += [folder + '/' + p.name for p in (source / folder).iterdir() if p.is_file()]
    for relative in files:
        incoming = (source / relative).read_text()
        destination = app / relative
        if destination.exists() and destination.read_text() != incoming:
            raise SystemExit('CONFLICT: ' + relative + '; no files modified.')
        plans[destination] = incoming
    # Inspect the site using normal Frappe commands without printing site credentials.
    subprocess.run(['bench', '--site', SITE, 'list-apps'], check=True)
    backup = bench / 'local-private/whatsapp-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True, mode=0o700)
    manifest = {}
    for destination in plans:
        relative = destination.relative_to(app)
        manifest[str(relative)] = destination.exists()
        if destination.exists():
            copy = backup / 'source' / relative
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, copy)
    shutil.copy2(site / 'site_config.json', backup / 'site_config.json')
    os.chmod(backup / 'site_config.json', 0o600)
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    subprocess.run(['bench', '--site', SITE, 'backup', '--with-files'], check=True)
    for destination, text in plans.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
    # Import only the new DocType; don't run unrelated payment migration hooks.
    subprocess.run(['bench', '--site', SITE, 'reload-doc', 'institute_lms', 'doctype', 'il_whatsapp_receipt'], check=True)
    subprocess.run(['bench', '--site', SITE, 'clear-cache'], check=True)
    print('PASS: WhatsApp files deployed and receipt schema imported. No payment files changed.')
    print('Private source/config backup: ' + str(backup))
    subprocess.run([str(bench / 'env/bin/python'), str(app / 'scripts/configure-whatsapp-webhook.py')], check=True)
    subprocess.run(['bench', '--site', SITE, 'clear-cache'], check=True)
    print('Restart only the sandbox bench before HTTP verification. Keep the protected LMS tunnel.')


if __name__ == '__main__':
    main()
