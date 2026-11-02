"""Exercise real owner mutations in one transaction; never commit or deliver messages."""
import os,logging,uuid,json
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
BENCH=Path('/home/sisu/frappe-bench')
STAGE='preflight'
def deny(*args,**kwargs):raise RuntimeError('Commit or external delivery attempted during rollback test')
def deferred(*args,**kwargs):
    if kwargs.get('enqueue_after_commit') is True and not kwargs.get('now'):return None
    deny()
def refresh(event=None,*args,**kwargs):
    if event in ('doc_update','list_update') and kwargs.get('after_commit') is True:return None
    deny()
def main():
    global STAGE
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    logging.disable(logging.CRITICAL)
    import frappe,requests,smtplib
    os.chdir(BENCH/'sites');frappe.init(site='platform.sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect()
    identifier=uuid.uuid4().hex
    email='owner-check-'+identifier+'@example.invalid'
    host=identifier+'.example.invalid'
    tenant=None
    try:
        frappe.set_user('gro4celk@gmail.com')
        from institute_lms import platform,plan_catalog
        platform.owner()
        if not frappe.conf.get('il_payments_paused'):raise RuntimeError('Payment pause required')
        with ExitStack() as stack:
            for target,name,replacement in [(frappe.db,'commit',deny),(frappe,'sendmail',deny),(frappe,'enqueue',deferred),(frappe,'publish_realtime',refresh),(requests.sessions.Session,'request',deny),(smtplib.SMTP,'sendmail',deny)]:stack.enter_context(patch.object(target,name,replacement))
            STAGE='invalid institute code validation'
            try:platform.register('Rollback Institute','1234',host,email)
            except frappe.ValidationError as exc:
                if 'starting with a letter' not in str(exc):raise RuntimeError('Unexpected validation message') from None
            else:raise RuntimeError('Invalid code accepted')
            print('PASS: numeric-only code produces the specific validation message.')
            STAGE='real institute registration hooks'
            code='T'+identifier[:10].upper()
            result=platform.register('Rollback Institute',code,host,email)
            tenant=result['tenant_id']
            assert frappe.db.exists('IL Organization',tenant)
            assert frappe.db.exists('User',email)
            assert frappe.db.exists('IL Subscription',{'tenant_id':tenant})
            assert frappe.db.exists('IL Provisioning Job',result['job'])
            repeat=platform.register('Rollback Institute',code,host,email)
            assert repeat['existing'] and repeat['tenant_id']==tenant
            print('PASS: real registration creates user, organization, subscription and job; retry reuses the record.')
            STAGE='organization suspension and restoration'
            platform.update_organization(tenant,False,'Rollback test suspension')
            assert not frappe.db.get_value('IL Organization',tenant,'enabled')
            platform.update_organization(tenant,True,'Rollback test restoration')
            assert frappe.db.get_value('IL Organization',tenant,'enabled')
            platform.override(tenant,{'features':{},'limits':{'students':10}},'Rollback policy test')
            platform.trial(tenant,5,'Rollback bounded trial')
            platform.provisioning_result(result['job'],'running','Rollback status test')
            assert frappe.db.get_value('IL Provisioning Job',result['job'],'status')=='running'
            print('PASS: suspend/restore, policy override, bounded trial and provisioning update persist inside the transaction.')
            STAGE='current provider catalogue publish'
            before=plan_catalog.current()
            assert set(before['plans'])=={'Individual','Silver','Gold','Platinum'}
            saved=plan_catalog.publish(before['plans'],before['revision'],'Rollback owner catalogue acceptance test')
            assert saved['revision']==before['revision']+1
            print('PASS: current four-package catalogue publishes through real validation hooks.')
            frappe.db.rollback()
            assert not frappe.db.exists('IL Organization',tenant)
            assert not frappe.db.exists('User',email)
            assert not frappe.db.exists('IL Subscription',{'tenant_id':tenant})
            assert not frappe.db.exists('IL Provisioning Job',result['job'])
            assert plan_catalog.current()['revision']==before['revision']
        print('PASS: all test records rolled back; original catalogue revision restored.')
        print('No email, SMS, payments, DNS changes, remote provisioning or policy delivery. HTTP/browser acceptance remains separate.')
    finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('BLOCKED at '+STAGE+': '+type(exc).__name__+'. No test changes committed; no raw logs or credentials displayed.')
        raise SystemExit(1) from None
