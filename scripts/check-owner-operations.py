"""Production acceptance: owner reads and rollback-only setup state checks. No mail/payment sent."""
import os,secrets,json,traceback,hashlib,tarfile
from unittest.mock import patch

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='platform.sisuacademylk.com');frappe.connect()
    try:
        from institute_lms import owner_operations,owner_access,release,platform,site_policies,plan_catalog,commerce_events
        frappe.set_user('sisu.student.test+platform.owner@gmail.com');frappe.session.data.csrf_token=secrets.token_hex(32)
        from pathlib import Path
        app=Path('/home/sisu/frappe-bench/apps/institute_lms')
        with tarfile.open('/tmp/sisu-owner-operations.tgz') as archive:
            manifest=json.load(archive.extractfile('manifest.json'))
        for name,value in manifest.items():
            assert hashlib.sha256((app/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==value['after'],name
        print('PASS: deployed sources match the owner release.')
        room=release.control_room();assert 'jobs' in room
        for job in room['jobs']:assert 'organization_title' in job and 'site_hostname' in job
        plans=plan_catalog.admin_get();assert plans
        policy=site_policies.listing();assert 'sites' in policy
        access=owner_access.access_list();assert access['can_manage'] is False
        commerce_events.listing();owner_operations.audit()
        ready=owner_operations.readiness();assert 'mail' in ready and 'reporting_sites' in ready
        print('PASS: owner organizations, plans, site policies, commerce, audit, access and local readiness load.')
        assert owner_operations.sources(),'Reporting configuration missing'
        for site in owner_operations.sources():
            report=owner_operations.billing(site=site)
            assert report['configured'] and len(report['rows'])<=50
            assert all(s['plan']!='Student' for s in report['subscriptions'])
            assert not {'db_password','signature','payload'} & set(report)
        print('PASS: configured campus subscription/invoice reports are read-only and exclude student subscriptions.')
        try:owner_operations.billing(site='unconfigured.example.test')
        except frappe.PermissionError:pass
        else:raise AssertionError('Unconfigured site accepted')
        name=frappe.db.get_value('IL Organization',{'site_hostname':'test.sisuacademylk.com'},'name')
        if name:
            job=frappe.db.get_value('IL Provisioning Job',{'organization':name},'name')
            if job:
                platform.provisioning_result(job,'running','Rollback test of operator progress note')
                try:platform.provisioning_result(job,'ready','Rollback test of verified setup guard')
                except frappe.ValidationError:pass
                else:raise AssertionError('Ready accepted without operator confirmation')
                with patch('institute_lms.provision_verification.require_verified') as verification:
                    platform.provisioning_result(job,'ready','Rollback test: simulated operator verification',verified=True)
                    verification.assert_called_once()
                assert frappe.db.get_value('IL Provisioning Job',job,'status')=='ready'
                print('PASS: setup progress, explicit confirmation and server verification hook (simulated). No website was created or contacted.')
        frappe.set_user('Guest')
        for fn in (owner_operations.billing,owner_operations.readiness,owner_operations.audit,release.control_room,owner_access.access_list,site_policies.listing):
            try:fn()
            except frappe.PermissionError:pass
            else:raise AssertionError('Guest owner access allowed')
        print('PASS: guest access denied; delegated owner cannot administer other owners.')
    finally:
        frappe.db.rollback();frappe.destroy()
        print('ROLLED BACK: no setup status, audit, account, invoice or payment changes retained. No mail or policy delivery sent. Browser and external-service acceptance remain separate.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'exception':type(exc).__name__,'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
        raise SystemExit(1) from None
