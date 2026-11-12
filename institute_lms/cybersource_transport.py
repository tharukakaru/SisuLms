"""Fixed-host CyberSource REST transport. No redirects or credential logging."""
import json
import re
from pathlib import Path
import requests
from .cybersource_contract import host_for, request_jwt, verify_session


class ProviderUnavailable(Exception):
    pass


def request(config, method, path, data=None, token=False):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    if not (method == 'POST' and path in ('/uc/v1/sessions', '/tss/v2/searches')
            or method == 'GET' and re.fullmatch(r'/tss/v2/transactions/[0-9]{10,40}', path)):
        raise ValueError('Unsupported CyberSource request')
    host = host_for(config.get('mode'))
    body = json.dumps(data, separators=(',', ':'), ensure_ascii=True).encode() if data is not None else b''
    try:
        if config.get('shared_secret'):
            # HNB-issued merchant/key ID/shared secret credentials. Never mix with P12.
            from .cybersource_http_signature import headers as signed_headers
            if config.get('p12_path') or config.get('p12_password'):
                raise ValueError('Select exactly one CyberSource authentication type')
            auth_headers = signed_headers(method, path, body, host,
                config['merchant_id'], config['key_id'], config['shared_secret'])
        else:
            key, cert, _ = load_key_and_certificates(Path(config['p12_path']).read_bytes(),
                                                    config['p12_password'].encode())
            if not isinstance(key, RSAPrivateKey) or cert is None:
                raise ValueError('RSA certificate required')
            auth = request_jwt(method, path, body, config['merchant_id'], config['key_id'], key, host=host)
            auth_headers = {'Authorization': 'Bearer ' + auth, 'Content-Type': 'application/json',
                            'v-c-merchant-id': config['merchant_id']}
        with requests.Session() as session:
            session.trust_env = False
            response = session.request(method, 'https://' + host + path, data=body or None,
                headers=auth_headers, timeout=(5, 25), allow_redirects=False)
            if not 200 <= response.status_code < 300 or len(response.content) > 512000:
                raise ProviderUnavailable('CyberSource request could not be confirmed')
            if token:
                value = response.text.strip()
                if value.startswith('"'): value = json.loads(value)
                claims = verify_session(value, lambda kid: public_key(kid, host=host))
                return value, claims
            result = response.json()
            if not isinstance(result, dict): raise ValueError('Invalid response')
            return result
    except (requests.RequestException, OSError, ValueError, KeyError, TypeError, InvalidSignature):
        raise ProviderUnavailable('CyberSource unavailable; keep the payment pending and reconcile') from None


def public_key(kid, host=None):
    if host is None:
        host = host_for('sandbox')
    if host not in (host_for('sandbox'), host_for('live')):
        raise ValueError('Unsupported CyberSource API host')
    if not re.fullmatch(r'[\w-]{1,100}', kid): raise ValueError('Invalid signing key')
    with requests.Session() as session:
        session.trust_env = False
        response = session.get('https://' + host + '/flex/v2/public-keys/' + kid,
                               timeout=(5, 15), allow_redirects=False)
        if response.status_code != 200 or len(response.content) > 16000:
            raise ValueError('Public key unavailable')
        return response.json()
