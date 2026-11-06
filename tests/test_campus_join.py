import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch


class StudentJoinTests(TestCase):
    def setUp(self):
        self.student = NS(user='learner', kind='Student', display_name='Learner')
        self.provider = NS(workspace='I2', user='admin', display_name='Institute Two')
        self.phone = NS(phone='+94700000000', verified_at='2026-11-02')
        self.previous = None
        self.member = MagicMock()
        self.f = NS(local=NS(site="test"),db=MagicMock(), PermissionError=PermissionError,
                    whitelist=lambda **kw: lambda fn: fn)
        self.f.throw = lambda message, exc: (_ for _ in ()).throw(exc(message))
        self.f.db.get_value.side_effect = lambda dt, *a, **kw: {
            'IL Verified Phone': self.phone, 'IL Public Profile': self.provider,
            'IL Member': self.previous}[dt]
        self.f.db.exists.return_value = True
        self.f.get_doc = MagicMock(side_effect=lambda arg, *rest: self.member if isinstance(arg, dict) else NS(name='I2', code='TWO'))
        self.require_user = MagicMock(return_value='learner')
        self.allocate = MagicMock(return_value='ST-TWO-00001')
        self.patches = patch.dict('sys.modules', {
            'frappe': self.f, 'frappe.model.naming': NS(make_autoname=self.allocate),
            'institute_lms.campus_context': NS(require_user=self.require_user),
            'institute_lms.profiles': NS(required=lambda: self.student,relate=MagicMock()),
        })
        self.patches.start()
        self.addCleanup(self.patches.stop)
        spec = importlib.util.spec_from_file_location('institute_lms._join_test', Path(__file__).parents[1] / 'institute_lms/campus_join.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_creates_institute_specific_student_number(self):
        result = self.module.register_student('published-profile')
        self.assertEqual(result['student_number'], 'ST-TWO-00001')
        self.allocate.assert_called_once_with('ST-TWO-.#####')
        self.member.insert.assert_called_once_with(ignore_permissions=True, set_name='ST-TWO-00001')
        data = self.f.get_doc.call_args.args[0]
        self.assertEqual((data['doctype'], data['institute'], data['user'], data['role']), ('IL Member', 'I2', 'learner', 'Student'))
        self.f.db.commit.assert_not_called()

    def test_repeat_returns_same_number_without_insert(self):
        self.previous = NS(name='ST-TWO-00001', role='Student', active=1)
        result = self.module.register_student('published-profile')
        self.assertFalse(result['created'])
        self.member.insert.assert_not_called()
        self.allocate.assert_not_called()

    def test_revoked_member_not_reactivated(self):
        self.previous = NS(name='ST-TWO-00001', role='Student', active=0)
        with self.assertRaises(PermissionError): self.module.register_student('published-profile')
        self.member.insert.assert_not_called()

    def test_teacher_cannot_request_student_role(self):
        self.student.kind = 'Teacher'
        with self.assertRaises(PermissionError): self.module.register_student('published-profile')
        self.member.insert.assert_not_called()

    def test_unverified_phone_rejected(self):
        self.phone.verified_at = None
        with self.assertRaises(PermissionError): self.module.register_student('published-profile')
        self.member.insert.assert_not_called()

    def test_unpublished_institute_rejected(self):
        self.provider = None
        with self.assertRaises(PermissionError): self.module.register_student('unknown-profile')
        self.member.insert.assert_not_called()

    def test_feature_gate_runs_before_queries(self):
        self.require_user.side_effect = PermissionError('Disabled')
        with self.assertRaises(PermissionError): self.module.register_student('published-profile')
        self.f.db.get_value.assert_not_called()

    def test_directory_does_not_require_membership_and_bounds_results(self):
        self.f.db.sql.return_value = [{'name': str(i), 'display_name': 'Institute'} for i in range(25)]
        result = self.module.directory("O'Brien", 2)
        self.assertEqual(len(result['institutes']), 24)
        self.assertTrue(result['has_more'])
        query, values = self.f.db.sql.call_args.args
        self.assertEqual(values, ("O'Brien", 48))
        self.assertNotIn("O'Brien", query)
        self.assertIn("p.status='Verified'", query)
        self.assertIn("m.role='Admin' AND m.active=1", query)
        self.assertIn('SELECT p.name, p.display_name', query)
        self.f.db.get_value.assert_not_called()

    def test_directory_rejects_invalid_paging_before_query(self):
        for page in (-1, 1001, 'invalid', None):
            with self.assertRaises(PermissionError): self.module.directory('', page)
        self.f.db.sql.assert_not_called()

    def test_directory_disabled_before_query(self):
        self.require_user.side_effect = PermissionError('Disabled')
        with self.assertRaises(PermissionError): self.module.directory()
        self.f.db.sql.assert_not_called()
