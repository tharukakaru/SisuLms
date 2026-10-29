import unittest
from institute_lms.billing_transport_rules import sign_message,verify_message,fingerprint
class TransportRules(unittest.TestCase):
    def setUp(self):
        self.key='x'*48
        self.p=dict(tenant_id='tenant-a',site_hostname='a.example.test',issued_at=1000,request_id='a'*32,action='settle',data={'amount_lkr':100})
    def check(self,p=None,key=None,tenant='tenant-a',site='a.example.test',now=1000):
        return verify_message(p or self.p,sign_message(self.p,self.key),key or self.key,tenant,site,now)
    def test_valid(self):self.assertEqual(self.check(),self.p)
    def test_altered_amount_rejected(self):
        with self.assertRaises(ValueError):self.check({**self.p,'data':{'amount_lkr':1}})
    def test_other_tenant_and_hostname_rejected(self):
        for kw in ({'tenant':'other'},{'site':'b.example.test'}):
            with self.assertRaises(ValueError):self.check(**kw)
    def test_expired_and_future_rejected(self):
        for now in (879,1121):
            with self.assertRaises(ValueError):self.check(now=now)
    def test_other_key_rejected(self):
        with self.assertRaises(ValueError):self.check(key='y'*48)
    def test_missing_identity_rejected(self):
        p={**self.p,'request_id':''}
        with self.assertRaises(ValueError):verify_message(p,sign_message(p,self.key),self.key,'tenant-a','a.example.test',1000)
    def test_snapshot_binds_amount_not_mutable_status(self):
        d={'name':'invoice-a','amount_lkr':100,'status':'Unpaid'}
        self.assertEqual(fingerprint(d),fingerprint({**d,'status':'Paid'}))
        self.assertNotEqual(fingerprint(d),fingerprint({**d,'amount_lkr':50}))
