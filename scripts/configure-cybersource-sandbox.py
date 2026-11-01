"""Run locally from the isolated Ubuntu bench. No network calls or secret output."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', required=True)
    parser.add_argument('--enable', action='store_true', help='Enable ONLY on a dedicated test site')
    args = parser.parse_args()
    bench = Path.cwd().resolve()
    sites = (bench / 'sites').resolve()
    site = (sites / args.site).resolve()
    if site.parent != sites or not (site / 'site_config.json').is_file():
        raise SystemExit('Run from the test bench and specify an existing site name')
    if input('Type SANDBOX to confirm this site contains only test financial data: ').strip() != 'SANDBOX':
        raise SystemExit('Cancelled')
    checkout_origin = input('Exact HTTPS checkout origin (no trailing slash): ').strip()
    u = urlsplit(checkout_origin)
    if u.scheme != 'https' or not u.hostname or u.username or u.password or u.path or u.query or u.fragment:
        raise SystemExit('An exact HTTPS origin is required')
    scope = input('Merchant scope (platform or tuition:PROVIDER_ACCOUNT): ').strip()
    if scope != 'platform' and not (scope.startswith('tuition:') and len(scope) > 8):
        raise SystemExit('Invalid scope')
    merchant = getpass.getpass('Sandbox merchant ID (hidden): ').strip()
    key_id = getpass.getpass('Registered JWT key ID (hidden): ').strip()
    cert_path = Path(input('Local path to the sandbox P12 certificate: ').strip()).expanduser()
    password = getpass.getpass('P12 password (hidden): ')
    if not merchant or not key_id or not password:
        raise SystemExit('Credentials are required')
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    content = cert_path.read_bytes()
    try:
        key, cert, _ = load_key_and_certificates(content, password.encode())
        if not isinstance(key, RSAPrivateKey) or cert is None: raise ValueError()
    except ValueError:
        raise SystemExit('P12 could not be unlocked as an RSA certificate') from None
    methods = [x.strip() for x in input('Activated methods, comma-separated (e.g. PANENTRY): ').split(',')]
    if not methods or not set(methods) <= {'PANENTRY','GOOGLEPAY','APPLEPAY','CLICKTOPAY'}:
        raise SystemExit('Specify only activated payment methods')
    currencies = [x.strip() for x in input('HNB-enabled currencies, comma-separated (usually LKR): ').split(',')]
    if not currencies or not set(currencies) <= {'LKR','USD'}: raise SystemExit('Unsupported currency')
    config_path = site / 'site_config.json'
    config = json.loads(config_path.read_text())
    existing_origin = config.get('host_name', '').rstrip('/')
    if existing_origin != checkout_origin:
        raise SystemExit('First configure this test site host_name to match the HTTPS checkout origin')
    private = bench / 'local-private' / 'cybersource'
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(private, 0o700)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = private / (args.site + '-' + stamp + '.json')
    with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        f.write(config_path.read_text())
    target = private / (hashlib.sha256(scope.encode()).hexdigest()[:16] + '-' + stamp + '.p12')
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as f:
        f.write(content)
    root = config.setdefault('il_cybersource', {})
    root.update(enabled=args.enable, mode='sandbox', origin=checkout_origin)
    root.setdefault('merchants', {})[scope] = dict(merchant_id=merchant, key_id=key_id,
        p12_path=str(target), p12_password=password, methods=methods, currencies=currencies)
    temporary = config_path.with_name('site_config.cybersource.tmp')
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        json.dump(config, f, indent=2)
    os.replace(temporary, config_path)
    print('Sandbox configuration saved. Enabled:', args.enable)
    print('No credentials printed. No provider requests, payments or production changes performed.')


if __name__ == '__main__':
    main()
