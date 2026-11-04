import importlib.util
import hashlib
import sys
import unittest
from datetime import datetime,timedelta
from types import SimpleNamespace as NS
from unittest.mock import MagicMock,patch
from pathlib import Path

class Keys(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,11,3)
  self.key='1793664000-ABCDEF1234567890'
  self.clock=patch('time.time',return_value=1793664000);self.clock.start();self.addCleanup(self.clock.stop)
  self.access=NS(name='G',student='Student',institute='Inst',classroom='Class',status='Awaiting key',invoice='I',ends_at=self.now+timedelta(days=1),enrollment_key_hash=hashlib.sha256(self.key.encode()).hexdigest())
  self.saved=MagicMock();self.queued=MagicMock()
  self.f=NS(session=NS(user='student'),db=MagicMock(),get_all=MagicMock(return_value=['G']),whitelist=lambda **kw:lambda fn:fn)
  self.f.cache=MagicMock();self.f.cache.get_value.return_value=None
  self.f.throw=lambda msg,*args:(_ for _ in ()).throw(ValueError(msg))
  self.f.db.exists.return_value=True
  self.modules={'frappe':self.f,'frappe.utils':NS(now_datetime=lambda:self.now,get_datetime=lambda v:v),
    'institute_lms.api':NS(identity=lambda:(NS(name='Inst'),NS(name='Student',role='Student')),require_role=lambda *a:None,scoped=lambda *a:NS(name='Class',title='Math')),
    'institute_lms.commercial':NS(locked=lambda *a:self.access,save=self.saved),
    'institute_lms.registration':NS(limit=lambda *a:None),
    'institute_lms.account_confirmations':NS(queue=self.queued)}
  self.p=patch.dict(sys.modules,self.modules);self.p.start();self.addCleanup(self.p.stop)
  spec=importlib.util.spec_from_file_location('institute_lms._keys_test',Path(__file__).parents[1]/'institute_lms/class_keys.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
 def test_redeem_is_student_scoped_and_consumed(self):
  self.assertTrue(self.m.redeem('Class',self.key)['enrolled'])
  self.assertEqual(self.f.get_all.call_args.kwargs['filters']['student'],'Student')
  self.assertEqual(self.access.status,'Active');self.assertIsNone(self.access.enrollment_key_hash)
  self.queued.assert_called_once()
  with self.assertRaises(ValueError):self.m.redeem('Class',self.key)
 def test_another_students_key_is_not_found(self):
  self.f.get_all.return_value=[]
  with self.assertRaises(ValueError):self.m.redeem('Class',self.key)
  self.saved.assert_not_called()
 def test_unpaid_invoice_cannot_be_unlocked(self):
  self.f.db.exists.return_value=False
  with self.assertRaises(ValueError):self.m.redeem('Class',self.key)
  self.saved.assert_not_called()
 def test_expired_access_cannot_be_unlocked(self):
  self.access.ends_at=self.now-timedelta(seconds=1)
  with self.assertRaises(ValueError):self.m.redeem('Class',self.key)
  self.saved.assert_not_called()
 def test_wrong_key_cannot_unlock(self):
  with self.assertRaises(ValueError):self.m.redeem('Class','WRONGKEY12345678')
  self.saved.assert_not_called()

 def test_key_expires_after_fifteen_minutes(self):
  with patch('time.time',return_value=1793664900):
   with self.assertRaisesRegex(ValueError,'expired'):self.m.redeem('Class',self.key)
  self.saved.assert_not_called()
 def test_resend_rotates_key_without_new_payment(self):
  old=self.access.enrollment_key_hash
  result=self.m.resend('Class')
  self.assertEqual(result['expires_in_seconds'],900)
  self.assertNotEqual(old,self.access.enrollment_key_hash)
  self.queued.assert_called_once()
  with self.assertRaises(ValueError):self.m.redeem('Class',self.key)
 def test_resend_requires_paid_invoice(self):
  self.f.db.exists.return_value=False
  with self.assertRaises(ValueError):self.m.resend('Class')
  self.saved.assert_not_called();self.queued.assert_not_called()
 def test_resend_throttled(self):
  self.f.cache.get_value.return_value=1793663990
  with self.assertRaisesRegex(ValueError,'one minute'):self.m.resend('Class')
  self.saved.assert_not_called()

 def test_institute_teacher_cannot_replace_institute_bank(self):
  room=NS(name='Class',owner_type='Institute',owner_user=None)
  self.modules['institute_lms.api'].classroom_for=lambda *a:(NS(name='Inst'),NS(role='Teacher'),room)
  self.modules['institute_lms.commercial'].account_for=MagicMock()
  self.f.PermissionError=ValueError
  with self.assertRaisesRegex(ValueError,'payment recipient'):self.m.save_bank_details('Class','My private bank account')
  self.saved.assert_not_called()
 def test_independent_owner_can_save_bank(self):
  room=NS(name='Class',owner_type='Teacher',owner_user='student')
  account=NS(bank_instructions='')
  self.modules['institute_lms.api'].classroom_for=lambda *a:(NS(name='Inst'),NS(role='Teacher'),room)
  self.modules['institute_lms.commercial'].account_for=lambda *a:account
  self.assertTrue(self.m.save_bank_details('Class','Bank, holder, account, branch')['saved'])
  self.assertEqual(account.bank_instructions,'Bank, holder, account, branch')
 def test_institute_admin_can_save_bank(self):
  room=NS(name='Class',owner_type='Institute',owner_user=None)
  account=NS(bank_instructions='')
  self.modules['institute_lms.api'].classroom_for=lambda *a:(NS(name='Inst'),NS(role='Admin'),room)
  self.modules['institute_lms.commercial'].account_for=lambda *a:account
  self.assertTrue(self.m.save_bank_details('Class','Institute bank account details')['saved'])
