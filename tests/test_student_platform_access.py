from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock
from test_upload_provisioning import function

class StudentPlatformAccess(TestCase):
    def test_expired_student_plan_does_not_block_dashboard(self):
        f=function('account_billing','state',{})
        self.assertEqual(f(NS(role='Student',enabled=1,trial_until='2000-01-01')),{'state':'Included','available':True})
    def test_suspended_student_stays_blocked(self):
        f=function('account_billing','state',{})
        self.assertFalse(f(NS(role='Student',enabled=0))['available'])
    def test_student_platform_price_zero_without_billing_country(self):
        f=function('account_billing','price',{})
        self.assertEqual(f(NS(role='Student'),'Student'),0)
    def test_no_student_platform_invoice(self):
        def fail(message):raise ValueError(message)
        f=function('account_billing','make_invoice',{'frappe':NS(throw=fail)})
        with self.assertRaisesRegex(ValueError,'no student platform subscription'):
            f(NS(role='Student'))
