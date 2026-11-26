"""OAuth signup intent tests; no real Google request, database or messages."""
import sys
import types
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit
from test_upload_provisioning import function


class GoogleSignupRole(unittest.TestCase):
    def setUp(self):
        self.oauth = types.ModuleType('frappe.utils.oauth')
        self.oauth.get_oauth2_authorize_url = MagicMock(return_value='https://accounts.google.com/o/oauth2/auth?state=test')
        modules = patch.dict(sys.modules, {'frappe.utils.oauth': self.oauth})
        modules.start()
        self.addCleanup(modules.stop)
        def throw(message):
            raise ValueError(message)
        self.start = function('portal_policy', 'google_start', {
            'frappe': types.SimpleNamespace(throw=throw),
            'public': lambda: {'google_available': True},
        })

    def test_each_signup_role_survives_oauth_return(self):
        for kind, expected in [('Student','Student'),('Teacher','Individual Teacher'),('Individual Teacher','Individual Teacher'),('Institute','Institute')]:
            with self.subTest(kind=kind):
                result = self.start(signup=1, kind=kind)
                provider, redirect = self.oauth.get_oauth2_authorize_url.call_args.args
                self.assertEqual(provider, 'google')
                self.assertEqual(parse_qs(urlsplit(redirect).query), {'verified_signup':['1'],'signup_role':[expected]})
                self.assertEqual(parse_qs(urlsplit(result['url']).query)['prompt'], ['select_account'])

    def test_signin_does_not_turn_into_signup(self):
        self.start(signup=0,kind='Institute')
        self.assertEqual(self.oauth.get_oauth2_authorize_url.call_args.args[1], '/campus')

    def test_privileged_or_unknown_kind_is_rejected(self):
        for kind in ['Administrator','Super Admin','Other']:
            with self.assertRaises(ValueError):
                self.start(signup=1,kind=kind)
        self.oauth.get_oauth2_authorize_url.assert_not_called()
