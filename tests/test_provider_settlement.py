import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from datetime import datetime

class Doc(dict):
    def __getattr__(self,k):return self.get(k)
    def __setattr__(self,k,v):self[k]=v
    def update(self,values):return super().update(values)

class ProviderSettlement(unittest.TestCase):
    def setUp(self):
        def fail(message,*args):raise ValueError(message)
        self.queue=Mock();self.saved=Mock()
        frappe=types.ModuleType('frappe');frappe.throw=fail;frappe.whitelist=lambda **k:lambda fn:fn
        utils=types.ModuleType('frappe.utils');utils.get_url=lambda path='':'https://example.invalid'+path;utils.now_datetime=lambda:datetime(2026,10,18);utils.get_datetime=lambda v:v
        commercial=types.ModuleType('institute_lms.commercial');commercial.locked=Mock();commercial.save=self.saved;commercial.account_access=Mock()
        gateway=types.ModuleType('institute_lms.payments_lk');gateway.provider_request=Mock()
        documents=types.ModuleType('institute_lms.provider_documents');documents.queue_document=self.queue
        modules={'frappe':frappe,'frappe.utils':utils,'institute_lms.commercial':commercial,'institute_lms.payments_lk':gateway,'institute_lms.provider_documents':documents}
        self.patch=patch.dict(sys.modules,modules);self.patch.start();self.addCleanup(self.patch.stop)
        spec=importlib.util.spec_from_file_location('institute_lms._test_cards',Path(__file__).parents[1]/'institute_lms/provider_cards.py');self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
    def test_settlement_issues_one_receipt_and_late_failure_cannot_unpay(self):
        bill=Doc(name='INV1',status='Unpaid');p={'id':'pay_123','status':'succeeded'}
        self.module.apply_payment(bill,p);self.module.apply_payment(bill,p)
        self.assertEqual(bill.status,'Paid');self.assertEqual(bill.receipt_number,'RC-INV1');self.assertEqual(self.queue.call_count,1)
        self.module.apply_payment(bill,{'id':'pay_123','status':'failed'});self.assertEqual(bill.status,'Paid')
        with self.assertRaises(ValueError):self.module.apply_payment(bill,{'id':'pay_other','status':'succeeded'})
    def test_decline_and_processing_do_not_create_receipts(self):
        for status in ('processing','failed'):
            bill=Doc(name='INV2',status='Unpaid');self.module.apply_payment(bill,{'id':'pay_2','status':status});self.assertEqual(bill.status,'Unpaid')
        self.queue.assert_not_called()
    def test_bank_review_conflict_requires_reconciliation(self):
        with self.assertRaises(ValueError):self.module.apply_payment(Doc(name='INV3',status='Under review'),{'id':'pay_3','status':'succeeded'})
        self.queue.assert_not_called()
