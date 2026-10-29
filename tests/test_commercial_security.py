"""Commercial service boundaries with mocked persistence, not a bench integration test."""
import importlib.util
import json
import sys
import time
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from institute_lms.saas_rules import sign

ROOT=Path(__file__).resolve().parents[1]/'institute_lms'
NOW=datetime(2026,10,16,12)
class R(dict):
    def __getattr__(self,k):return self.get(k)
    def __setattr__(self,k,v):self[k]=v

class Boundaries(unittest.TestCase):
    def setUp(self):
        f=types.ModuleType('frappe');self.f=f
        f.whitelist=lambda **kw:lambda fn:fn
        f.throw=lambda msg,kind=ValueError:(_ for _ in ()).throw(kind(msg))
        f.PermissionError=PermissionError;f.session=R(user='student@example.invalid')
        f.conf=R();f.local=R(site='tenant.example.invalid',request=R(path='/api/method/x'))
        f.get_doc=MagicMock();f.get_all=MagicMock(return_value=[]);f.db=MagicMock();f.db.exists.return_value=False
        f.set_user=lambda user:setattr(f.session,'user',user)
        u=types.ModuleType('frappe.utils');u.now_datetime=lambda:NOW;u.get_datetime=lambda v:datetime.fromisoformat(str(v));u.getdate=lambda v:datetime.fromisoformat(str(v)).date()
        modules=patch.dict(sys.modules,{'frappe':f,'frappe.utils':u});modules.start();self.addCleanup(modules.stop)
        self.api=self.fake('api',scoped=MagicMock(),identity=lambda:(R(name='I'),R(name='S',user=f.session.user,role='Student')))
        self.fake('registration',require_owner=lambda:f.throw('Owner required',PermissionError))
        self.fake('saas',audit=MagicMock())
        self.c=self.load('commercial');self.c.save=MagicMock(side_effect=lambda d:d)
    def fake(self,name,**values):
        m=types.ModuleType('institute_lms.'+name);m.__dict__.update(values);sys.modules[m.__name__]=m;return m
    def load(self,name):
        spec=importlib.util.spec_from_file_location('institute_lms.'+name,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
    def test_student_cannot_verify_provider_invoice(self):
        with self.assertRaises(PermissionError):self.c.approve_invoice('bill','bank',100,'note')
        self.f.get_doc.assert_not_called()
    def test_student_cannot_assign_package(self):
        self.api.institute=lambda:R(name='I')
        with self.assertRaises(PermissionError):self.c.configure('Institute','Gold','x@example.invalid',reason='test')
    def test_individual_subscription_does_not_meter_enrolment_count(self):
        self.c.account_for=lambda *a:R(name='A')
        self.c.locked=lambda *a:R(name='A',plan='Individual')
        self.c.locked_reason=lambda a:None
        self.f.get_doc.return_value=R(institute='I',owner_type='Teacher',owner_user='T')
        def rows(dt,**kw):return ['C1','C2'] if dt=='IL Classroom' else ['S'+str(i) for i in range(30)]
        self.f.get_all.side_effect=rows
        doc=R(active=1,classroom='C1',student='NEW',get_doc_before_save=lambda:None)
        self.c.enforce_enrollment_limit(doc)
        doc.student='S0';self.c.enforce_enrollment_limit(doc)
        self.f.get_all.assert_not_called()
    def test_unlimited_package_allows_admission_but_suspension_does_not(self):
        self.c.account_for=lambda *a:R(name='A')
        self.c.locked=lambda *a:R(name='A',plan='Silver')
        self.c.locked_reason=lambda a:None
        self.f.get_doc.return_value=R(institute='I',owner_type='Institute')
        doc=R(active=1,classroom='C',student='S',get_doc_before_save=lambda:None)
        self.c.enforce_enrollment_limit(doc)
        self.f.get_all.assert_not_called()
        self.c.locked_reason=lambda a:'Workspace suspended'
        with self.assertRaises(PermissionError):self.c.enforce_enrollment_limit(doc)
    def test_invoice_submission_rejects_other_student(self):
        self.c.locked=lambda *a:R(institute='I',student='OTHER')
        with self.assertRaises(PermissionError):self.c.submit_slip('bill','file','ref','8000','2026-10-16')
        self.c.save.assert_not_called()
    def test_student_cannot_review_slip(self):
        self.api.classroom_for=lambda *a:(R(name='I'),R(role='Student'),R())
        self.c.locked=lambda *a:R(classroom='C',institute='I')
        with self.assertRaises(PermissionError):self.c.review_slip('slip','Approved','received')
        self.c.save.assert_not_called()
    def test_locked_provider_cannot_review(self):
        permission=MagicMock()
        self.fake('teaching',require=permission)
        self.api.classroom_for=lambda *a:(R(name='I'),R(role='Teacher'),R())
        self.c.account_for=lambda *a:R(name='A');self.c.locked_reason=lambda a:'Invoice overdue'
        self.c.locked=lambda *a:R(classroom='C',institute='I')
        with self.assertRaises(PermissionError):self.c.review_slip('slip','Approved','received')
        self.assertEqual(permission.call_args.args[2],'fees')
        self.c.save.assert_not_called()
    def test_repeated_slip_review_cannot_settle_again(self):
        self.c.reviewer=lambda s:(None,None,R())
        self.c.locked=lambda *a:R(status='Approved')
        with self.assertRaises(ValueError):self.c.review_slip('slip','Approved','received')
        self.c.save.assert_not_called()
    def test_duplicate_bank_reference_rejected(self):
        slip=R(status='Pending',invoice='B',provider_account='A',reference='REF')
        self.c.locked=lambda dt,n:slip if dt=='IL Bank Slip' else R(status='Unpaid')
        self.c.reviewer=lambda s:(None,None,R(paid_access_kind='Month'))
        self.f.db.exists.return_value=True
        with self.assertRaisesRegex(ValueError,'reference'):self.c.review_slip('slip','Approved','bank checked')
        self.c.save.assert_not_called()
    def test_provider_proof_must_be_private_and_attached_to_invoice(self):
        self.c.invoice_detail=lambda n:{'payment_proof':'F'}
        self.f.get_doc.return_value=R(is_private=1,attached_to_doctype='IL Provider Invoice',attached_to_name='OTHER')
        with self.assertRaises(PermissionError):self.c.provider_proof_data('B')
    def test_teacher_cannot_access_institute_billing(self):
        self.api.identity=lambda:(R(name='I'),R(role='Teacher',user='T'))
        with self.assertRaises(PermissionError):self.c.account_access(R(institute='I',owner_type='Institute'))
    def test_teacher_cannot_access_another_teacher_billing(self):
        self.api.identity=lambda:(R(name='I'),R(role='Teacher',user='T'))
        with self.assertRaises(PermissionError):self.c.account_access(R(institute='I',owner_type='Teacher',owner_user='OTHER'))
    def test_grant_uses_programme_identity_and_no_wallet(self):
        self.c.account_for=lambda *a:R(name='A')
        def get_doc(*args):return R(programme_enrollment='P') if isinstance(args[0],str) else R(args[0])
        self.f.get_doc.side_effect=get_doc
        self.c.grant(R(name='B',enrollment='E',student='S',amount=135000),R(name='C',institute='I',teacher='T',title='Business'),NOW,datetime(2027,4,16),'Bank transfer')
        row=self.c.save.call_args.args[0]
        self.assertEqual(row.product_key,'Programme:P');self.assertEqual(row.gross_minor,13500000)
        self.assertNotIn('payout_wallet',row)
    def test_hnb_cannot_start_without_documented_integration(self):
        with self.assertRaisesRegex(ValueError,'not configured'):self.c.hnb_checkout('B')
    def test_bridge_rejects_unknown_action(self):
        b=self.load('provider_bridge')
        with self.assertRaises(ValueError):b.checked('delete_site',{})
        with self.assertRaises(ValueError):b.checked('approve_invoice',{'extra':'x'})
    def bridge(self):
        b=self.load('provider_bridge');self.f.conf=R(il_control_plane_key='x'*40,il_tenant_id='T',il_owner_email='owner@example.invalid')
        self.f.cache=MagicMock();self.f.cache.get_value.return_value=None
        p=dict(tenant_id='T',site_hostname='tenant.example.invalid',actor='owner@example.invalid',issued_at=int(time.time()),nonce='a'*48,action='owner_invoices',args={})
        return b,p
    def test_bridge_rejects_wrong_signature(self):
        b,p=self.bridge()
        with self.assertRaises(PermissionError):b.receive(json.dumps(p),'wrong')
    def test_bridge_rejects_cross_site_and_stale_requests(self):
        b,p=self.bridge()
        for updates in ({'tenant_id':'OTHER'},{'site_hostname':'other.example.invalid'},{'actor':'stranger@example.invalid'},{'issued_at':0}):
            bad={**p,**updates}
            with self.assertRaises(PermissionError):b.receive(json.dumps(bad),sign(bad,'x'*40))
    def test_bridge_rejects_replay(self):
        b,p=self.bridge();self.f.cache.get_value.return_value=True
        with self.assertRaisesRegex(PermissionError,'replay'):b.receive(json.dumps(p),sign(p,'x'*40))

if __name__=='__main__':unittest.main()
