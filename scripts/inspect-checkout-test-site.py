"""Read-only staging readiness check. Never prints credentials or customer records."""
import json
import os
import logging
import traceback
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
SITE = 'staging.sisuacademylk.com'
STAGE = 'startup'


def main():
    global STAGE
    logging.disable(logging.CRITICAL)
    STAGE = 'sites_directory'
    os.chdir(BENCH / 'sites')
    STAGE = 'import_frappe'
    import frappe
    STAGE = 'initialize_site'
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    connected = False
    try:
        STAGE = 'database_connect'
        frappe.connect()
        connected = True
        STAGE = 'configuration_summary'
        config = frappe.conf
        gateway = config.get('il_cybersource') or {}
        merchant = (gateway.get('merchants') or {}).get('platform') or {}
        print(json.dumps({
            'site': SITE,
            'expected_https_origin': config.get('host_name', '').rstrip('/') == 'https://' + SITE,
            'maintenance': bool(config.get('maintenance_mode')),
            'payments_paused': bool(config.get('il_payments_paused')),
            'gateway_enabled': bool(gateway.get('enabled')),
            'gateway_sandbox_mode': gateway.get('mode') == 'sandbox',
            'expected_merchant_configured': merchant.get('merchant_id') == 'sisu_academy_1793191054',
            'key_id_present': bool(merchant.get('key_id')),
            'certificate_file_present': bool(merchant.get('p12_path')) and Path(merchant['p12_path']).is_file(),
            'certificate_password_present': bool(merchant.get('p12_password')),
            'site_encryption_key_present': bool(config.get('encryption_key')),
        }))
        for doctype in ('IL CyberSource Attempt', 'IL Institute', 'IL Account Invoice',
                        'IL Provider Invoice', 'IL Invoice'):
            STAGE = 'schema_check:' + doctype
            exists = bool(frappe.db.exists('DocType', doctype))
            print(json.dumps({'doctype': doctype, 'schema_present': exists,
                              'record_count': frappe.db.count(doctype) if exists else None}))
        STAGE = 'source_check'
        app = BENCH / 'apps/institute_lms'
        print(json.dumps({'payment_backend_present': (app / 'institute_lms/cybersource.py').is_file(),
                          'checkout_component_present': (app / 'frontend/src/native/CyberSourcePayment.vue').is_file()}))
        print('READ ONLY: no credentials printed, provider requests, configuration changes or payments.')
        print('Record counts do not establish that existing staging data is disposable test data.')
    finally:
        # Cleanup must not hide the original initialization/connection failure.
        if connected:
            try:
                frappe.db.rollback()
            except Exception:
                print('NOTE: cleanup rollback failed; no writes were requested.')
        try:
            frappe.destroy()
        except Exception:
            print('NOTE: Frappe cleanup failed; original diagnostic preserved.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'failed_stage': STAGE, 'exception_type': type(exc).__name__,
                          'frames': [{'file': Path(f.filename).name, 'function': f.name,
                                      'line': f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-6:]]}))
        raise SystemExit('STOPPED: ' + type(exc).__name__ + '; raw details withheld.') from None
