import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class OwnerAccessTests(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType('frappe')
        self.f.conf = {'il_owner_email': 'primary@example.test', 'il_owner_provisioned': True}
        self.f.session = types.SimpleNamespace(user='primary@example.test')
        self.f.db = Mock()
        self.f.db.get_value.return_value = 1
        self.f.db.exists.return_value = False
        self.f.PermissionError = PermissionError
        self.f.whitelist = lambda **kw: lambda fn: fn
        def fail(message, kind=ValueError):
            raise kind(message)
        self.f.throw = fail
        self.patch = patch.dict(sys.modules, {'frappe': self.f})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        path = Path(__file__).parents[1] / 'institute_lms/owner_access.py'
        spec = importlib.util.spec_from_file_location('owner_access_under_test', path)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_primary_requires_enabled_user_and_provisioning(self):
        self.assertTrue(self.m.is_owner())
        self.f.db.get_value.return_value = 0
        self.assertFalse(self.m.is_owner())
        self.f.db.get_value.return_value = 1
        self.f.conf['il_owner_provisioned'] = False
        self.assertFalse(self.m.is_owner())

    def test_role_label_does_not_grant_access(self):
        self.f.session.user = 'institute-admin@example.test'
        self.assertFalse(self.m.is_owner())
        with self.assertRaises(PermissionError):
            self.m.require_primary()

    def test_revoked_delegate_loses_access_on_next_request(self):
        self.f.session.user = 'delegate@example.test'
        self.f.db.exists.return_value = True
        self.assertTrue(self.m.is_owner())
        self.f.db.exists.assert_called_with('IL Owner Access', {'user': 'delegate@example.test', 'enabled': 1})
        self.f.db.exists.return_value = False
        self.assertFalse(self.m.is_owner())

    def test_delegate_cannot_manage_access(self):
        self.f.session.user = 'delegate@example.test'
        self.f.db.exists.return_value = True
        with self.assertRaises(PermissionError):
            self.m.add('other@example.test', 'Escalate')
        with self.assertRaises(PermissionError):
            self.m.remove('primary@example.test', 'Remove')

    def test_guest_denied_without_database_lookup(self):
        self.f.session.user = 'Guest'
        self.assertFalse(self.m.is_owner())
        self.f.db.get_value.assert_not_called()
