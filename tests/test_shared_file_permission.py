from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock,patch
from test_upload_provisioning import function


class SharedFilePermission(TestCase):
    def setUp(self):
        self.f=NS(session=NS(user='student'),db=MagicMock(),PermissionError=PermissionError)
        def throw(message,exc):raise exc(message)
        self.f.throw=throw
        self.f.db.exists.return_value=False
        self.room=MagicMock(return_value=(NS(name='B'),NS(role='Student',name='student-B'),NS(name='room-B')))
        self.course=MagicMock()
        p=patch.dict('sys.modules',{'institute_lms.campus_context':NS(enabled=lambda:True),
            'institute_lms.api':NS(accessible_room=self.room)})
        p.start();self.addCleanup(p.stop)
        self.check=function('native_access','file_permission',{'frappe':self.f,'require_course':self.course})
        self.doc=NS(name='file-B',attached_to_doctype='IL Classroom',attached_to_name='room-B')

    def test_foreign_user_permission_check_is_not_session_authority(self):
        with self.assertRaises(PermissionError):self.check(self.doc,user='another-student')
        self.room.assert_not_called()

    def test_foreign_classroom_rejection_propagates(self):
        self.room.side_effect=PermissionError('Foreign institute')
        with self.assertRaises(PermissionError):self.check(self.doc)

    def test_allowed_classroom_does_not_override_framework_permissions(self):
        self.assertIsNone(self.check(self.doc,user='student'))
        self.room.assert_called_once_with('room-B')

    def test_protected_material_requires_viewer_even_for_enrolled_student(self):
        self.f.db.exists.return_value=True
        with self.assertRaises(PermissionError):self.check(self.doc)

    def test_orphan_native_attachment_cannot_skip_course_check(self):
        self.doc.attached_to_doctype='Course Lesson'
        self.f.db.get_value.return_value=None
        with self.assertRaises(PermissionError):self.check(self.doc)
        self.course.assert_not_called()

    def test_native_attachment_checks_resolved_course(self):
        self.doc.attached_to_doctype='Course Lesson'
        self.f.db.get_value.return_value='course-B'
        self.check(self.doc)
        self.course.assert_called_once_with('course-B')
