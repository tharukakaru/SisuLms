from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch
from test_upload_provisioning import function


class TeacherMembershipScope(TestCase):
    def setUp(self):
        self.actor = NS(user='teacher', role='Teacher')
        self.relationship = NS(kind='Teacher membership', user='teacher', status='Active', profile='profile-B')
        self.write = MagicMock()
        self.f = NS(db=MagicMock(), get_doc=MagicMock(return_value=self.relationship),
                    get_all=MagicMock(side_effect=[['teacher-B'], ['room-B']]), PermissionError=PermissionError)
        self.f.db.get_value.return_value = 'B'
        def throw(message, exc=ValueError): raise exc(message)
        self.f.throw = throw
        p = patch.dict('sys.modules', {
            'institute_lms.api': NS(identity=lambda: (NS(name='A'), self.actor)),
            'institute_lms.campus_teachers': NS(sync=MagicMock()),
            'institute_lms.profiles': NS(write=self.write)})
        p.start(); self.addCleanup(p.stop)
        self.change = function('teaching', 'membership', {'frappe':self.f, 'institute_profile':lambda inst:'profile-A'})

    def test_leaving_other_workspace_cleans_only_target_assignments(self):
        self.change('relationship-B', 'Left')
        calls = self.f.get_all.call_args_list
        self.assertEqual(calls[0].kwargs['filters'], {'user':'teacher','institute':'B','role':'Teacher'})
        self.assertEqual(calls[1].kwargs['filters']['institute'], 'B')
        self.assertEqual(calls[1].kwargs['filters']['public_provider'], 'profile-B')
        self.f.db.set_value.assert_called_once_with('IL Classroom','room-B','teacher_assignment_active',0)

    def test_admin_cannot_remove_other_institute_affiliation(self):
        self.actor.role = 'Admin'
        with self.assertRaises(PermissionError): self.change('relationship-B', 'Removed')
        self.write.assert_not_called()
        self.f.db.set_value.assert_not_called()

    def test_user_cannot_leave_someone_elses_affiliation(self):
        self.relationship.user = 'other-teacher'
        with self.assertRaises(PermissionError): self.change('relationship-B', 'Left')
        self.write.assert_not_called()

    def test_missing_target_workspace_does_not_partially_change_relationship(self):
        self.f.db.get_value.return_value = None
        with self.assertRaises(ValueError): self.change('relationship-B', 'Left')
        self.assertEqual(self.relationship.status, 'Active')
        self.write.assert_not_called()
