from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock
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
