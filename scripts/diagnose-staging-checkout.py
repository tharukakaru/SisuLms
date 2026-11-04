"""Inspect only the named sandbox invoice; never retry or reset a payment."""
import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit
import requests

BENCH = Path('/home/sisu/frappe-bench')


def main():
    os.chdir(BENCH / 'sites')
    import frappe
    from institute_lms.cybersource_contract import unb64
    from institute_lms.cybersource_transport import request
    frappe.init(site='staging.sisuacademylk.com', sites_path=str(BENCH / 'sites'))
    frappe.connect()
    try:
        rows = frappe.get_all('IL CyberSource Attempt', filters={'invoice': 'fm34oisjhc', 'kind': 'subscription'},
            fields=['name', 'status', 'browser_event', 'session_expires', 'transaction_id'],
            order_by='creation desc', limit_page_length=5)
        print(json.dumps({'attempts': rows}, default=str))
        for row in rows[:1]:
            doc = frappe.get_doc('IL CyberSource Attempt', row.name)
            print(json.dumps({'expired': float(doc.session_expires or 0) <= time.time(),
                              'invoice_currency': doc.currency, 'amount_minor': doc.amount_minor}))
            token = doc.get_password('session_token', raise_exception=False)
            if token:
                claims = json.loads(unb64(token.split('.')[1]))
                # Only permit known display metadata; never output the JWT or full claims.
                contexts = claims.get('ctx') or []
                if isinstance(contexts, list):
                    for context in contexts:
                        data = context.get('data', {}) if isinstance(context, dict) else {}
                        library = data.get('clientLibrary')
                        if isinstance(library, str):
                            url = urlsplit(library)
                            if url.scheme == 'https' and url.hostname and url.hostname.endswith('.cybersource.com'):
                                print(json.dumps({'session_library': url.scheme + '://' + url.netloc + url.path,
                                                  'integrity_present': bool(data.get('clientLibraryIntegrity'))}))
            config = dict(frappe.conf.il_cybersource['merchants'][doc.merchant_scope], mode='sandbox')
            try:
                report = request(config, 'POST', '/tss/v2/searches', {'save': False,
                    'query': 'clientReferenceInformation.code:' + doc.reference,
                    'offset': 0, 'limit': 10, 'sort': 'submitTimeUtc:desc'})
                print(json.dumps({'report_lookup': 'PASS', 'matching_transaction_count':
                    len(report.get('_embedded', {}).get('transactionSummaries', []))}))
            except Exception as exc:
                print(json.dumps({'report_lookup': 'UNCONFIRMED', 'exception': type(exc).__name__}))
        url = 'https://apitest.cybersource.com/uc/v1/assets/1.0.0/UnifiedCheckout.js'
        with requests.Session() as client:
            client.trust_env = False
            with client.get(url, timeout=(5, 20), allow_redirects=False, stream=True) as response:
                print(json.dumps({'configured_library_http_status': response.status_code,
                                  'content_type': response.headers.get('Content-Type', '')[:100]}))
        print('READ ONLY: no attempt reset, new session, payment, invoice change or credentials displayed.')
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        raise SystemExit('STOPPED: ' + type(exc).__name__ + '; raw details withheld.') from None
