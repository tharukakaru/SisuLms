from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch
from institute_lms.campus_provisioning import institute_insert, allows
from test_upload_provisioning import function


class CampusProvisioning(TestCase):
    def setUp(self):
        self.shared=True
        self.doc=NS(code='TESTB',name=None,is_new=lambda:True)
        def throw(message):raise PermissionError(message)
        f=NS(db=NS(exists=MagicMock(return_value=True)),throw=throw)
        p=patch.dict('sys.modules',{'institute_lms.campus_context':NS(enabled=lambda:self.shared)})
        p.start();self.addCleanup(p.stop)
        self.validate=function('validation','validate_institute',{'frappe':f,'institute_code':lambda code:code})

    def test_authorized_shared_insert(self):
        with institute_insert(self.doc):self.validate(self.doc)
        self.assertFalse(allows(self.doc))

    def test_unscoped_shared_insert_rejected(self):
        with self.assertRaises(PermissionError):self.validate(self.doc)

    def test_single_site_remains_single_site(self):
        self.shared=False
        with institute_insert(self.doc):
            with self.assertRaises(PermissionError):self.validate(self.doc)

    def test_other_document_or_changed_code_rejected(self):
        with institute_insert(self.doc):
            self.assertFalse(allows(NS(**vars(self.doc))))
            self.doc.code='OTHER'
            self.assertFalse(allows(self.doc))

    def test_scope_cleared_after_failure(self):
        with self.assertRaises(ValueError):
            with institute_insert(self.doc):raise ValueError('failed')
        self.assertFalse(allows(self.doc))

    def test_existing_institute_cannot_use_insert_scope(self):
        self.doc.is_new=lambda:False
        with institute_insert(self.doc):self.assertFalse(allows(self.doc))
