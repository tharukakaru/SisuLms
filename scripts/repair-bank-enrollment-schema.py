"""Add only the paid-access enrollment-key schema; never approve or unlock records."""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone

BENCH=Path('/home/sisu/frappe-bench')
SCHEMA=BENCH/'apps/institute_lms/institute_lms/institute_lms/doctype/il_paid_access/il_paid_access.json'
SITES=('staging.sisuacademylk.com','sisuacademylk.com')

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o077)
    root=Path.home()/'.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise RuntimeError('Private recovery directory required')
    recovery=root/('bank-schema-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    recovery.mkdir(mode=0o700)
    if SCHEMA.is_symlink():raise RuntimeError('Unexpected schema symlink')
    original=SCHEMA.read_bytes()
    data=json.loads(original)
    if data.get('name')!='IL Paid Access':raise RuntimeError('Unexpected schema')
    status=next(f for f in data['fields'] if f['fieldname']=='status')
    if status['fieldtype']!='Select':raise RuntimeError('Unexpected status type')
    options=status.get('options','').splitlines()
    if not {'Active','Revoked'}.issubset(options):raise RuntimeError('Unexpected access statuses')
    if 'Awaiting key' not in options:options.append('Awaiting key')
    status['options']='\n'.join(options)
    field=next((f for f in data['fields'] if f['fieldname']=='enrollment_key_hash'),None)
    if field and field['fieldtype']!='Data':raise RuntimeError('Unexpected key field type')
    if not field:
        data['fields'].append(dict(fieldname='enrollment_key_hash',label='Enrollment key hash',fieldtype='Data',hidden=1,read_only=1))
    if 'enrollment_key_hash' not in data['field_order']:data['field_order'].append('enrollment_key_hash')
    (recovery/'il_paid_access.before.json').write_bytes(original)
    for site in SITES:
        with (recovery/(site+'.backup.log')).open('w') as log:
            subprocess.run(['/usr/local/bin/bench','--site',site,'backup'],cwd=BENCH,stdout=log,stderr=log,check=True)
    SCHEMA.write_text(json.dumps(data,indent=2)+'\n')
    SCHEMA.chmod(0o644)
    import frappe
    os.chdir(BENCH/'sites')
    for site in SITES:
        frappe.init(site=site,sites_path=str(BENCH/'sites'))
        frappe.connect()
        try:
            frappe.set_user('Administrator')
            frappe.reload_doc('institute_lms','doctype','il_paid_access',force=True)
            frappe.clear_cache(doctype='IL Paid Access')
            meta=frappe.get_meta('IL Paid Access',cached=False)
            if 'Awaiting key' not in meta.get_field('status').options.splitlines():
                raise RuntimeError('Status schema verification failed')
            if not meta.has_field('enrollment_key_hash') or not frappe.db.has_column('IL Paid Access','enrollment_key_hash'):
                raise RuntimeError('Key column verification failed')
            frappe.db.commit()
            print('PASS: '+site+' accepts Awaiting key and has the enrollment-key hash column.')
        finally:
            frappe.destroy()
    print('READY: restart web and workers, then retry the existing pending slip approval.')
    print('No slips approved, invoices paid, access unlocked or notifications sent by this repair.')
    print('Recovery directory: '+str(recovery))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+type(exc).__name__+'. Schema repair may be partial; do not assume success. No automatic payment retry.')
        raise SystemExit(1) from None
