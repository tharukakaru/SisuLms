import importlib
import sys
import types
import unittest
from datetime import datetime,timedelta
from unittest.mock import Mock,patch
class Row(dict):
    def __getattr__(self,k):return self.get(k)
    def __setattr__(self,k,v):self[k]=v
class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=types.ModuleType('frappe');u=types.ModuleType('frappe.utils')
        f.whitelist=lambda **kw:lambda fn:fn
        u.get_datetime=lambda x:x;u.now_datetime=datetime.now
        with patch.dict(sys.modules,{'frappe':f,'frappe.utils':u}):
            cls.service=importlib.import_module('institute_lms.usage_billing')
    def test_disabled_status_does_not_query_unmigrated_table(self):
        fake=Row(conf={});fake.get_all=Mock(side_effect=AssertionError('DB touched'))
        with patch.object(self.service,'frappe',fake):
            self.assertEqual(self.service.status()['invoices'],[])
    def test_overdue_blocks_without_scheduler(self):
        now=datetime(2026,12,1)
        fake=Row(conf={'il_usage_billing_enabled':1},get_all=lambda *a,**k:[Row(suspended=0,status='Unpaid',due_at=now)])
        with patch.object(self.service,'frappe',fake),patch.object(self.service,'now_datetime',lambda:now):
            self.assertTrue(self.service.blocked('tenant-sub'))
    def test_final_snapshot_is_not_recalculated_and_suspends(self):
        now=datetime(2026,12,20);doc=Row(issued_at=datetime(2026,12,1),status='Unpaid',due_at=datetime(2026,12,11),suspended=0)
        bill=Row(name='base',subscription='sub',period_end=datetime(2026,12,1))
        acc=Row(name='sub',role='Institute')
        fake=Row(conf={'il_usage_billing_enabled':1},get_all=lambda *a,**k:['base'],db=Row(get_value=lambda *a:'usage'))
        fake.get_doc=lambda dt,*a,**k: {'IL Account Invoice':bill,'IL Account Subscription':acc,'IL Usage Invoice':doc}[dt]
        with patch.object(self.service,'frappe',fake),patch.object(self.service,'now_datetime',lambda:now),patch.object(self.service,'quote',side_effect=AssertionError('Recalculated immutable bill')),patch.object(self.service,'save') as save:
            self.service.daily();self.assertEqual(doc.suspended,1);save.assert_called_once_with(doc)
    def test_provider_query_uses_institute_and_owner_scope(self):
        now=datetime(2026,12,1)
        fake=Row(get_all=Mock(return_value=[]))
        a=Row(name='teacher-sub',role='Teacher',institute='tenant1',user='teacher1',trial_until=now)
        bill=Row(period_start=now,period_end=now+timedelta(days=30),paid_at=now,plan='Gold')
        with patch.object(self.service,'frappe',fake):
            result=self.service.quote(a,bill)
            self.assertEqual(result['quantity'],0)
            self.assertEqual(fake.get_all.call_args.kwargs['filters'],{'institute':'tenant1','owner_type':'Teacher','owner_user':'teacher1'})

    def test_repeated_local_verification_does_not_rewrite_audit(self):
        doc=Row(name='usage-1',issued_at=datetime(2026,12,1),status='Paid',amount_lkr=100,payment_reference='bank:ref',suspended=0,reviewed_by='original-owner')
        fake=Row(conf={'il_usage_billing_enabled':1},get_doc=lambda *a,**k:doc,db=Row(exists=lambda *a:False))
        with patch.object(self.service,'frappe',fake),patch.object(self.service,'save') as save:
            result=self.service.settle_verified('usage-1','ref',100,'Evidence checked again')
            self.assertTrue(result['already_applied'])
            self.assertEqual(doc.reviewed_by,'original-owner')
            save.assert_not_called()

    def test_reference_allocated_to_subscription_cannot_pay_usage(self):
        doc=Row(name='usage-1',issued_at=datetime(2026,12,1),status='Unpaid',amount_lkr=100)
        def fail(message,*args):raise ValueError(message)
        fake=Row(conf={'il_usage_billing_enabled':1},get_doc=lambda *a,**k:doc,db=Row(exists=lambda *a:True),throw=fail)
        with patch.object(self.service,'frappe',fake),patch.object(self.service,'save') as save:
            with self.assertRaisesRegex(ValueError,'allocated to a subscription'):
                self.service.settle_verified('usage-1','ref',100,'Bank evidence reviewed')
            self.assertEqual(doc.status,'Unpaid')
            save.assert_not_called()
