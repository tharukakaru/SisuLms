"""Real Frappe public-account persistence test; synthetic OTP proofs, always rollback."""
import importlib.util,json,logging,os,time,uuid
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from types import SimpleNamespace
stage='preflight'
def deny(*args,**kwargs):raise RuntimeError('Unexpected delivery during rollback test')
def deferred(*args,**kwargs):
    if kwargs.get('enqueue_after_commit') is True and not kwargs.get('now'):return None
    raise RuntimeError('Unexpected immediate job during rollback test')
def refresh(event=None,*args,**kwargs):
    if event in ('doc_update','list_update') and kwargs.get('after_commit') is True:return None
    raise RuntimeError('Unexpected realtime event during rollback test')
def main():
    global stage
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise RuntimeError('Run in local sandbox bench')
    logging.disable(logging.CRITICAL)
    import frappe,requests,smtplib
    source=Path(__file__).resolve().parents[1]/'institute_lms/public_signup.py'
    spec=importlib.util.spec_from_file_location('institute_lms.public_signup_test',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    os.chdir(bench/'sites');frappe.init(site='hnb-checkout.localhost',sites_path=str(bench/'sites'));frappe.connect()
    try:
        if frappe.conf.get('il_shared_campus_enabled') or frappe.conf.get('il_public_signup_enabled'):raise RuntimeError('Expected disabled public/shared modes')
        from institute_lms import portal_policy
        policy=portal_policy.public()
        if not policy['privacy_policy_url'] or not policy['privacy_policy_version']:raise RuntimeError('Sandbox privacy policy missing')
        original_user=frappe.session.user
        with ExitStack() as stack:
            commits=stack.enter_context(patch.object(frappe.db,'commit'))
            stack.enter_context(patch.object(frappe,'sendmail',deny))
            stack.enter_context(patch.object(frappe,'enqueue',deferred))
            stack.enter_context(patch.object(frappe,'publish_realtime',refresh))
            stack.enter_context(patch.object(requests.sessions.Session,'request',deny))
            stack.enter_context(patch.object(smtplib.SMTP,'sendmail',deny))
            stack.enter_context(patch.object(module,'ready',lambda:None))
            stack.enter_context(patch.object(module,'challenges',SimpleNamespace(key=lambda t:'sisu-public-rollback:'+t,store=lambda *a:None,google_identity=lambda _:False)))
            for kind in ('Student','Individual Teacher','Institute'):
                stage='creating rollback-only '+kind
                identifier=uuid.uuid4().hex
                email='rollback-'+identifier+'@example.invalid'
                data={'kind':kind,'email':email,'phone':'+94761234567','first_name':'Rollback','last_name':'Account',
                    'username':'test_'+identifier[:20],'country':'Sri Lanka','bio':'Rollback fixture','qualifications':'',
                    'privacy_policy_url':policy['privacy_policy_url'],'privacy_policy_version':policy['privacy_policy_version']}
                state={'flow':'public-account-v1','details':data,'expires':time.time()+600,'email_verified':True,'phone_verified':True}
                frappe.set_user('Guest')
                commits.reset_mock()
                try:
                    with patch.object(module,'read',lambda _:state):
                        password='Test-'+uuid.uuid4().hex
                        result=module.complete(identifier,password,password)
                    assert result['created'] and frappe.db.exists('User',email)
                    assert frappe.db.exists('IL Verified Phone',{'user':email})
                    assert frappe.db.exists('IL Public Profile',{'user':email,'kind':{'Individual Teacher':'Teacher'}.get(kind,kind)})
                    assert not frappe.db.exists('IL Member',{'user':email})
                    assert not frappe.db.exists('IL Account Subscription',{'user':email})
                    assert not frappe.db.exists('Has Role',{'parent':email,'role':['in',['System Manager','Institute Admin','Institute Teacher']]})
                    assert commits.call_count==1
                    print('PASS: '+kind+' identity saved through hooks; no membership, subscription or privileged role granted.')
                finally:frappe.db.rollback()
                assert not frappe.db.exists('User',email)
                assert not frappe.db.exists('IL Public Profile',{'user':email})
                assert not frappe.db.exists('IL Verified Phone',{'user':email})
                print('PASS: '+kind+' test records removed by rollback.')
            frappe.set_user(original_user)
        print('All test records rolled back. Public/shared mode remains OFF. No email or SMS sent.')
        print('Synthetic verified challenges only: actual OTP delivery, HTTP, Google callbacks and browser signup remain untested.')
    finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('BLOCKED at '+stage+' ['+type(e).__name__+']. No credentials displayed; no test changes committed.')
        raise SystemExit(1)
