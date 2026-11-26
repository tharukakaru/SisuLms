import hashlib,json
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock
from test_upload_provisioning import function

class InstituteAutomaticApproval(TestCase):
 def setUp(self):
  self.f=NS(db=MagicMock(),get_doc=MagicMock(),PermissionError=PermissionError)
  def fail(message,kind=ValueError):raise kind(message)
  self.f.throw=fail;self.f.db.exists.return_value=False
  self.doc=NS(name='request',status='Pending review',email='institute@example.invalid',details='{"full_name":"Owner"}')
  self.doc.insert=MagicMock(return_value=self.doc);self.doc.save=MagicMock()
  self.f.get_doc.return_value=self.doc
  self.approve=MagicMock(side_effect=lambda *args:setattr(self.doc,'status','Approved'))
  self.create=function('registration','_new_verified_institute',{'frappe':self.f,'json':json,'hashlib':hashlib,'_apply_application_review':self.approve})
  self.details={'kind':'Institute','email':self.doc.email,'username':'academy'}
 def test_new_institute_reuses_approval_without_creating_workspace(self):
  self.assertEqual(self.create(self.details).status,'Approved')
  payload=self.f.get_doc.call_args.args[0]
  self.assertEqual(payload['account_type'],'Institute');self.assertEqual(payload['email_verified'],1)
  self.assertFalse(json.loads(payload['details'])['onboarding_profile_completed'])
  self.approve.assert_called_once();self.assertIsNone(self.approve.call_args.args[3])
  self.assertEqual(self.f.get_doc.call_count,1)
 def test_existing_user_pending_application_or_username_never_auto_approved(self):
  for collision in range(3):
   self.f.db.exists.side_effect=lambda *a,**k: (a[0]=='User' if collision==0 else a[0]=='IL Registration Request' if collision==1 else a[0]=='IL Public Profile')
   with self.assertRaises(ValueError):self.create(self.details)
  self.approve.assert_not_called();self.doc.insert.assert_not_called()
 def test_teacher_and_owner_cannot_use_institute_approval(self):
  for kind in ('Individual Teacher','Super Admin','Student'):
   with self.assertRaises(PermissionError):self.create({**self.details,'kind':kind})
  self.doc.insert.assert_not_called()
 def test_two_challenges_share_database_unique_request_identity(self):
  self.create(self.details);a=self.doc.insert.call_args.kwargs['set_name']
  self.create(self.details);b=self.doc.insert.call_args.kwargs['set_name']
  self.assertEqual(a,b)
 def test_duplicate_insert_never_reaches_approval(self):
  self.doc.insert.side_effect=ValueError('Duplicate primary key')
  with self.assertRaises(ValueError):self.create(self.details)
  self.approve.assert_not_called()
 def test_existing_owner_review_still_requires_owner(self):
  denied=MagicMock(side_effect=PermissionError())
  review=function('registration','review_application',{'frappe':self.f,'require_owner':denied})
  with self.assertRaises(PermissionError):review('request','Approved','reason')
  self.f.db.sql.assert_not_called()
