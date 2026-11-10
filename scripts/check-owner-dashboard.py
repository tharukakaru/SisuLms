"""Read-only acceptance for the owner overview. No payment, invitation or scheduler mutation."""
import os,json,tarfile,hashlib
from pathlib import Path

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='platform.sisuacademylk.com');frappe.connect()
    try:
        from institute_lms import owner_operations,owner_access
        frappe.set_user('sisu.student.test+platform.owner@gmail.com')
        with tarfile.open('/tmp/sisu-owner-dashboard.tgz') as t:manifest=json.load(t.extractfile('manifest.json'))
        app=Path('/home/sisu/frappe-bench/apps/institute_lms')
        for name,entry in manifest.items():assert hashlib.sha256((app/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==entry['after'],name
        overview=owner_operations.overview()
        for campus in overview['campuses']:
            assert campus['available'],'Campus reporting unavailable: '+campus['site']
            assert 'student_memberships' in campus['counts']
        assert overview['campuses'],'No reporting sources configured'
        assert not owner_access.access_list()['can_manage']
        print('PASS: release hashes, live campus counts and delegated-owner invitation restriction.')
        frappe.set_user('Guest')
        try:owner_operations.overview()
        except frappe.PermissionError:pass
        else:raise AssertionError('Guest dashboard access allowed')
        print('PASS: guest dashboard access denied. No invitation, payment or account change.')
    finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('CHECK FAILED: '+(str(exc) if isinstance(exc,AssertionError) else type(exc).__name__))
        raise SystemExit(1) from None
