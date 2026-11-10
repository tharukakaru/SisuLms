"""Read-only status plus rollback-only policy retry validation. No delivery is dispatched."""
import os,secrets,traceback,json
from unittest.mock import patch

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='platform.sisuacademylk.com');frappe.connect()
    try:
        from institute_lms import site_policies
        frappe.set_user('sisu.student.test+platform.owner@gmail.com');frappe.session.data.csrf_token=secrets.token_hex(32)
        value=site_policies.listing();assert 'sites' in value
        for row in value['sites']:
            assert 'blockers' in row and 'can_retry' in row
            assert not {'signature','key','payload','features','price_minor'} & set(row)
        print('PASS: owner status lists hosting readiness and delivery confirmation without secrets or obsolete prices.')
        name=frappe.db.get_value('IL Organization',{'site_hostname':'test.sisuacademylk.com'},'name')
        assert name,'Named test organization not found'
        details=site_policies.organization_details(name);assert details['name']==name and details['subscription'] is not None
        # Only simulate connection readiness; never dispatch or alter a remote site.
        with patch.object(site_policies,'blockers',return_value=[]):
            result=site_policies.retry(name,'Rollback acceptance of hosted policy retry')
            assert result['queued']
            assert frappe.db.get_value('IL Policy Delivery',{'organization':name},'status')=='Pending'
            assert site_policies.retry(name,'Rollback duplicate retry check')['queued']
        print('PASS: manage-institute details; retry queues Pending with simulated readiness; duplicate retry is safe. No network delivery attempted.')
        frappe.set_user('Guest')
        for call in (lambda:site_policies.listing(),lambda:site_policies.organization_details(name),lambda:site_policies.retry(name,'Unauthorized retry check')):
            try:call()
            except frappe.PermissionError:pass
            else:raise AssertionError('Guest access was allowed')
        print('PASS: guest status, management and retry access denied.')
    finally:
        frappe.db.rollback();frappe.destroy()
        print('ROLLED BACK: no delivery, organization, subscription, audit or message changes retained. Actual remote delivery still requires configured hosting.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'exception':type(exc).__name__,'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
        raise SystemExit(1) from None
