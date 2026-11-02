from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
import sys
from test_upload_provisioning import function

class OwnerControlPanel(TestCase):
    def test_audit_requires_owner_before_reading(self):
        owner=Mock(side_effect=PermissionError('Owner required'))
        db=Mock()
        fn=function('platform','audit_log',{'owner':owner,'frappe':db})
        with self.assertRaises(PermissionError):fn()
        db.get_all.assert_not_called()

    def test_audit_pagination_is_bounded(self):
        db=Mock();db.get_all.return_value=[]
        fn=function('platform','audit_log',{'owner':Mock(),'frappe':db})
        fn(-4)
        self.assertEqual(db.get_all.call_args.kwargs['limit_start'],0)
        fn(1000000)
        self.assertEqual(db.get_all.call_args.kwargs['limit_start'],500000)
        self.assertEqual(db.get_all.call_args.kwargs['limit_page_length'],50)

    def test_paused_subscription_blocks_before_merchant_config(self):
        def throw(message):raise ValueError(message)
        platform=NS(control=Mock())
        fn=function('subscription_payments','config',{'frappe':NS(conf={'il_payments_paused':True},throw=throw)})
        with patch.dict(sys.modules,{'institute_lms.platform':platform}):
            with self.assertRaisesRegex(ValueError,'Payments are paused'):fn()
        platform.control.assert_called_once()

    def test_invalid_registration_code_returns_user_validation(self):
        def throw(message):raise RuntimeError(message)
        fn=function('platform','register',{'owner':Mock(),'frappe':NS(throw=throw)})
        domain=NS(institute_code=Mock(side_effect=ValueError('Institute code must start with a letter')))
        with patch.dict(sys.modules,{'institute_lms.domain':domain,'institute_lms.contact':NS(email_address=Mock())}):
            with self.assertRaisesRegex(RuntimeError,'start with a letter'):
                fn('Test','1234','test.example.invalid','test@example.invalid')
