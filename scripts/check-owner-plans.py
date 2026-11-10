"""Rollback owner publication; verify shared reads without sending anything."""
import os,json,copy,secrets,traceback
from types import SimpleNamespace
from unittest.mock import patch
SOURCE='platform.sisuacademylk.com'
def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    from institute_lms import plan_catalog,account_billing,saas
    baseline=None
    for site in (SOURCE,'sisuacademylk.com','teen.sisuacademylk.com'):
        frappe.init(site=site);frappe.connect()
        try:
            frappe.set_user('Guest');frappe.local.request=SimpleNamespace(path='/api/method/institute_lms.plan_catalog.public_catalog');frappe.local.form_dict=frappe._dict()
            account_billing.guard_request();saas.guard_request()
            value=plan_catalog.public_catalog()
            if baseline is None:baseline=value
            assert value==baseline,'Site catalogue differs'
            assert set(value)=={'revision','currency','plans'}
            print('PASS: guest-safe shared catalogue on '+site)
        finally:frappe.db.rollback();frappe.destroy()
    frappe.init(site=SOURCE);frappe.connect()
    try:
        frappe.set_user('sisu.student.test+platform.owner@gmail.com');frappe.session.data.csrf_token=secrets.token_hex(32)
        before=plan_catalog.admin_get();edited=copy.deepcopy(before['plans']);old_features=edited['Individual']['features'].copy()
        edited['Individual']['card_features']=['Rollback test benefit'];edited['Individual']['monthly_lkr']+=1
        result=plan_catalog.publish(edited,before['revision'],'Rollback acceptance of shared provider catalogue')
        assert result['revision']==before['revision']+1
        assert plan_catalog.public_catalog()['plans']['Individual']['card_features']==['Rollback test benefit']
        assert plan_catalog.plan_features('Individual')['news']==old_features['news']
        assert plan_catalog.plan('Individual')['monthly_lkr']==edited['Individual']['monthly_lkr']
        try:plan_catalog.publish(edited,before['revision'],'Reject stale catalogue editor transaction')
        except frappe.ValidationError:pass
        else:raise AssertionError('Stale revision accepted')
        print('PASS: publication, card text/access separation, new price lookup and stale revision rejection.')
        frappe.set_user('Guest')
        try:plan_catalog.publish(edited,result['revision'],'Unauthorized catalogue update attempt')
        except frappe.PermissionError:pass
        else:raise AssertionError('Guest publication allowed')
        print('PASS: unauthorized publication denied.')
    finally:
        frappe.db.rollback();frappe.destroy()
        print('ROLLED BACK: no plan, audit, invoice, subscription, payment or message changes retained. Browser acceptance remains separate.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'exception':type(exc).__name__,'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
        raise SystemExit(1) from None
