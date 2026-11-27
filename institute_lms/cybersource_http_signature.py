"""CyberSource HTTP-signature request headers for a merchant shared-secret key.

No network I/O, logging, local persistence or gateway environment guessing.
NOTE: Check current CyberSource acceptance of HTTP signatures before production.
"""
import base64
import hashlib
import hmac
import re
from email.utils import formatdate


def headers(method, path, body, host, merchant_id, key_id, shared_secret, date=None):
    if method not in ('GET', 'POST') or not re.fullmatch(r'/[a-zA-Z0-9/_-]+', path):
        raise ValueError('Unsupported HTTP request for signing')
    if host not in ('apitest.cybersource.com', 'api.cybersource.com'):
        raise ValueError('Untrusted CyberSource host')
    if not all(isinstance(x, str) and x and not re.search(r'[\r\n"]', x)
               for x in (merchant_id, key_id, shared_secret)):
        raise ValueError('Missing or unsafe merchant authentication configuration')
    date = date or formatdate(usegmt=True)
    if not isinstance(date, str) or '\n' in date or '\r' in date:
        raise ValueError('Invalid request date')
    if not isinstance(body, bytes) or (method == 'GET' and body):
        raise ValueError('Unexpected request body')
    fields = [('host', host), ('date', date), ('(request-target)', method.lower() + ' ' + path)]
    if method == 'POST':
        digest = 'SHA-256=' + base64.b64encode(hashlib.sha256(body).digest()).decode('ascii')
        fields.append(('digest', digest))
    fields.append(('v-c-merchant-id', merchant_id))
    signing_string = '\n'.join(k + ': ' + v for k, v in fields).encode('utf-8')
    try:
        decoded = base64.b64decode(shared_secret, validate=True)
    except (ValueError, base64.binascii.Error):
        raise ValueError('Invalid base64 merchant shared secret') from None
    if len(decoded) < 16:
        raise ValueError('Invalid merchant shared secret')
    signature = base64.b64encode(hmac.new(decoded, signing_string, hashlib.sha256).digest()).decode('ascii')
    names = ' '.join(k for k, _ in fields)
    result = {'Host': host, 'Date': date, 'v-c-merchant-id': merchant_id,
              'Content-Type': 'application/json',
              'Signature': f'keyid="{key_id}", algorithm="HmacSHA256", headers="{names}", signature="{signature}"'}
    if method == 'POST':
        result['Digest'] = digest
    return result
