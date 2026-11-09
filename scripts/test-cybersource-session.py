"""Create one sandbox checkout session; never submit card details or a payment."""
import argparse
import getpass
import json
import sys
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path

import requests
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from institute_lms.cybersource_contract import HOST, request_jwt, session_request, verify_session
from institute_lms.cybersource_transport import public_key


def hidden(prompt):
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        return getpass.getpass(prompt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate')
    args = parser.parse_args()
    key_id = hidden('REST-Certificate Key ID (hidden; not Merchant ID): ').strip()
    if not key_id or key_id == 'sisu_academy_1793191054':
        raise ValueError('Invalid key identifier')
    password = hidden('P12 password (hidden): ')
    key, cert, _ = load_key_and_certificates(Path(args.certificate).read_bytes(), password.encode())
    if not isinstance(key, RSAPrivateKey) or cert is None:
        raise ValueError('RSA certificate required')
    if not cert.not_valid_before_utc <= datetime.now(timezone.utc) < cert.not_valid_after_utc:
        raise ValueError('Certificate outside validity period')
    merchant = 'sisu_academy_1793191054'
    path = '/uc/v1/sessions'
    payload = session_request('sisu-' + uuid.uuid4().hex, 100, 'LKR',
                              'https://www.sisuacademylk.com', ['PANENTRY'])
    body = json.dumps(payload, separators=(',', ':'), ensure_ascii=True).encode()
    auth = request_jwt('POST', path, body, merchant, key_id, key)
    print('Testing sandbox Sessions API only. No checkout will be opened or payment submitted.')
    with requests.Session() as client:
        client.trust_env = False
        response = client.post('https://' + HOST + path, data=body,
            headers={'Authorization': 'Bearer ' + auth, 'Content-Type': 'application/json',
                     'v-c-merchant-id': merchant}, timeout=(5, 25), allow_redirects=False)
    print('Sandbox Sessions HTTP status:', response.status_code)
    if not 200 <= response.status_code < 300:
        print('STOPPED: session not created. Credentials, permissions or request contract need investigation.')
        print('Raw response withheld. No automatic retry.')
        return 1
    if len(response.content) > 512000:
        raise ValueError('Oversized response')
    token = response.text.strip()
    if token.startswith('"'):
        token = json.loads(token)
    verify_session(token, public_key)
    print('PASS: sandbox accepted session request; returned token signature and expiry verified.')
    print('NOT TESTED: browser checkout, 3DS, wallets, authorization, capture or settlement.')
    print('Session discarded. No credentials saved, site settings changed or payments submitted.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt) as exc:
        print('STOPPED: ' + type(exc).__name__ + '. No secrets or raw response displayed; no automatic retry.')
        sys.exit(1)
