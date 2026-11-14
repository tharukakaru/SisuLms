from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
from test_upload_provisioning import function
class PublicSignupBoundaries(TestCase):
    def test_requires_explicit_public_and_shared_flags(self):
        enabled=function('public_signup','enabled',{})
        for config in ({},{'il_public_signup_enabled':1},{'il_shared_campus_enabled':1},{'il_public_signup_enabled':1,'il_shared_campus_enabled':1,'il_control_plane':1}):
            self.assertFalse(enabled(config))
        self.assertTrue(enabled({'il_public_signup_enabled':1,'il_shared_campus_enabled':1}))
    def test_sandbox_proof_cannot_complete_public_signup(self):
        def fail(message):raise ValueError(message)
        read=function('public_signup','read',{'challenges':NS(read=lambda _: {'flow':'verified-self-signup-v1'}),'frappe':NS(throw=fail)})
        with self.assertRaisesRegex(ValueError,'Start public signup'):read('token')
    def test_public_challenge_retains_verified_state(self):
        state={'flow':'public-account-v1','email_verified':True,'phone_verified':False}
        read=function('public_signup','read',{'challenges':NS(read=lambda _:state)})
        self.assertIs(read('token'),state)

    def test_google_start_accepts_new_provider_but_rejects_registered_identity(self):
        import secrets,time
        from institute_lms import signup_rules
        def fail(message):raise ValueError(message)
        email='new@example.invalid'
        f=NS(conf={'il_public_signup_enabled':1,'il_shared_campus_enabled':1},session=NS(user=email),db=NS(exists=Mock(return_value=True),get_value=Mock(return_value=None)),throw=fail)
        issue=Mock();registered=Mock(return_value=False)
        start=function('public_signup','start',dict(ready=lambda:None,frappe=f,rules=signup_rules,google_identity=lambda e:e==email,registered_google_account=registered,challenges=NS(issue=issue),secrets=secrets,time=time))
        fields=dict(kind='Individual Teacher',teaching_path='institute',email=email,phone='+94761234567',first_name='Test',last_name='Teacher',username='test_teacher',country='Sri Lanka',timezone='Asia/Colombo',subject='Maths',privacy_accepted=True,privacy_policy_version='v1')
        with patch.dict('sys.modules',{'institute_lms.portal_policy':NS(public=lambda:dict(privacy_policy_url='/privacy',privacy_policy_version='v1'))}):
            self.assertIn('challenge',start(fields))
            self.assertEqual(issue.call_args.args[1]['details']['teaching_path'],'institute')
            registered.return_value=True;issue.reset_mock()
            self.assertEqual(start(fields),{'account_exists':True})
            issue.assert_not_called()
