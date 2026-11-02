from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock,patch
from test_upload_provisioning import function


class SharedIdentity(TestCase):
    def setUp(self):
        self.shared=True
        self.member=NS(role='Student',user='learner',name='student-B')
        self.f=NS(session=NS(user='learner'),db=MagicMock(),get_roles=MagicMock(return_value=['System Manager']),
                  PermissionError=PermissionError,AuthenticationError=PermissionError,_dict=lambda **k:NS(**k))
        self.f.db.get_value.return_value=self.member
        def throw(message,exc):raise exc(message)
        self.f.throw=throw
        self.google=MagicMock()
        p=patch.dict('sys.modules',{'institute_lms.campus_context':NS(enabled=lambda:self.shared),
            'institute_lms.portal_policy':NS(require_google_student=self.google)})
        p.start();self.addCleanup(p.stop)
        self.identity=function('api','identity',{'frappe':self.f,'institute':lambda:NS(name='B')})

    def test_system_manager_retains_actual_student_membership(self):
        _,member=self.identity()
        self.assertIs(member,self.member)
        self.assertEqual(member.role,'Student')
        self.google.assert_called_once()

    def test_system_manager_without_membership_is_denied(self):
        self.f.db.get_value.return_value=None
        with self.assertRaises(PermissionError):self.identity()

    def test_membership_query_is_selected_institute_and_active_user(self):
        self.identity()
        self.assertEqual(self.f.db.get_value.call_args.args[1],{'institute':'B','user':'learner','active':1})

    def test_single_institute_operator_behavior_unchanged(self):
        self.shared=False
        _,member=self.identity()
        self.assertEqual(member.role,'Admin')
        self.f.db.get_value.assert_not_called()
