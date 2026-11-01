"""Read-only Meta credential checks; stage token without enabling outbound dispatch."""
from datetime import datetime, timezone
import argparse
import getpass
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import re
import tempfile
import time
import warnings
import requests

class CheckError(Exception):
    pass


REQUIRED = {'whatsapp_business_management', 'whatsapp_business_messaging'}


def safe_meta_error(error, sensitive):
    if not isinstance(error, dict):
        return 'No diagnostic text supplied'
    text = ' | '.join(error.get(k, '') for k in ('error_user_title', 'error_user_msg', 'message') if isinstance(error.get(k), str))
    for value in sorted((v for v in sensitive if isinstance(v, str) and v), key=len, reverse=True):
        text = text.replace(value, '[REDACTED]')
    text = re.sub(r'https?://[^\s]+', '[URL REDACTED]', text)
    text = re.sub(r'[A-Za-z0-9_+/=|.-]{32,}', '[VALUE REDACTED]', text)
    return ascii(' '.join(text.split())[:700])


def inspect_token(data, app_id, now):
    if data.get('is_valid') is not True or str(data.get('app_id')) != app_id:
        raise CheckError('Token invalid or issued to a different app.')
    if not REQUIRED <= set(data.get('scopes') or []):
        raise CheckError('Token lacks required WhatsApp management/messaging permissions.')
    result = {}
    for key in ('expires_at', 'data_access_expires_at'):
        value = data.get(key)
        if type(value) is not int or value < 0:
            raise CheckError('Token expiration metadata unavailable; inspect in Meta before proceeding.')
        if value and value <= now:
            raise CheckError('Token or data access has expired.')
        result[key] = value
    return result


def phone_matches(row, phone_id, number):
    return str(row.get('id')) == phone_id and re.sub(r'\D', '', str(row.get('display_phone_number', ''))) == number


def staged_config(config, credentials, secret=None, verify_token=None):
    result = dict(config)
    if secret is not None:
        if config.get('il_whatsapp_token'):
            raise CheckError('An active outbound token already exists. Stop and review before switching accounts.')
        if not secret or not verify_token or len(verify_token) < 32:
            raise CheckError('App Secret and 32+ character verify token required.')
        result.update(il_whatsapp_app_id=credentials['app_id'],
            il_whatsapp_app_secret=secret, il_whatsapp_verify_token=verify_token,
            il_whatsapp_waba_id=credentials['waba_id'], il_whatsapp_phone_id=credentials['phone_id'])
    result['il_whatsapp_pending_credentials'] = credentials
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new-account', action='store_true', help='Verify and atomically replace sandbox webhook account configuration')
    args = parser.parse_args()
    warnings.simplefilter('error', getpass.GetPassWarning)
    logging.disable(logging.CRITICAL)
    bench = Path.home() / 'sisu-hnb-sandbox-bench'
    if Path.cwd().resolve() != bench.resolve():
        raise CheckError('Run only from ~/sisu-hnb-sandbox-bench.')
    path = bench / 'sites/hnb-checkout.localhost/site_config.json'
    original = path.read_bytes()
    config = json.loads(original)
    if args.new_account and config.get('il_whatsapp_token'):
        raise CheckError('An active outbound token already exists. Review before changing accounts.')
    app_id = getpass.getpass('Meta App ID (hidden): ').strip()
    version = input('Supported Graph API version shown in Meta (vNN.0): ').strip()
    waba = getpass.getpass('WhatsApp Business Account ID (hidden): ').strip()
    phone = getpass.getpass('Phone Number ID (hidden): ').strip()
    number = re.sub(r'\D', '', getpass.getpass('Registered business number including country code (hidden): '))
    if not all(v.isdigit() for v in (app_id, waba, phone)) or not re.fullmatch(r'v\d{2,3}\.0', version) or not 7 <= len(number) <= 15:
        raise CheckError('Invalid IDs, version or business number.')
    if not args.new_account and (waba != str(config.get('il_whatsapp_waba_id')) or phone != str(config.get('il_whatsapp_phone_id'))):
        raise CheckError('IDs differ from webhook configuration. Review before continuing; nothing changed.')
    secret = getpass.getpass('NEW Meta App Secret (hidden): ').strip() if args.new_account else config.get('il_whatsapp_app_secret')
    if not secret:
        raise CheckError('Complete the webhook configuration first.')
    token = getpass.getpass('System User access token (hidden): ').strip()
    if not token:
        raise CheckError('Access token is empty.')
    verify_token = getpass.getpass('Webhook Verify token (32+ characters; hidden; save in password manager): ') if args.new_account else None
    if args.new_account and len(verify_token) < 32:
        raise CheckError('Verify token must contain at least 32 characters; nothing changed.')
    session = requests.Session(); session.trust_env = False

    def get(resource, auth, params):
        stage = "token inspection" if resource == "debug_token" else "phone-number list" if resource.endswith("/phone_numbers") else "WABA lookup"
        response = session.get('https://graph.facebook.com/' + version + '/' + resource,
            headers={'Authorization': 'Bearer ' + auth}, params=params,
            timeout=(5, 25), allow_redirects=False)
        if response.status_code != 200:
            try:
                error = response.json().get('error', {})
            except (ValueError, AttributeError):
                error = {}
            codes = {k: error[k] for k in ('code', 'error_subcode') if isinstance(error, dict) and type(error.get(k)) is int}
            detail = safe_meta_error(error, [token, secret, auth, verify_token, *params.values()])
            raise CheckError('Meta rejected %s (HTTP %s; codes %s). Sanitized reason: %s' % (stage, response.status_code, json.dumps(codes), detail))
        return response.json()

    # Meta requires input_token in this API request. HTTPS only, logging disabled,
    # no environment proxies, no URL/error-body output and no redirects.
    audit = inspect_token(get('debug_token', app_id + '|' + secret, {'input_token': token})['data'], app_id, int(time.time()))
    print('PASS: token is valid, belongs to the selected app, and has both WhatsApp permissions.')
    for key, value in audit.items():
        print(key + ': ' + (datetime.fromtimestamp(value, timezone.utc).isoformat() if value else 'No fixed expiration reported; revocation remains possible.'))
    proof = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
    # Generic account metadata is optional and is rejected for some Meta account types.
    # Prove access and containment using the authenticated account phone_numbers edge.
    after = None
    found = None
    for _ in range(20):
        params = {'fields': 'id,display_phone_number,verified_name', 'limit': 100, 'appsecret_proof': proof}
        if after: params['after'] = after
        page = get(waba + '/phone_numbers', token, params)
        found = next((row for row in page.get('data', []) if phone_matches(row, phone, number)), None)
        if found or not page.get('paging', {}).get('next'): break
        after = page.get('paging', {}).get('cursors', {}).get('after')
        if not isinstance(after, str) or not after: break
    if not found:
        raise CheckError('Selected phone ID and business number were not found under this WABA.')
    print('PASS: selected Phone Number ID belongs to selected WABA and matches your entered business number.')
    print('Verified phone name: ' + ascii(str(found.get('verified_name', '')))[:160])
    print('Registered business number matched (value hidden).')
    if input('Confirm these are your registered business assets, not Meta test assets (type CONFIRM): ').strip() != 'CONFIRM':
        raise CheckError('Not confirmed; no credentials saved.')
    if path.read_bytes() != original:
        raise CheckError('Configuration changed during verification; no credentials saved. Run again.')
    # Deliberately NOT il_whatsapp_token: that key would activate existing dispatch.
    credentials = dict(access_token=token, app_id=app_id,
        graph_version=version, waba_id=waba, phone_id=phone, checked_at=int(time.time()), **audit)
    config = staged_config(config, credentials, secret if args.new_account else None, verify_token)
    backup_dir = bench / 'local-private/whatsapp-config-backups'
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(backup_dir, 0o700)
    backup = backup_dir / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as output:
        output.write(original)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.whatsapp-staged-')
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as output:
            json.dump(config, output, indent=2); output.flush(); os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    print('PASS: verified token staged privately in sandbox backend configuration.')
    if args.new_account:
        print('PASS: new webhook app/account configuration saved; previous config backed up privately.')
    print('Outbound token/templates were not enabled or changed. No messages sent.')


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        raise SystemExit('Cancelled; no token printed.') from None
    except CheckError as exc:
        raise SystemExit(str(exc)) from None
    except Exception:
        raise SystemExit('Read-only verification failed; no credentials or response details printed. Nothing enabled.') from None
