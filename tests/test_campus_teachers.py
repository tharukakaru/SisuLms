from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock
from test_upload_provisioning import function


class CampusTeachers(TestCase):
    def setUp(self):
        self.row = None
        self.member = MagicMock()
        self.f = NS(db=MagicMock(), get_doc=MagicMock(return_value=self.member), PermissionError=PermissionError)
        self.f.db.get_value.side_effect = lambda dt,*a,**kw: {'IL Member':self.row,'IL Public Profile':'Test Teacher','User':1,'IL Institute':'TEST'}[dt]
        def throw(message,exc): raise exc(message)
        self.f.throw = throw
        self.enabled = MagicMock(return_value=True)
        self.sync = function('campus_teachers','sync', {'frappe':self.f,'enabled':self.enabled,'make_autoname':lambda pattern:'TC-TEST-0001'})
        self.relationship = NS(user='teacher')

    def test_approval_creates_only_target_teacher_membership(self):
        self.sync(self.relationship,'target','Active')
        data = self.f.get_doc.call_args.args[0]
        self.assertEqual((data['institute'],data['user'],data['role']),('target','teacher','Teacher'))
        self.member.insert.assert_called_once_with(ignore_permissions=True,set_name='TC-TEST-0001')
        self.f.db.commit.assert_not_called()

    def test_removal_deactivates_existing_membership(self):
        self.row = NS(name='target-teacher',role='Teacher')
        self.sync(self.relationship,'target','Removed')
        self.assertEqual(self.member.active,0)
        self.f.get_doc.assert_called_once_with('IL Member','target-teacher')
        self.member.save.assert_called_once_with(ignore_permissions=True)

    def test_other_role_is_not_overwritten(self):
        self.row = NS(name='student',role='Student')
        with self.assertRaises(PermissionError): self.sync(self.relationship,'target','Active')
        self.f.get_doc.assert_not_called()

    def test_repeat_approval_reuses_membership(self):
        self.row = NS(name='target-teacher',role='Teacher')
        self.sync(self.relationship,'target','Active')
        self.assertEqual(self.member.active,1)
        self.member.insert.assert_not_called()

    def test_rejection_never_creates_membership(self):
        self.sync(self.relationship,'target','Rejected')
        self.f.db.sql.assert_not_called()

    def test_disabled_feature_does_not_change_existing_sites(self):
        self.enabled.return_value = False
        self.sync(self.relationship,'target','Active')
        self.f.db.sql.assert_not_called()
