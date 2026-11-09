import importlib,sys
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch

class DemoLearning(TestCase):
 def setUp(self):
  def fail(message,error=ValueError):raise error(message)
  self.room=NS(name='demo-room',title='[DEMO] locked',institute='I',public_provider='P',teacher='T',fee_mode='Paid',fee=1000,active=1,published=1)
  def value(dt,*args,**kw):
   return {'IL Institute':'SISUDEMO','IL Public Profile':'sisu-public-demo-independent@example.invalid','User':0,'IL Member':NS(active=0,institute='I')}.get(dt)
  self.db=Mock();self.db.get_value.side_effect=value;self.db.exists.return_value=True
  self.cache=Mock();self.cache.get_value.return_value=False
  self.f=NS(whitelist=lambda **kw:lambda f:f,throw=fail,PermissionError=PermissionError,local=NS(site='sisuacademylk.com'),db=self.db,session=NS(user='student'),cache=self.cache,get_doc=Mock(return_value=self.room))
  self.patch=patch.dict(sys.modules,{'frappe':self.f,'institute_lms.profiles':NS(required=lambda:NS(kind='Student')),'institute_lms.registration':NS(limit=Mock())})
  self.patch.start();self.addCleanup(self.patch.stop);sys.modules.pop('institute_lms.demo_learning',None)
  self.mod=importlib.import_module('institute_lms.demo_learning');self.addCleanup(lambda:sys.modules.pop('institute_lms.demo_learning',None))
 def test_demo_key_cannot_unlock_real_paid_class(self):
  self.room.title='Real paid class'
  with self.assertRaises(PermissionError):self.mod.open_practice('demo-room','SISU-DEMO')
  self.cache.set_value.assert_not_called()
 def test_class_cards_accept_plain_dicts_and_do_not_claim_real_paid_access(self):
  result=self.mod.decorate([{'name':'demo-room'}])
  self.assertTrue(result[0]['demo']);self.assertFalse(result[0]['unlocked'])
  self.room.title='Real paid class';self.cache.get_value.return_value=True
  result=self.mod.decorate([{'name':'demo-room'}])
  self.assertFalse(result[0]['demo']);self.assertFalse(result[0]['unlocked'])
 def test_follow_and_exact_key_required_without_any_database_write(self):
  self.db.exists.return_value=False
  with self.assertRaises(ValueError):self.mod.open_practice('demo-room','SISU-DEMO')
  self.db.exists.return_value=True
  with self.assertRaises(ValueError):self.mod.open_practice('demo-room','wrong')
  result=self.mod.open_practice('demo-room','SISU-DEMO')
  self.assertTrue(result['unlocked']);self.cache.set_value.assert_called_once()
  self.db.set_value.assert_not_called();self.db.sql.assert_not_called()
