from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
from test_upload_provisioning import function
class PublicPasswordLogin(TestCase):
    def test_requires_both_verified_contacts_and_student_profile(self):
        f=NS(conf={'public':True},db=NS(get_value=Mock(return_value=NS(phone='+94700000000',verified_at='now')),exists=Mock(return_value=True)))
        predicate=function('portal_policy','verified_public_password_account',{'frappe':f})
        with patch.dict('sys.modules',{'institute_lms.public_signup':NS(enabled=lambda c:c.get('public',False))}):
            self.assertTrue(predicate('student'))
            self.assertFalse(predicate('Guest'))
            f.db.exists.return_value=False;self.assertFalse(predicate('student'))
            f.db.exists.return_value=True;f.db.get_value.return_value=None;self.assertFalse(predicate('student'))
            f.conf={};self.assertFalse(predicate('student'))
