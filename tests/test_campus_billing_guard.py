from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch
from test_upload_provisioning import function


class CampusBillingGuard(TestCase):
    def setUp(self):
        self.f = NS(conf={},session=NS(user='student'),form_dict={},
                    local=NS(request=NS(path='/api/method/placeholder')), db=MagicMock(), PermissionError=PermissionError)
        def throw(message,exc): raise exc(message)
        self.f.throw = throw
        self.institute = MagicMock(side_effect=PermissionError('No institute selected'))
        p = patch.dict('sys.modules',{'institute_lms.api':NS(institute=self.institute)})
        p.start();self.addCleanup(p.stop)
        self.state = MagicMock(return_value={'available':False})
        self.guard = function('account_billing','guard_request',{'frappe':self.f,'privileged':lambda:False,'state':self.state,'account':MagicMock()})

    def test_context_free_endpoints_reach_their_own_guards(self):
        for endpoint in ('campus_context.choices','campus_context.select','campus_context.clear',
                         'campus_join.directory','campus_join.details','campus_join.register_student'):
            self.f.form_dict['cmd']='institute_lms.'+endpoint
            self.guard()
        self.institute.assert_not_called()

    def test_unknown_campus_method_is_not_exempt(self):
        self.f.form_dict['cmd']='institute_lms.campus_join.unreviewed_method'
        with self.assertRaises(PermissionError):self.guard()
        self.institute.assert_called_once()

    def test_classroom_access_still_requires_selected_institute(self):
        self.f.form_dict['cmd']='institute_lms.api.classroom_detail'
        with self.assertRaises(PermissionError):self.guard()

    def test_selected_unpaid_member_still_denied_class_access(self):
        self.institute.side_effect=None
        self.institute.return_value=NS(name='A')
        self.f.db.get_value.return_value=NS(role='Student',user='student')
        self.f.form_dict['cmd']='institute_lms.api.classroom_detail'
        with self.assertRaises(PermissionError):self.guard()
        self.state.assert_called_once()
