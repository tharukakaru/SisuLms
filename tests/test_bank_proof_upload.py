import io
import types
import unittest
from unittest.mock import Mock, patch
from test_upload_provisioning import function

class ProofUploadTests(unittest.TestCase):
    def setup_upload(self, content=b'proof', owner='student'):
        doc=types.SimpleNamespace(name='new-proof',owner=owner,is_private=1,attached_to_name=None,insert=Mock())
        frappe=types.SimpleNamespace(session=types.SimpleNamespace(user='student'),request=types.SimpleNamespace(files={'file':types.SimpleNamespace(filename='proof.txt',stream=io.BytesIO(content))}),get_doc=Mock(return_value=doc),PermissionError=PermissionError)
        def throw(message,kind=ValueError):raise kind(message)
        frappe.throw=throw
        identity=Mock()
        module=types.ModuleType('institute_lms.api');module.identity=identity
        fn=function('commercial','upload_proof',{'frappe':frappe,'proof_extension':lambda content,name:'txt'})
        return fn,frappe,doc,module
    def test_bytes_create_new_private_owned_record_without_existing_url(self):
        fn,f,doc,module=self.setup_upload()
        with patch.dict('sys.modules',{'institute_lms.api':module}):self.assertEqual(fn(),{'name':'new-proof'})
        data=f.get_doc.call_args.args[0]
        self.assertEqual(data['content'],b'proof');self.assertEqual(data['owner'],'student');self.assertEqual(data['is_private'],1)
        self.assertNotIn('file_url',data);self.assertNotIn('attached_to_name',data)
        doc.insert.assert_called_once_with(ignore_permissions=True)
    def test_rejects_invalid_size_before_file_creation(self):
        for content in (b'',b'x'*(5*1024*1024+1)):
            fn,f,doc,module=self.setup_upload(content)
            with patch.dict('sys.modules',{'institute_lms.api':module}),self.assertRaises(ValueError):fn()
            f.get_doc.assert_not_called()
    def test_cannot_return_another_users_file(self):
        fn,f,doc,module=self.setup_upload(owner='other')
        with patch.dict('sys.modules',{'institute_lms.api':module}),self.assertRaises(PermissionError):fn()
