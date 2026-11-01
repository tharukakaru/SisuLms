"""Import a private Firebase key; never print its contents or enable push."""
import getpass
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import warnings


def main():
    warnings.simplefilter('error', getpass.GetPassWarning)
    logging.disable(logging.CRITICAL)
    os.umask(0o077)
    bench = Path.home() / 'sisu-hnb-sandbox-bench'
    if os.name != 'posix' or Path.cwd().resolve() != bench.resolve():
        raise ValueError('Run from the dedicated Ubuntu sandbox bench.')
    config_path = bench / 'sites/hnb-checkout.localhost/site_config.json'
    original = config_path.read_bytes()
    config = json.loads(original)
    if config.get('il_push_adapter'):
        raise ValueError('An existing push adapter is configured; stop for review.')
    source_module = Path(__file__).resolve().parents[1] / 'institute_lms/firebase_backend.py'
    destination_module = bench / 'apps/institute_lms/institute_lms/firebase_backend.py'
    if destination_module.exists() and destination_module.read_bytes() != source_module.read_bytes():
        raise ValueError('Firebase module conflict; no files changed.')
    import firebase_admin
    from firebase_admin import credentials
    spec = importlib.util.spec_from_file_location('firebase_setup_backend', source_module)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    raw_path = getpass.getpass('Local downloaded JSON path (hidden; Windows or Ubuntu path): ').strip().strip('"')
    if re.match(r'^[A-Za-z]:[\\/]', raw_path):
        raw_path = '/mnt/' + raw_path[0].lower() + '/' + raw_path[3:].replace('\\', '/')
    source = Path(raw_path).expanduser()
    if not source.is_file() or source.stat().st_size > 65536:
        raise ValueError('JSON file missing or exceeds 64 KiB.')
    raw = source.read_bytes()
    data = module.validate_metadata(json.loads(raw))
    # Validate SDK parsing/key material before copying anything; this sends no request.
    credential = credentials.Certificate(data)
    if credential.project_id != module.PROJECT:
        raise ValueError('SDK project mismatch.')
    directory = Path.home() / '.sisu-secrets/firebase/hnb-checkout.localhost'
    for part in (Path.home()/'.sisu-secrets', Path.home()/'.sisu-secrets/firebase', directory):
        if part.is_symlink(): raise ValueError('Symlink credential directory refused.')
        part.mkdir(mode=0o700, exist_ok=True)
        if part.stat().st_uid != os.getuid(): raise ValueError('Credential directory owner mismatch.')
        os.chmod(part, 0o700)
    target = directory / ('service-account-' + secrets.token_hex(8) + '.json')
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as output:
        output.write(raw)
    try:
        app = module.initialize(target, 'sisu-setup-' + secrets.token_hex(8))
        if app.project_id != module.PROJECT: raise ValueError('Initialized project mismatch.')
        firebase_admin.delete_app(app)
        if config_path.read_bytes() != original: raise ValueError('Site configuration changed; retry after review.')
        config['il_firebase_sandbox'] = {'project_id': module.PROJECT, 'credential_path': str(target), 'push_enabled': False}
        # No key contents in config/backups; only the protected external path.
        destination_module.write_bytes(source_module.read_bytes())
        fd, temporary = tempfile.mkstemp(dir=config_path.parent, prefix='.firebase-config-')
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, 'w') as output:
                json.dump(config, output, indent=2); output.flush(); os.fsync(output.fileno())
            os.replace(temporary, config_path)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    print('PASS: credential Firebase project ID = sisu-lms')
    print('PASS: Firebase Admin SDK initialized locally; no network requests or messages sent.')
    print('PASS: credential stored outside bench/repository in owner-only Linux storage (directories 0700, file 0600).')
    print('PASS: normal bench backups contain only the credential path, not the Firebase key.')
    print('PASS: push remains disabled; no il_push_adapter was configured.')
    print('Original download remains in place. After confirming success, remove it from Downloads and any synced copies.')
    print('Exclude ~/.sisu-secrets from shared/home-directory backup jobs; ordinary bench backup does not include it.')


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt):
        # Library parsing errors can include input; never emit exception values/tracebacks.
        print('Setup stopped safely. Check sandbox directory, installed SDK, JSON project and permissions. No secrets printed.', file=sys.stderr)
        raise SystemExit(1) from None
