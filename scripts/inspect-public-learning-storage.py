"""Read-only public/staging storage readiness; never prints service credentials."""
import json
import logging
import os
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH / 'sites')
    for site in ('sisuacademylk.com', 'staging.sisuacademylk.com'):
        try:
            frappe.init(site=site, sites_path=str(BENCH / 'sites'))
            frappe.connect()
            c = frappe.conf
            from institute_lms.account_storage import configured
            media = c.get('il_private_media_s3') or {}
            live = c.get('il_live_recording_s3') or {}
            limit = c.get('il_account_storage_bytes')
            print(json.dumps({'site': site,
                'shared_campus': bool(c.get('il_shared_campus_enabled')),
                'tenant_id_present': bool(c.get('il_tenant_id')),
                'tenant_subscription_present': bool(c.get('il_tenant_id') and frappe.db.exists('IL Subscription', {'tenant_id': c.get('il_tenant_id')})),
                'account_storage_configured': configured(),
                'legacy_usage_billing_flag': bool(c.get('il_usage_billing_enabled')),
                'storage_allocation_bytes': limit if type(limit) is int else None,
                'storage_allocation_type': type(limit).__name__,
                'local_file_backend': c.get('il_storage_backend', 'frappe') == 'frappe',
                'stored_file_bytes': int(frappe.db.sql('SELECT COALESCE(SUM(file_size),0) FROM `tabFile` WHERE is_folder=0')[0][0]),
                'private_video_fields': {k: bool(media.get(k)) for k in ('bucket', 'region', 'access_key', 'secret')},
                'expected_video_adapter': c.get('il_private_video_adapter') == 'institute_lms.private_media.grant',
                'video_hosts_present': bool(c.get('il_private_video_hosts')),
                'live_recording_fields': {k: bool(live.get(k)) for k in ('bucket', 'region', 'access_key', 'secret')},
                'demo_institute_present': bool(frappe.db.exists('IL Institute', {'code': 'SISUDEMO'}))}))
        finally:
            frappe.db.rollback()
            frappe.destroy()
    print('READ ONLY: no uploads, credentials shown, provider calls, configuration changes or messages.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: ' + type(exc).__name__ + '; no private configuration printed.')
        raise SystemExit(1) from None
