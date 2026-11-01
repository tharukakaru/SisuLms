"""CyberSource Sessions v1 contract. No Frappe, credentials or network side effects."""
import base64
import hashlib
import json
import re
import time
import uuid
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

HOST = 'apitest.cybersource.com'  # Deliberately no production endpoint in this release.
METHODS = {'PANENTRY', 'GOOGLEPAY', 'APPLEPAY', 'CLICKTOPAY'}


def minor(value):
    try:
        amount = Decimal(str(value)) * 100
        if not amount.is_finite() or amount <= 0 or amount != amount.to_integral_value():
            raise ValueError('Invalid payment amount')
        return int(amount)
    except InvalidOperation as exc:
        raise ValueError('Invalid payment amount') from exc


def origin(value):
    u = urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password or u.path or u.query or u.fragment:
        raise ValueError('Configure the exact HTTPS checkout origin without a trailing slash')
    return value


def session_request(reference, amount_minor, currency, checkout_origin, methods):
    if not re.fullmatch(r'sisu-[a-f0-9]{32}', reference):
        raise ValueError('Invalid attempt reference')
    if type(amount_minor) is not int or amount_minor <= 0 or currency not in ('LKR', 'USD'):
        raise ValueError('Unsupported invoice amount or currency')
    if not isinstance(methods, list) or not methods or not set(methods) <= METHODS:
        raise ValueError('Configure only activated payment methods')
    return {
        'targetOrigins': [origin(checkout_origin)], 'clientVersion': '1.0',
        'country': 'LK', 'locale': 'en_GB', 'allowedCardNetworks': ['VISA', 'MASTERCARD'],
        'allowedPaymentTypes': methods, 'buttonType': 'CHECKOUT',
        'captureMandate': {'billingType': 'FULL', 'requestEmail': True,
                           'requestShipping': False, 'requestSaveCredentials': False},
        'completeMandate': {'type': 'CAPTURE', 'consumerAuthentication': '3DS',
                            'tms': {'tokenCreate': False}},
        'data': {'clientReferenceInformation': {'code': reference},
                 'orderInformation': {'amountDetails': {
                     'totalAmount': f'{Decimal(amount_minor) / 100:.2f}', 'currency': currency}}},
    }


def b64url(data):
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def unb64(value):
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def request_jwt(method, path, body, merchant, key_id, private_key, now=None):
    """P12-key JWT v2 authentication, implemented directly (no provider SDK)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    now = int(time.time()) if now is None else now
    claims = {'iat': now, 'exp': now + 120, 'iss': merchant, 'jti': str(uuid.uuid4()),
              'request-host': HOST, 'request-method': method.lower(),
              'request-resource-path': path, 'v-c-jwt-version': '2', 'v-c-merchant-id': merchant}
    if body:
        claims.update(digest=base64.b64encode(hashlib.sha256(body).digest()).decode(),
                      digestAlgorithm='SHA-256')
    header = {'alg': 'RS256', 'typ': 'JWT', 'kid': key_id}
    encoded = '.'.join(b64url(json.dumps(v, separators=(',', ':')).encode()) for v in (header, claims))
    signature = private_key.sign(encoded.encode(), padding.PKCS1v15(), hashes.SHA256())
    return encoded + '.' + b64url(signature)


def verify_session(token, fetch_key, now=None):
    """Trust only RSA keys fetched from the fixed CyberSource sandbox origin."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    if not isinstance(token, str) or len(token) > 64000:
        raise ValueError('Invalid session response')
    h, p, s = token.split('.')
    header = json.loads(unb64(h))
    if header.get('alg') != 'RS256' or not re.fullmatch(r'[\w-]{1,100}', str(header.get('kid', ''))):
        raise ValueError('Invalid session signing key')
    jwk = fetch_key(header['kid'])
    if jwk.get('kty') != 'RSA' or jwk.get('kid', header['kid']) != header['kid']:
        raise ValueError('Invalid public key')
    key = rsa.RSAPublicNumbers(int.from_bytes(unb64(jwk['e']), 'big'),
                              int.from_bytes(unb64(jwk['n']), 'big')).public_key()
    key.verify(unb64(s), (h + '.' + p).encode(), padding.PKCS1v15(), hashes.SHA256())
    claims = json.loads(unb64(p))
    now = time.time() if now is None else now
    if not isinstance(claims.get('exp'), (int, float)) or claims['exp'] <= now:
        raise ValueError('Session expired')
    if claims.get('iat', now) > now + 30 or claims.get('nbf', now) > now + 30:
        raise ValueError('Session is not yet valid')
    return claims


def verify_transaction(data, attempt):
    """Input MUST be an authenticated Transaction Details response, never browser data.

    Require both authorization and capture acceptance. Authorization alone grants
    nothing. Unknown/partial/report-delayed responses remain pending.
    """
    if (data.get('merchantId') != attempt['merchant_id']
            or data.get('clientReferenceInformation', {}).get('code') != attempt['reference']):
        raise ValueError('Merchant or reference mismatch')
    amounts = data.get('orderInformation', {}).get('amountDetails', {})
    if amounts.get('currency') != attempt['currency'] or minor(amounts.get('totalAmount')) != attempt['amount_minor']:
        raise ValueError('Amount or currency mismatch')
    if not re.fullmatch(r'[0-9]{10,40}', str(data.get('id', ''))):
        raise ValueError('Invalid transaction ID')
    apps = data.get('applicationInformation', {}).get('applications', [])
    by_name = {a.get('name'): str(a.get('reasonCode')) for a in apps if isinstance(a, dict)}
    # Conflicting or reversal/refund records cannot be treated as a new payment.
    if len(by_name) != len(apps) or any(n in by_name for n in ('ics_credit', 'ics_auth_reversal', 'ics_auto_auth_reversal')):
        return 'review'
    if by_name.get('ics_auth') == '100' and by_name.get('ics_bill') == '100':
        return 'succeeded'
    if by_name.get('ics_auth') in ('200', '201', '202', '203', '204', '205', '207', '208', '210', '211', '231') and 'ics_bill' not in by_name:
        return 'failed'
    return 'pending'
