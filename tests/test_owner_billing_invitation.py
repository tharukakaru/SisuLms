from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock
from test_upload_provisioning import function
class BillingInvitation(TestCase):
    def test_both_frappe_token_methods_queue_without_using_owner_as_sender(self):
        for method in ('_reset_password','reset_password'):
            reset=Mock(return_value='https://platform.example/update-password?key=private')
            user=NS(enabled=1,**{method:reset})
            frappe=NS(db=NS(exists=lambda *args:True),get_doc=lambda *args:user,sendmail=Mock())
            fn=function('platform','invite_billing_contact',{'frappe':frappe,'owner':Mock(),'organization':lambda _:NS(admin_contact='billing@example.com',title='A & B'),'audit':Mock()})
            self.assertEqual(fn('org'),{'queued':True})
            reset.assert_called_once_with(send_email=False)
            args=frappe.sendmail.call_args.kwargs
            self.assertTrue(args['delayed']);self.assertNotIn('sender',args);self.assertIn('A &amp; B',args['message'])
    def test_owner_check_runs_before_any_contact_lookup(self):
        owner=Mock(side_effect=PermissionError);lookup=Mock()
        fn=function('platform','invite_billing_contact',{'owner':owner,'organization':lookup})
        with self.assertRaises(PermissionError):fn('org')
        lookup.assert_not_called()
