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
  self.access=NS(name='G',student='Student',institute='Inst',classroom='Class',status='Awaiting key',invoice='I',ends_at=self.now+timedelta(days=1),enrollment_key_hash=hashlib.sha256(b'ABCDEF1234567890').hexdigest())
  self.saved=MagicMock();self.queued=MagicMock()
  self.f=NS(session=NS(user='student'),db=MagicMock(),get_all=MagicMock(return_value=['G']),whitelist=lambda **kw:lambda fn:fn)
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
  self.assertTrue(self.m.redeem('Class','ABCDEF1234567890')['enrolled'])
  self.assertEqual(self.f.get_all.call_args.kwargs['filters']['student'],'Student')
  self.assertEqual(self.access.status,'Active');self.assertIsNone(self.access.enrollment_key_hash)
  self.queued.assert_called_once()
  with self.assertRaises(ValueError):self.m.redeem('Class','ABCDEF1234567890')
 def test_another_students_key_is_not_found(self):
  self.f.get_all.return_value=[]
  with self.assertRaises(ValueError):self.m.redeem('Class','ABCDEF1234567890')
  self.saved.assert_not_called()
 def test_unpaid_invoice_cannot_be_unlocked(self):
  self.f.db.exists.return_value=False
  with self.assertRaises(ValueError):self.m.redeem('Class','ABCDEF1234567890')
  self.saved.assert_not_called()
 def test_expired_access_cannot_be_unlocked(self):
  self.access.ends_at=self.now-timedelta(seconds=1)
  with self.assertRaises(ValueError):self.m.redeem('Class','ABCDEF1234567890')
  self.saved.assert_not_called()
 def test_wrong_key_cannot_unlock(self):
  with self.assertRaises(ValueError):self.m.redeem('Class','WRONGKEY12345678')
  self.saved.assert_not_called()
