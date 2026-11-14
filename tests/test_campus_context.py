import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch


class CampusContextTests(TestCase):
    def setUp(self):
        self.f = NS(conf={'il_shared_campus_enabled': 1}, session=NS(user='student', data={}),
                    db=MagicMock(), get_doc=MagicMock(), local=NS(session_obj=MagicMock()),
                    PermissionError=PermissionError, whitelist=lambda **kw: lambda fn: fn)
        self.f.throw = lambda message, exc: (_ for _ in ()).throw(exc(message))
        self.f.db.get_value.side_effect = lambda dt, *a, **kw: 1 if dt == 'User' else NS(name='M1', role='Student', institute='I1')
        spec = importlib.util.spec_from_file_location('context_under_test', Path(__file__).parents[1] / 'institute_lms/campus_context.py')
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', {'frappe': self.f}):
            spec.loader.exec_module(self.module)

    def test_off_by_default(self):
        self.f.conf = {}
        with self.assertRaises(PermissionError): self.module.select('I1')
        self.f.local.session_obj.update.assert_not_called()

    def test_control_plane_cannot_be_shared_campus(self):
        self.f.conf['il_control_plane'] = 1
        with self.assertRaises(PermissionError): self.module.select('I1')

    def test_guest_cannot_select(self):
        self.f.session.user = 'Guest'
        with self.assertRaises(PermissionError): self.module.select('I1')

    def test_selection_uses_authenticated_membership(self):
        result = self.module.select('I1')
        self.assertEqual(result['role'], 'Student')
        self.f.db.get_value.assert_called_with('IL Member', {'institute': 'I1', 'user': 'student', 'active': 1}, ['name', 'role', 'institute'], as_dict=True)
        self.assertEqual(self.f.session.data['il_active_institute'], 'I1')

    def test_foreign_institute_does_not_replace_selection(self):
        self.f.session.data['il_active_institute'] = 'I1'
        self.f.db.get_value.side_effect = lambda dt, *a, **kw: 1 if dt == 'User' else None
        with self.assertRaises(PermissionError): self.module.select('I2')
        self.assertEqual(self.f.session.data['il_active_institute'], 'I1')

    def test_revocation_blocks_open_session(self):
        self.module.select('I1')
        self.f.db.get_value.side_effect = lambda dt, *a, **kw: 1 if dt == 'User' else None
        with self.assertRaises(PermissionError): self.module.current_institute()
        self.f.get_doc.assert_not_called()

    def test_no_implicit_institute(self):
        with self.assertRaises(PermissionError): self.module.current_institute()
        self.f.get_doc.assert_not_called()

    def test_clear_returns_to_no_institute_without_deleting_membership(self):
        self.f.session.data['il_active_institute'] = 'I1'
        self.assertIsNone(self.module.clear()['selected'])
        self.assertNotIn('il_active_institute', self.f.session.data)
        self.f.db.delete.assert_not_called()

    def test_choices_are_limited_to_current_active_memberships(self):
        self.f.get_all = MagicMock(return_value=[NS(institute='I1', role='Teacher')])
        self.f.db.get_value.side_effect = lambda dt, *a, **kw: 1 if dt == 'User' else 'Joined academy'
        self.f.session.data['il_active_institute'] = 'revoked-institute'
        result = self.module.choices()
        self.assertIsNone(result['selected'])
        self.assertEqual([r['institute'] for r in result['institutes']], ['I1'])
        self.assertEqual(self.f.get_all.call_args.kwargs['filters'], {'user': 'student', 'active': 1})

    def mobile(self):
        self.module.__package__ = 'institute_lms'
        self.f.local.il_mobile_session = 'device-1'
        self.f.local.il_mobile_institute = None
        self.doc = NS(user='student', revoked=0, expires_at=100, institute=None)
        self.f.get_doc.return_value = self.doc
        self.saved = MagicMock()
        mocked = {'frappe.utils': NS(get_datetime=lambda value: value, now_datetime=lambda: 50),
                  'institute_lms.saas': NS(managed=self.saved)}
        patcher = patch.dict('sys.modules', mocked)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_mobile_selection_persists_only_authenticated_device(self):
        self.mobile()
        self.f.session.data['il_active_institute'] = 'browser-campus'
        self.module.select('I1')
        self.assertEqual(self.doc.institute, 'I1')
        self.assertEqual(self.module.selected_institute(), 'I1')
        self.saved.assert_called_once_with(self.doc)
        self.f.get_doc.assert_called_once_with('IL Mobile Session', 'device-1', for_update=True)
        self.assertEqual(self.f.session.data['il_active_institute'], 'browser-campus')
        self.f.local.session_obj.update.assert_not_called()

    def test_mobile_clear_does_not_clear_browser(self):
        self.mobile()
        self.f.session.data['il_active_institute'] = 'browser-campus'
        self.module.clear()
        self.assertIsNone(self.doc.institute)
        self.assertIsNone(self.module.selected_institute())
        self.saved.assert_called_once()
        self.assertEqual(self.f.session.data['il_active_institute'], 'browser-campus')

    def test_mobile_foreign_revoked_expired_session_denied(self):
        self.mobile()
        for field, value in [('user', 'other'), ('revoked', 1), ('expires_at', 40)]:
            original = getattr(self.doc, field)
            setattr(self.doc, field, value)
            with self.assertRaises(PermissionError): self.module.select('I1')
            setattr(self.doc, field, original)
        self.saved.assert_not_called()

    def test_mobile_choices_read_token_context(self):
        self.mobile()
        self.f.local.il_mobile_institute = 'I1'
        self.f.session.data['il_active_institute'] = 'browser-campus'
        self.f.get_all = MagicMock(return_value=[NS(institute='I1', role='Teacher')])
        self.f.db.get_value.side_effect = lambda dt, *a, **kw: 1 if dt == 'User' else 'Academy'
        self.assertEqual(self.module.choices()['selected'], 'I1')
