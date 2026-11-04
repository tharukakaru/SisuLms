"""Quarantine unreferenced local proof artifacts from the rollback test only."""
import os
import re
from pathlib import Path
from datetime import datetime, timezone

def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    import frappe
    os.chdir('/home/sisu/frappe-bench/sites')
    frappe.init(site='sisuacademylk.com', sites_path='/home/sisu/frappe-bench/sites')
    frappe.connect()
    try:
        if frappe.conf.get('il_storage_backend', 'frappe') != 'frappe':
            raise RuntimeError('Only local proof storage supported')
        root = Path(frappe.get_site_path('private', 'files')).resolve()
        destination = Path('/home/sisu/.sisu-secrets') / ('proof-cleanup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        count = 0
        for path in root.glob('bank-proof*.txt'):
            if path.is_symlink() or not path.is_file() or path.resolve().parent != root or path.stat().st_size != 63:
                continue
            raw = path.read_bytes()
            if not re.fullmatch(rb'DEMO ONLY - no transfer made - [0-9a-f]{32}', raw):
                continue
            url = '/private/files/'+path.name
            if (frappe.db.exists('File', {'file_url': url})
                    or frappe.db.exists('IL Stored Object', {'storage_key': url})):
                print('RETAINED: referenced test proof')
                continue
            destination.mkdir(mode=0o700, parents=True, exist_ok=True)
            target = destination/path.name
            if target.exists():
                raise RuntimeError('Quarantine collision')
            path.rename(target)
            target.chmod(0o600)
            count += 1
        print('QUARANTINED: '+str(count)+' unreferenced rollback-test proofs; no permanent deletion.')
        if count:
            print('Recovery directory: '+str(destination))
        print('No database records, user uploads, payments or messages changed.')
    finally:
        frappe.db.rollback()
        frappe.destroy()

if __name__ == '__main__':
    main()
