import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch


class MobileAuthTests(TestCase):
    def setUp(self):
        now = datetime(2026, 11, 9)
        self.document = NS(name='M1', user='student', revoked=0,
                           expires_at=now + timedelta(days=1), google_authenticated=1)
        self.document.get = lambda key: 'I1' if key == 'institute' else None
        self.f = NS(
            local=NS(form_dict={'institute': 'I2'},
                     request=NS(path='/api/method/institute_lms.campus_context.select')),
            session=NS(user='Guest', data={'old': True}),
            db=MagicMock(), get_doc=MagicMock(return_value=self.document),
            get_request_header=MagicMock(return_value='Sisu ' + 'x' * 48),
            PermissionError=PermissionError, AuthenticationError=ValueError,
            whitelist=lambda **kw: lambda fn: fn,
        )
        self.f.form_dict = self.f.local.form_dict
        self.f.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        self.f.db.get_value.side_effect = lambda dt, *a: 'M1' if dt == 'IL Mobile Session' else 1

        def set_user(user):
            self.f.session.user = user
            self.f.session.data = {}
            self.f.local.form_dict = {}
            self.f.form_dict = self.f.local.form_dict

        self.f.set_user = MagicMock(side_effect=set_user)
        root = Path(__file__).parents[1] / 'institute_lms'
        spec = importlib.util.spec_from_file_location('institute_lms.mobile_auth_under_test', root / 'mobile_auth.py')
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', {
            'frappe': self.f,
            'frappe.utils': NS(now_datetime=lambda: now, get_datetime=lambda value: value, get_url=lambda: ''),
            'institute_lms.saas': NS(managed=MagicMock()),
        }):
            spec.loader.exec_module(self.module)

    def test_parsed_arguments_survive_identity_reset_and_rpc_dispatch(self):
        self.module.authenticate()
        self.f.local.form_dict['cmd'] = 'institute_lms.campus_context.select'
        select = lambda institute: institute
        args = {key: value for key, value in self.f.form_dict.items() if key != 'cmd'}
        self.assertEqual(select(**args), 'I2')
        self.assertEqual(self.f.session.user, 'student')
        self.assertEqual(self.f.session.data, {})
        self.assertEqual(self.f.local.il_mobile_session, 'M1')
        self.assertEqual(self.f.local.il_mobile_institute, 'I1')
        self.assertTrue(self.f.local.il_mobile_google)

    def test_revoked_token_rejected_before_identity_change(self):
        self.document.revoked = 1
        with self.assertRaisesRegex(ValueError, 'expired or revoked'):
            self.module.authenticate()
        self.f.set_user.assert_not_called()

    def test_client_cmd_still_rejected(self):
        self.f.form_dict['cmd'] = 'institute_lms.campus_context.select'
        with self.assertRaises(PermissionError):
            self.module.authenticate()
        self.f.set_user.assert_not_called()

    def test_browser_cookie_mixing_still_rejected(self):
        self.f.session.user = 'student'
        with self.assertRaisesRegex(ValueError, 'mix mobile tokens'):
            self.module.authenticate()
        self.f.set_user.assert_not_called()
