import importlib.util
import sys
import types
import unittest
from datetime import datetime, date
from pathlib import Path
from unittest.mock import MagicMock, patch
from institute_lms.delivery_rules import address_snapshot, offer_values, next_status

class Rules(unittest.TestCase):
    def test_confirmed_residential_address_required(self):
        data=dict(recipient='Example learner',phone='+94771234567',address_line1='12 Example Road',city='Colombo',postal_code='00100',country='Sri Lanka',address_confirmed=True)
        self.assertEqual(address_snapshot(data)['city'],'Colombo')
        for missing in ('address_confirmed','recipient','phone','address_line1','city','postal_code','country'):
            with self.subTest(missing=missing), self.assertRaises(ValueError):address_snapshot({**data,missing:''})
        with self.assertRaises(ValueError):address_snapshot({**data,'phone':'0771234567'})
    def test_offer_price_and_disable(self):
        self.assertEqual(offer_values({'enabled':False}),{'enabled':0})
        data=dict(enabled=True,title='Tute',bank_instructions='Example bank',amount='750.50')
        self.assertEqual(offer_values(data)['amount_minor'],75050)
        for price in ('0','-1','NaN','0.001'):
            with self.assertRaises(ValueError):offer_values({**data,'amount':price})
    def test_payment_must_precede_dispatch(self):
        self.assertEqual(next_status('Pending','Approved'),'Approved')
        self.assertEqual(next_status('Approved','Dispatched'),'Dispatched')
        for current,action in [('Pending','Dispatched'),('Rejected','Dispatched'),('Dispatched','Approved'),('Approved','Approved')]:
            with self.assertRaises(ValueError):next_status(current,action)

class Row(dict):
    def __getattr__(self,key):return self.get(key)

class Service(unittest.TestCase):
    def setUp(self):
        f=types.ModuleType('frappe');f.whitelist=lambda **kw:lambda fn:fn;f.PermissionError=PermissionError
        f.throw=lambda text,exc=ValueError:(_ for _ in ()).throw(exc(text))
        f.db=MagicMock();f.get_doc=MagicMock();f.get_all=MagicMock(return_value=[]);f.session=Row(user='student')
        self.f=f;self.room=Row(name='C',institute='I',active=1,owner_type='Institute');self.member=Row(name='S',role='Student');self.account=Row(name='A',plan='Platinum')
        api=types.ModuleType('institute_lms.api');api.classroom_for=MagicMock(return_value=(Row(name='I'),self.member,self.room));api.access=lambda *a:{'allowed':True};self.api=api
        commercial=types.ModuleType('institute_lms.commercial');commercial.account_for=lambda *a:self.account;commercial.locked_reason=lambda a:None;self.commercial=commercial
        util=types.ModuleType('frappe.utils');util.now_datetime=lambda:datetime(2026,10,16);util.getdate=lambda x:date.fromisoformat(str(x)[:10])
        p=patch.dict(sys.modules,{'frappe':f,'frappe.utils':util,'institute_lms.api':api,'institute_lms.commercial':commercial});p.start();self.addCleanup(p.stop)
        spec=importlib.util.spec_from_file_location('institute_lms.delivery',Path(__file__).resolve().parents[1]/'institute_lms/delivery.py');self.d=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.d)
    def test_gold_denies_mutations_and_hides_addresses(self):
        self.account.plan='Gold';self.account['plan']='Gold'
        with self.assertRaises(PermissionError):self.d.configure('C',{'enabled':True})
        state=self.d.state('C');self.assertFalse(state['available']);self.assertEqual(state['orders'],[]);self.f.get_all.assert_not_called()
    def test_unassigned_fails_closed(self):
        self.account=None
        with self.assertRaises(PermissionError):self.d.context('C')
    def test_provider_suspended_denies_reads(self):
        self.commercial.locked_reason=lambda a:'Workspace suspended'
        with self.assertRaises(PermissionError):self.d.state('C')
    def test_student_query_scoped_before_pagination(self):
        self.d.offer_for=lambda room:None;self.d.state('C',2)
        kw=self.f.get_all.call_args.kwargs
        self.assertEqual(kw['filters'],{'institute':'I','classroom':'C','student':'S'});self.assertEqual(kw['start'],50)
    def test_teacher_still_scoped_to_class(self):
        self.member['role']='Teacher';self.d.offer_for=lambda room:None;self.d.state('C')
        self.assertEqual(self.f.get_all.call_args.kwargs['filters'],{'institute':'I','classroom':'C'})
    def test_other_student_cannot_read_proof(self):
        self.f.get_doc.return_value=Row(name='O',classroom='C',student='another-student',institute='I')
        with self.assertRaises(PermissionError):self.d.proof('O')
    def test_cross_institute_order_denied(self):
        self.f.get_doc.return_value=Row(name='O',classroom='C',student='S',institute='OTHER')
        with self.assertRaises(PermissionError):self.d.checked_order('O')
    def test_staff_write_authority_required(self):
        self.api.classroom_for.side_effect=PermissionError('Not assigned')
        with self.assertRaises(PermissionError):self.d.configure('C',{})
        self.api.classroom_for.assert_called_once_with('C',True)

if __name__=='__main__':unittest.main()
