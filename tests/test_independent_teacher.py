import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch


class PersonalTeacherWorkspace(unittest.TestCase):
    def setUp(self):
        self.provider = NS(kind='Teacher', status='Verified', user='teacher', workspace='personal')
        self.f = NS(db=MagicMock(), get_all=MagicMock(), get_doc=MagicMock(), PermissionError=ValueError)
        self.f.throw = lambda text, *args: (_ for _ in ()).throw(ValueError(text))
        self.f.db.exists.return_value = False
        self.f.db.get_value.return_value = None
        self.f.get_all.return_value = [NS(user='teacher', role='Teacher')]
        scope = patch.dict(sys.modules, {'frappe': self.f})
        scope.start(); self.addCleanup(scope.stop)
        spec = importlib.util.spec_from_file_location('institute_lms._independent_test',
            Path(__file__).parents[1] / 'institute_lms/independent_teacher.py')
        self.mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)

    def test_explicit_personal_workspace_allowed(self):
        self.assertEqual(self.mod.workspace(self.provider), 'personal')

    def test_missing_binding_not_inferred_from_teacher_membership(self):
        self.provider.workspace = None
        self.assertIsNone(self.mod.workspace(self.provider))
        self.f.get_all.assert_not_called()

    def test_institute_profile_blocks_personal_registration(self):
        self.f.db.exists.return_value = True
        self.assertIsNone(self.mod.workspace(self.provider))

    def test_admin_other_teacher_or_missing_owner_blocks_scope(self):
        for staff in ([], [NS(user='teacher', role='Admin')],
                      [NS(user='other', role='Teacher')],
                      [NS(user='teacher', role='Teacher'), NS(user='other', role='Admin')]):
            with self.subTest(staff=staff):
                self.f.get_all.return_value = staff
                self.assertIsNone(self.mod.workspace(self.provider))

    def test_revoked_or_different_role_membership_not_reactivated(self):
        for active, role in ((0, 'Student'), (1, 'Teacher'), (1, 'Admin')):
            self.f.db.get_value.return_value = NS(name='existing', active=active, role=role)
            with self.assertRaises(ValueError):
                self.mod.register_member(self.provider, NS(user='student'), '+94000', 'ST-IND-1')
        self.f.get_doc.assert_not_called()

    def test_retry_reuses_existing_student(self):
        self.f.db.get_value.return_value = NS(name='existing', active=1, role='Student')
        self.assertEqual(self.mod.register_member(self.provider, NS(user='student'), '+94000', 'new'), 'existing')
        self.f.get_doc.assert_not_called()

    def test_new_membership_only_in_bound_workspace(self):
        member = NS(institute='personal', user='student', role='Student', name='ST-IND-1', insert=MagicMock())
        self.f.get_doc.return_value = member
        number = self.mod.register_member(self.provider, NS(user='student', display_name='Test'), '+94000', 'ST-IND-1')
        self.assertEqual(number, 'ST-IND-1')
        data = self.f.get_doc.call_args.args[0]
        self.assertEqual((data['institute'], data['user'], data['role']), ('personal', 'student', 'Student'))
        member.insert.assert_called_once_with(ignore_permissions=True, set_name='ST-IND-1')
