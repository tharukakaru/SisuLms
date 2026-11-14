import unittest,json,secrets,time
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
from test_upload_provisioning import function
from institute_lms import signup_rules

class ExistingSignup(unittest.TestCase):
    def setUp(self):
        self.data=dict(kind='Student',email='student@example.invalid',first_name='Test',last_name='Learner',phone='+94761234567',username='test_learner',country='Sri Lanka',timezone='Asia/Colombo',birth_date='2005-02-28',privacy_accepted=True,privacy_policy_version='v1')
        def fail(message): raise ValueError(message)
        self.f=NS(conf={},session=NS(user='Guest'),db=NS(exists=Mock(return_value=False),get_value=Mock(return_value=None)),throw=fail)
        self.challenges=NS(issue=Mock())
        self.google=Mock(return_value=False);self.registered=Mock(return_value=False)
        self.start=function('public_signup','start',dict(frappe=self.f,ready=lambda:None,rules=signup_rules,json=json,secrets=secrets,time=time,challenges=self.challenges,google_identity=self.google,registered_google_account=self.registered))
        self.policy=patch.dict('sys.modules',{'institute_lms.portal_policy':NS(public=lambda:{'privacy_policy_url':'/privacy','privacy_policy_version':'v1'})})
        self.policy.start();self.addCleanup(self.policy.stop)
    def test_existing_email_shows_outcome_without_sending_code(self):
        self.f.db.exists.return_value=True
        self.assertEqual(self.start(self.data),{'account_exists':True})
        self.challenges.issue.assert_not_called()
    def test_existing_google_account_cannot_restart_signup(self):
        self.f.session.user=self.data['email'];self.google.return_value=True;self.registered.return_value=True
        self.assertEqual(self.start(self.data),{'account_exists':True})
        self.challenges.issue.assert_not_called()
    def test_new_google_user_can_complete_onboarding(self):
        self.f.session.user=self.data['email'];self.google.return_value=True;self.f.db.exists.return_value=True
        self.assertIn('challenge',self.start(self.data))
        self.challenges.issue.assert_called_once()
    def test_username_collision_is_not_reported_as_existing_email(self):
        self.f.db.get_value.return_value='another@example.invalid'
        with self.assertRaisesRegex(ValueError,'Account details are unavailable'):self.start(self.data)
        self.challenges.issue.assert_not_called()
    def test_registered_google_account_requires_sisu_record(self):
        check=function('public_signup','registered_google_account',{'frappe':self.f})
        self.assertFalse(check('new@example.invalid'))
        for doctype in ('IL Public Profile','IL Member','IL Registration Request'):
            self.f.db.exists.side_effect=lambda dt,filters: dt==doctype
            self.assertTrue(check('existing@example.invalid'))
