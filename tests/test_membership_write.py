from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch
from institute_lms.membership_write import authorized_insert, target_for
from test_upload_provisioning import function


class MembershipWrite(TestCase):
    def setUp(self):
        self.doc=NS(institute='B',user='student',role='Student',active=1,name=None,get_doc_before_save=lambda:None)
        self.institute=MagicMock(side_effect=PermissionError('No selected institute'))
        self.count=MagicMock(return_value=0)
        self.quota=MagicMock(side_effect=lambda resource,current:current()+1)
        def throw(message,exc):raise exc(message)
        self.shared=True
        p=patch.dict('sys.modules',{'institute_lms.api':NS(institute=self.institute),
            'institute_lms.campus_context':NS(enabled=lambda:self.shared)})
        p.start();self.addCleanup(p.stop)
        self.validate=function('saas','enforce_member',{'frappe':NS(throw=throw,PermissionError=PermissionError),'quota':self.quota,'current_count':self.count})

    def test_authorized_insert_runs_hook_and_target_counter_without_selection(self):
        with authorized_insert(self.doc):self.validate(self.doc)
        self.institute.assert_not_called()
        self.quota.assert_called_once()
        self.assertEqual(self.count.call_args.args[2],('B','Student',''))
        self.assertIsNone(target_for(self.doc))

    def test_unscoped_insert_cannot_skip_selection(self):
        with self.assertRaises(PermissionError):self.validate(self.doc)

    def test_document_flags_cannot_grant_scope(self):
        self.doc.flags=NS(authorized_insert=True)
        self.assertIsNone(target_for(self.doc))

    def test_other_document_cannot_reuse_scope(self):
        other=NS(**vars(self.doc))
        with authorized_insert(self.doc):self.assertIsNone(target_for(other))

    def test_changed_target_user_or_role_invalidates_scope(self):
        for field,value in [('institute','C'),('user','other'),('role','Admin')]:
            original=getattr(self.doc,field)
            with authorized_insert(self.doc):
                setattr(self.doc,field,value)
                self.assertIsNone(target_for(self.doc))
            setattr(self.doc,field,original)

    def test_failure_clears_scope(self):
        with self.assertRaises(ValueError):
            with authorized_insert(self.doc):raise ValueError('insert failed')
        self.assertIsNone(target_for(self.doc))

    def test_single_site_cannot_use_shared_insert_scope(self):
        self.shared=False
        with authorized_insert(self.doc):
            with self.assertRaises(PermissionError):self.validate(self.doc)
