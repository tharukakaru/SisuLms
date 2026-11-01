"""Configure only the dedicated test site; never prints credentials."""
import getpass
import json
import os
from pathlib import Path
import tempfile
import warnings


def main():
    warnings.simplefilter("error", getpass.GetPassWarning)
    bench = Path.home() / 'sisu-hnb-sandbox-bench'
    if Path.cwd().resolve() != bench.resolve():
        raise SystemExit('Run only from ~/sisu-hnb-sandbox-bench')
    path = bench / 'sites/hnb-checkout.localhost/site_config.json'
    config = json.loads(path.read_text())
    token = getpass.getpass('Verify token (32+ characters, also enter in Meta): ')
    secret = getpass.getpass('Meta App Secret (hidden; NOT the access token): ')
    waba = input('WhatsApp Business Account ID: ').strip()
    phone = input('Phone Number ID (not the phone number): ').strip()
    if len(token) < 32 or not secret or not waba.isdigit() or not phone.isdigit():
        raise SystemExit('Invalid configuration; no changes saved.')
    config.update(il_whatsapp_verify_token=token, il_whatsapp_app_secret=secret,
                  il_whatsapp_waba_id=waba, il_whatsapp_phone_id=phone)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.whatsapp-config-')
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump(config, f, indent=2)
            f.flush(); os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    print('Webhook credentials saved privately. Outbound sending was not enabled.')


if __name__ == '__main__':
    main()
