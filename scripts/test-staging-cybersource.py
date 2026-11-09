"""Verify saved staging credentials with one sandbox session; no payment or writes."""
import json
import os
import sys
import uuid
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
SITE = 'staging.sisuacademylk.com'


def main():
    if Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    path = BENCH / 'sites' / SITE / 'site_config.json'
    config = json.loads(path.read_text())
    gateway = config.get('il_cybersource') or {}
    merchant = (gateway.get('merchants') or {}).get('platform') or {}
    if gateway.get('enabled') or not config.get('il_payments_paused'):
        raise RuntimeError('Expected disabled checkout and retained payment pause')
    if (gateway.get('mode') != 'sandbox'
            or gateway.get('origin') != 'https://' + SITE
            or merchant.get('merchant_id') != 'sisu_academy_1793191054'
            or 'LKR' not in merchant.get('currencies', [])):
        raise RuntimeError('Unexpected sandbox configuration')
    sys.path.insert(0, str(BENCH / 'apps/institute_lms'))
    from institute_lms.cybersource_contract import session_request
    from institute_lms.cybersource_transport import request
    payload = session_request('sisu-' + uuid.uuid4().hex, 100, 'LKR',
                              gateway['origin'], merchant['methods'])
    print('CHECKING: staging server to Cybersource sandbox; one session, no payment.')
    request(dict(merchant, mode='sandbox'), 'POST', '/uc/v1/sessions', payload, token=True)
    print('PASS: server credentials accepted; session signature/expiry verified.')
    print('Requested methods: ' + ', '.join(merchant['methods']))
    print('NOT TESTED: browser/device wallet availability, 3DS or payment completion.')
    os.chdir(BENCH / 'sites')
    import frappe
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    connected = False
    try:
        frappe.connect()
        connected = True
        print(json.dumps({'lkr_provider_billing_enabled': bool(frappe.conf.get('il_usage_billing_enabled')),
                          'shared_campus': bool(frappe.conf.get('il_shared_campus_enabled')),
                          'active_teacher_memberships': frappe.db.count('IL Member', {'role': 'Teacher', 'active': 1}),
                          'active_admin_memberships': frappe.db.count('IL Member', {'role': 'Admin', 'active': 1})}))
        for email in ('tharukakarunarathne60@gmail.com', 'gro4celk@gmail.com'):
            exists = bool(frappe.db.exists('User', email))
            memberships = frappe.get_all('IL Member', filters={'user': email},
                fields=['role', 'active'], limit_page_length=20) if exists else []
            print(json.dumps({'site': SITE, 'email': email, 'exists': exists,
                'enabled': bool(exists and frappe.db.get_value('User', email, 'enabled')),
                'memberships': memberships,
                'active_provider_membership': any(m.role in ('Teacher', 'Admin') and m.active for m in memberships)}))
    finally:
        if connected:
            frappe.db.rollback()
        frappe.destroy()
    print('UNCHANGED: checkout disabled, payment pause retained; no invoices, messages or payments created.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        raise SystemExit('STOPPED: ' + type(exc).__name__ + '; no secrets displayed; no automatic retry.') from None
