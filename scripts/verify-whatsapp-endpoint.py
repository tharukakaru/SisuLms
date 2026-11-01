"""Probe webhook without printing URL queries, credentials, or response bodies."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit
import requests

PATH = '/api/method/institute_lms.notification_service.whatsapp_webhook'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', default='http://127.0.0.1:8102')
    args = parser.parse_args()
    url = urlsplit(args.origin)
    if url.path or url.query or url.fragment or url.username or url.password:
        raise SystemExit('Use an origin only, without a path or query.')
    if args.origin != 'http://127.0.0.1:8102' and (url.scheme != 'https' or not url.hostname or not url.hostname.endswith('.trycloudflare.com')):
        raise SystemExit('Only local gateway or HTTPS trycloudflare sandbox origins are allowed.')
    config = json.loads((Path.home() / 'sisu-hnb-sandbox-bench/sites/hnb-checkout.localhost/site_config.json').read_text())
    token = config.get('il_whatsapp_verify_token')
    secret = config.get('il_whatsapp_app_secret')
    if not token or not secret:
        raise SystemExit('Webhook configuration missing.')
    session = requests.Session(); session.trust_env = False
    challenge = secrets.token_hex(12)

    def check(label, method, path, expected, body=None, **kwargs):
        try:
            response = session.request(method, args.origin + path, timeout=(5, 25), allow_redirects=False, **kwargs)
            ok = response.status_code == expected and (body is None or response.content == body)
        except requests.RequestException:
            ok = False
        print(('PASS: ' if ok else 'FAIL: ') + label)
        if not ok:
            raise SystemExit('Verification stopped. No credentials or response contents printed.')

    query = {'hub.mode': 'subscribe', 'hub.verify_token': token, 'hub.challenge': challenge}
    check('GET exact challenge', 'GET', PATH, 200, challenge.encode(), params=query)
    query['hub.verify_token'] = 'deliberately-invalid'
    check('GET wrong token rejected', 'GET', PATH, 403, params=query)
    raw = b'{"object":"whatsapp_business_account","entry":[]}'
    headers = {'Content-Type': 'application/json', 'X-Hub-Signature-256': 'sha256=invalid'}
    check('POST bad signature rejected', 'POST', PATH, 403, data=raw, headers=headers)
    headers['X-Hub-Signature-256'] = 'sha256=' + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    check('POST signed empty event reaches backend', 'POST', PATH, 200, b'EVENT_RECEIVED', data=raw, headers=headers)
    check('POST altered body rejected', 'POST', PATH, 403, data=raw+b' ', headers=headers)
    for path in ('/', '/login', '/campus', '/api/method/frappe.auth.get_logged_user'):
        check('Non-webhook route blocked: ' + path, 'GET', path, 404)
    check('Dispatch override blocked', 'POST', PATH+'?cmd=login', 400, data=raw, headers=headers)
    print('HTTP probes passed. This is NOT Meta subscription or real-message end-to-end verification.')


if __name__ == '__main__':
    main()
