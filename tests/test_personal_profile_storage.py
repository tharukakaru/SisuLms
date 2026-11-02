import importlib,sys
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
from test_upload_provisioning import function

class PersonalStorage(TestCase):
 def setUp(self):
  def fail(message,error=ValueError):raise error(message)
  self.f=NS(conf={},throw=fail,PermissionError=PermissionError,db=Mock(),get_all=Mock(return_value=[]))
  self.patch=patch.dict(sys.modules,{'frappe':self.f,'institute_lms.campus_context':NS(enabled=lambda:True,require_user=lambda:'me')})
  self.patch.start();self.addCleanup(self.patch.stop)
  sys.modules.pop('institute_lms.profile_storage',None)
  self.m=importlib.import_module('institute_lms.profile_storage');self.addCleanup(lambda:sys.modules.pop('institute_lms.profile_storage',None))
 def test_personal_storage_context_is_owned_bounded_and_cleared(self):
  self.assertFalse(self.m.bounded(30))
  with self.assertRaises(PermissionError):
   with self.m.personal_upload(NS(name='P',user='someone-else')):pass
  with self.m.personal_upload(NS(name='P',user='me')):
   self.assertTrue(self.m.bounded(100,NS(attached_to_doctype='IL Public Profile',attached_to_name='P',is_private=0)))
   with self.assertRaises(PermissionError):self.m.bounded(100,NS(attached_to_doctype='IL Classroom',attached_to_name='P',is_private=0))
   with self.assertRaises(ValueError):self.m.bounded(1024*1024+1)
  self.assertFalse(self.m.bounded(30))
 def test_quota_rejects_accumulated_photos(self):
  self.f.get_all.return_value=[NS(file_size=1)]*40
  with self.assertRaises(ValueError):
   with self.m.personal_upload(NS(name='P',user='me')):pass
 def test_shared_profile_save_does_not_activate_institute_membership(self):
  import json,re
  profile=NS(name='P',user='me',username='student',kind='Student',display_name='Student',country='Sri Lanka',is_school=0,status='Verified',code='ST',lms_id='ST1')
  profile.set=lambda key,value:setattr(profile,key,value)
  self.f.db.exists.return_value=True;self.f.session=NS(user='me')
  activate=Mock();write=Mock()
  fn=function('profiles','save_profile',{'frappe':self.f,'json':json,'re':re,'signed_in':Mock(),'mine':lambda:profile,'write':write})
  with patch.dict(sys.modules,{'institute_lms.onboarding':NS(account_kind=lambda:'Student',activate=activate),'institute_lms.portal_policy':NS(require_google_student=Mock())}):
   fn({'kind':'Student','username':'student','display_name':'Student','country':'Sri Lanka','grades':'Grade 11'})
  write.assert_called_once_with(profile);activate.assert_not_called();self.assertEqual(profile.grades,'Grade 11')
