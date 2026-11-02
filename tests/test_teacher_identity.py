import json
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
from test_upload_provisioning import function
class TeacherIdentity(TestCase):
 def setUp(self):
  self.data={'flow':'public-account-v1','kind':'Individual Teacher','email':'teacher','phone':'+94761234567'}
  self.phone=NS(phone=self.data['phone'],verified_at='now');self.profile=NS(name='p',status='Pending');self.enabled=True
  def get(dt,*a,**k):return {'User':1,'IL Public Profile':self.profile,'IL Verified Phone':self.phone}[dt]
  self.f=function('teacher_identity','eligible',{'json':json,'frappe':NS(db=NS(get_value=get),get_all=lambda *a,**k:[NS(details=json.dumps(self.data))])})
  p=patch.dict('sys.modules',{'institute_lms.public_signup':NS(enabled=lambda:self.enabled)});p.start();self.addCleanup(p.stop)
 def test_verified_identity_can_apply_without_provider_endorsement(self):self.assertTrue(self.f('teacher'))
 def test_phone_change_requires_new_proof(self):self.phone.phone='+94769999999';self.assertFalse(self.f('teacher'))
 def test_student_registration_cannot_grant_teacher_eligibility(self):self.data['kind']='Student';self.assertFalse(self.f('teacher'))
 def test_missing_phone_verification_denied(self):self.phone.verified_at=None;self.assertFalse(self.f('teacher'))
 def test_rejected_profile_denied(self):self.profile.status='Rejected';self.assertFalse(self.f('teacher'))
 def test_public_mode_off_denied(self):self.enabled=False;self.assertFalse(self.f('teacher'))
