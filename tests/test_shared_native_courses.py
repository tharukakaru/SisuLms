from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch
from test_upload_provisioning import function


class SharedNativeCourses(TestCase):
    def setUp(self):
        self.shared=True
        self.f=NS(get_all=MagicMock(return_value=['room']),get_doc=MagicMock(
            return_value=NS(active=1,fee_mode='Free',as_dict=lambda:{})),PermissionError=PermissionError)
        def throw(message,exc):raise exc(message)
        self.f.throw=throw
        self.checked=MagicMock(return_value=('institute','member','room'))
        self.access=MagicMock(return_value={'allowed':True})
        p=patch.dict('sys.modules',{
            'institute_lms.campus_context':NS(enabled=lambda:self.shared),
            'institute_lms.api':NS(classroom_for=self.checked,access=self.access),
            'institute_lms.saas':NS(require=MagicMock()),
            'institute_lms.retention':NS(access_allowed=lambda room:True),
            'institute_lms.commercial':NS(account_for=lambda *a:None)})
        p.start();self.addCleanup(p.stop)
        self.read=function('native_access','require_course',{'frappe':self.f})

    def test_free_course_still_requires_scoped_classroom_access(self):
        self.read('course')
        self.checked.assert_called_once_with('room')
        self.access.assert_called_once_with('room','member')

    def test_foreign_free_course_denied(self):
        self.checked.side_effect=PermissionError('Foreign institute')
        with self.assertRaises(PermissionError):self.read('course')
        self.access.assert_not_called()

    def test_unenrolled_student_denied(self):
        self.access.return_value={'allowed':False}
        with self.assertRaises(PermissionError):self.read('course')

    def test_unlinked_native_course_denied_in_shared_mode(self):
        self.f.get_all.return_value=[]
        with self.assertRaises(PermissionError):self.read('course')

    def test_single_institute_free_course_behavior_preserved(self):
        self.shared=False
        self.read('course')
        self.checked.assert_not_called()
