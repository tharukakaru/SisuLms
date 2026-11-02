from types import SimpleNamespace as NS
from urllib.parse import unquote
from unittest import TestCase
from unittest.mock import MagicMock,patch
from test_upload_provisioning import function


class SharedNativeGuard(TestCase):
    def setUp(self):
        self.shared=True
        self.f=NS(conf={},session=NS(user='student'),form_dict={},db=MagicMock(),
            local=NS(request=NS(path='/api/resource/IL%20Member')),
            get_roles=MagicMock(return_value=[]),PermissionError=PermissionError)
        self.f.db.exists.return_value=False
        def throw(message,exc):raise exc(message)
        self.f.throw=throw
        self.course=MagicMock()
        p=patch.dict('sys.modules',{'institute_lms.campus_context':NS(enabled=lambda:self.shared)})
        p.start();self.addCleanup(p.stop)
        self.guard=function('native_access','guard',{'frappe':self.f,'unquote':unquote,
            'SAFE':{'login','logout'},'READERS':{'lms.read'},'require_course':self.course})

    def test_empty_shared_site_still_denies_generic_resource_api(self):
        with self.assertRaises(PermissionError):self.guard()

    def test_system_manager_cannot_bypass_shared_resource_guard(self):
        self.f.get_roles.return_value=['System Manager']
        with self.assertRaises(PermissionError):self.guard()

    def test_administrator_cannot_bypass_shared_resource_guard(self):
        self.f.session.user='Administrator'
        with self.assertRaises(PermissionError):self.guard()

    def test_scoped_native_reader_still_checks_course(self):
        self.f.form_dict={'cmd':'lms.read','course':'course-B'}
        self.guard()
        self.course.assert_called_once_with('course-B')

    def test_foreign_progress_identity_denied(self):
        self.f.form_dict={'cmd':'lms.read','course':'course-B','member':'another-student'}
        with self.assertRaises(PermissionError):self.guard()
        self.course.assert_not_called()

    def test_sisu_endpoints_reach_their_own_guards(self):
        self.f.form_dict={'cmd':'institute_lms.campus_join.directory'}
        self.guard()

    def test_single_site_operator_behavior_preserved(self):
        self.shared=False
        self.f.get_roles.return_value=['System Manager']
        self.guard()
