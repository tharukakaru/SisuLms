from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch
from test_upload_provisioning import function


class SharedMemberDeactivation(TestCase):
    def setUp(self):
        self.shared = True
        self.member = NS(user='student', active=1, save=MagicMock())
        self.account = NS(enabled=1, save=MagicMock())
        self.f = NS(session=NS(user='admin'), get_roles=MagicMock(return_value=[]),
                    get_doc=MagicMock(return_value=self.account), sessions=MagicMock())
        self.f.throw = lambda message: (_ for _ in ()).throw(PermissionError(message))
        self.scope = MagicMock(return_value=self.member)
        self.change = function('api', 'set_member_active', {
            'frappe': self.f, 'identity': lambda: (NS(name='A'), NS(role='Admin')),
            'require_role': MagicMock(), 'scoped': self.scope, 'cint': int})
        p = patch.dict('sys.modules', {'institute_lms.campus_context': NS(enabled=lambda: self.shared)})
        p.start(); self.addCleanup(p.stop)

    def test_shared_deactivation_preserves_account_and_other_sessions(self):
        self.change('member-A', 0)
        self.assertEqual(self.member.active, 0)
        self.member.save.assert_called_once_with(ignore_permissions=True)
        self.f.get_doc.assert_not_called()
        self.f.sessions.clear_sessions.assert_not_called()

    def test_shared_activation_cannot_reenable_platform_disabled_account(self):
        self.account.enabled = 0
        self.change('member-A', 1)
        self.assertEqual(self.account.enabled, 0)
        self.account.save.assert_not_called()

    def test_single_institute_preserves_login_revocation(self):
        self.shared = False
        self.change('member-A', 0)
        self.assertEqual(self.account.enabled, 0)
        self.account.save.assert_called_once_with(ignore_permissions=True)
        self.f.sessions.clear_sessions.assert_called_once_with(user='student', force=True)

    def test_foreign_member_cannot_be_changed(self):
        self.scope.side_effect = PermissionError('Wrong institute')
        with self.assertRaises(PermissionError): self.change('member-B', 0)
        self.member.save.assert_not_called()
        self.f.get_doc.assert_not_called()
