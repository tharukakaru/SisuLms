import hashlib
from types import SimpleNamespace as NS
from contextlib import nullcontext
from unittest import TestCase
from test_upload_provisioning import function

class VerificationWindowTests(TestCase):
    def setUp(self):
        self.clock=1000;self.values={};self.response={}
        cache=NS(lock=lambda *a,**k:nullcontext(),get_value=lambda k:self.values.get(k),set_value=lambda k,v,**kw:self.values.__setitem__(k,v))
        def fail(message):raise ValueError(message)
        f=NS(cache=cache,local=NS(response=self.response),throw=fail)
        self.limit=function('registration','limit',dict(frappe=f,time=NS(time=lambda:self.clock),hashlib=hashlib))
    def test_fifth_allowed_sixth_has_five_minute_boundary(self):
        for _ in range(5):self.limit('self-signup:email:a')
        with self.assertRaises(ValueError):self.limit('self-signup:email:a')
        self.assertEqual(self.response['retry_after_seconds'],200)
        self.clock=1200;self.limit('self-signup:email:a')
    def test_phone_and_ip_use_short_window(self):
        for ident in ('phone-user:a','phone-number:a','phone-ip:a','self-signup-ip:a'):
            for _ in range(5):self.limit(ident)
            with self.assertRaises(ValueError):self.limit(ident)
            self.assertLessEqual(self.response['retry_after_seconds'],300)
    def test_non_verification_limit_unchanged(self):
        for _ in range(5):self.limit('profile-image:a')
        with self.assertRaises(ValueError):self.limit('profile-image:a')
        self.assertEqual(self.response['retry_after_seconds'],2600)
