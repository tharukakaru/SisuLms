"""Boundary test: the assigned instructor must never redirect institute revenue."""
import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock,patch
from decimal import Decimal

class Record(dict):
    def __getattr__(self,k):return self.get(k)

class SettlementOwnership(unittest.TestCase):
    def test_institution_and_independent_beneficiaries_and_frozen_split(self):
        frappe=types.ModuleType('frappe');frappe.get_all=MagicMock(return_value=['institute-wallet'])
        def fail(message,*args):raise ValueError(message)
        frappe.throw=fail
        prices=types.ModuleType('institute_lms.owner_pricing')
        prices.current=lambda *args:Record(name='price-revision-1',currency='LKR',period='Per payment')
        prices.amount=lambda _:dict(total_minor=30000)
        commercial=types.ModuleType('institute_lms.commercial');commercial.account_for=lambda *a:None
        key='institute_lms.class_billing';previous=sys.modules.pop(key,None)
        try:
            with patch.dict(sys.modules,{'frappe':frappe,'institute_lms.owner_pricing':prices,'institute_lms.commercial':commercial}):
                billing=importlib.import_module(key)
                institute=Record(name='TA')
                room=Record(owner_type='Institute',teacher='nimal',owner_user='institute@example.invalid')
                quote=billing.invoice_split(institute,8000,'student@example.invalid',room)
                self.assertEqual(quote['amount'],Decimal('8300'))
                self.assertEqual(quote['beneficiary_minor'],800000)
                self.assertEqual(quote['platform_minor'],30000)
                self.assertEqual(quote['payout_wallet'],'institute-wallet')
                filters=frappe.get_all.call_args.kwargs['filters']
                self.assertEqual(filters['beneficiary'],'Institute');self.assertNotIn('owner_user',filters)
                # Changing the instructor has no effect on ownership or recipient.
                room['teacher']='another-teacher'
                self.assertEqual(billing.settlement_filters(institute,room),filters)
                programme=billing.invoice_split(institute,135000,'student@example.invalid',room)
                self.assertEqual(programme['beneficiary_minor'],13500000)
                room.update(owner_type='Teacher',owner_user='nimal@example.invalid')
                filters=billing.settlement_filters(institute,room)
                self.assertEqual(filters['beneficiary'],'Teacher');self.assertEqual(filters['owner_user'],'nimal@example.invalid')
                frappe.get_all.return_value=[]
                with self.assertRaises(ValueError):billing.invoice_split(institute,8000,'student@example.invalid',room)
                # Monthly packages collect full tuition for the frozen class owner.
                commercial.account_for=lambda *a:Record(name='provider-monthly')
                frappe.conf={'il_class_collection_mode':'platform'}
                frappe.get_all.return_value=['teacher-wallet']
                full=billing.invoice_split(institute,8000,'student@example.invalid',room)
                self.assertEqual(full['amount'],Decimal('8000'))
                self.assertEqual(full['beneficiary_minor'],800000)
                self.assertEqual(full['platform_minor'],0)
                self.assertEqual(full['payout_wallet'],'teacher-wallet')
                frappe.conf={}
                direct=billing.invoice_split(institute,8000,'student@example.invalid',room)
                self.assertIsNone(direct['payout_wallet'])
        finally:
            sys.modules.pop(key,None)
            if previous:sys.modules[key]=previous
