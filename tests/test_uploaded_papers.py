"""Uploaded-paper service tests with mocks only; never initializes a site."""
import importlib
import json
import sys
import types
import unittest
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch
from zipfile import ZipFile
from test_materials import MaterialAuthorization, Record
from institute_lms.material_contract import validate_file, MAX_BYTES


class UploadedPaperValidation(unittest.TestCase):
    def test_supported_documents_and_size(self):
        for ext in ('pdf','txt','doc','ppt','xls'):
            raw=b'%PDF-1.7' if ext=='pdf' else b'Lesson' if ext=='txt' else bytes.fromhex('D0CF11E0A1B11AE1')
            self.assertEqual(validate_file('paper.'+ext,raw,paper=True)[0],ext)
        for name,body in [('a.html',b'<script/>'),('a.svg',b'<svg/>'),('a.xls',b'not excel'),('a.txt',b'\xff'),('a.pdf',b'%PDF-'+b'0'*MAX_BYTES)]:
            with self.assertRaises(ValueError):validate_file(name,body,paper=True)
        with self.assertRaises(ValueError):validate_file('a.xls',bytes.fromhex('D0CF11E0A1B11AE1'))

    def test_excel_container_and_macro_validation(self):
        def workbook(extra=None):
            data=BytesIO()
            with ZipFile(data,'w') as z:
                z.writestr('[Content_Types].xml','<Types/>');z.writestr('xl/workbook.xml','<workbook/>')
                if extra:z.writestr(extra,'bad')
            return data.getvalue()
        self.assertEqual(validate_file('a.xlsx',workbook(),paper=True)[0],'xlsx')
        for extra in ('xl/vbaProject.bin','../file'):
            with self.assertRaises(ValueError):validate_file('a.xlsx',workbook(extra),paper=True)
        with self.assertRaises(ValueError):validate_file('a.docx',workbook(),paper=True)

    def test_image_bytes_verified_not_just_extension(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow unavailable in this test interpreter')
        data=BytesIO();Image.new('RGB',(2,2)).save(data,format='PNG')
        self.assertEqual(validate_file('image.png',data.getvalue(),paper=True)[0],'png')
        for filename,raw in [('fake.png',b'<html/>'),('wrong.jpg',data.getvalue())]:
            with self.assertRaises(ValueError):validate_file(filename,raw,paper=True)


class UploadedPaperAccess(MaterialAuthorization):
    def setUp(self):
        super().setUp()
        self.f.db=MagicMock();self.f.db.sql.return_value=[];self.f.db.count.return_value=0
        self.f.get_all=MagicMock(return_value=[])
        self.mod.now_datetime=lambda:datetime(2026,10,30)
        self.mod.accessible_room.return_value=(Record(name='A'),Record(role='Student'),self.room)
        self.teaching=types.ModuleType('institute_lms.teaching');self.teaching.require=MagicMock()
        self.modules=patch.dict(sys.modules,{'institute_lms.teaching':self.teaching})
        self.modules.start();self.addCleanup(self.modules.stop)

    def upload(self):
        self.mod.accessible_room.return_value=(Record(name='A'),Record(role='Teacher'),self.room)
        return self.mod.upload_paper('room-A','Paper','12345678-1234-1234-1234-123456789abc','Instructions')

    def test_student_direct_private_file_url_is_blocked(self):
        import ast
        from pathlib import Path
        tree=ast.parse((Path(__file__).resolve().parents[1]/'institute_lms/native_access.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='file_permission')
        env={'frappe':self.f,'__name__':'institute_lms.native_access','__package__':'institute_lms'}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'native_access.py','exec'),env)
        self.f.db.exists.return_value=True
        with self.assertRaises(PermissionError):
            env['file_permission'](Record(name='file',attached_to_doctype='IL Classroom',attached_to_name='room-A'))

    def test_authorized_upload_is_classroom_scoped_and_downloadable(self):
        with patch.object(self.mod,'store_upload',return_value={'file_id':'private-file','filename':'paper.pdf','file_type':'pdf','file_size':100}) as store:
            result=self.upload()
        self.teaching.require.assert_called_once_with(self.room,self.mod.accessible_room.return_value[1],'edit')
        store.assert_called_once_with(self.room,paper=True)
        document=self.f.get_doc.call_args.args[0]
        self.assertEqual(document['institute'],'A');self.assertEqual(document['classroom'],'room-A')
        self.assertEqual(document['download_policy'],'Downloadable');self.assertEqual(document['url'],'')
        self.assertTrue(result['name'].startswith('paper-upload-'))

    def test_shared_storage_keeps_file_private(self):
        file_manager=types.ModuleType('frappe.utils.file_manager');file_manager.save_file=MagicMock(return_value=Record(name='file-1'))
        self.f.request=Record(files={'file':Record(filename='paper.pdf',stream=BytesIO(b'%PDF-1.7'))})
        with patch.dict(sys.modules,{'frappe.utils.file_manager':file_manager}):
            self.mod.store_upload(self.room,paper=True)
        self.assertEqual(file_manager.save_file.call_args.kwargs['is_private'],1)
        self.assertEqual(file_manager.save_file.call_args.args[2:],('IL Classroom','room-A'))

    def test_unauthorized_teacher_cannot_store_file(self):
        self.teaching.require.side_effect=PermissionError('Management required')
        with patch.object(self.mod,'store_upload') as store:
            with self.assertRaises(PermissionError):self.upload()
            store.assert_not_called()

    def test_retry_is_idempotent(self):
        self.f.db.sql.side_effect=lambda sql,args:[('existing',)] if 'tabIL Material' in sql else []
        with patch.object(self.mod,'store_upload') as store:
            self.assertTrue(self.upload()['uploaded']);store.assert_not_called()

    def test_title_validation_precedes_storage(self):
        with patch.object(self.mod,'store_upload') as store:
            with self.assertRaises(ValueError):self.mod.upload_paper('room-A',' ','12345678-1234-1234-1234-123456789abc')
            store.assert_not_called()

    def test_enrolled_student_list_scoped_without_private_urls(self):
        self.mod.accessible_room.return_value=(Record(name='A'),Record(role='Student'),self.room)
        self.f.get_all.return_value=[Record(name='paper-upload-1',expires_at=None)]
        self.assertEqual(len(self.mod.paper_listing('room-A')),1)
        args=self.f.get_all.call_args.kwargs
        self.assertEqual(args['filters']['institute'],'A');self.assertEqual(args['filters']['classroom'],'room-A')
        self.assertNotIn('url',args['fields']);self.assertNotIn('file_id',args['fields'])

    def test_unenrolled_or_foreign_classroom_list_rejected(self):
        self.mod.accessible_room.side_effect=PermissionError('Classroom unavailable')
        with self.assertRaises(PermissionError):self.mod.paper_listing('room-B')
        self.f.get_all.assert_not_called()

    def test_student_download_and_text_preview_use_access_gate(self):
        self.mod.accessible_room.return_value=(Record(name='A'),Record(role='Student'),self.room)
        self.f.get_doc.return_value=Record(name='paper-upload-1',classroom='room-A',file_type='txt',filename='paper.txt',file_id='file',download_policy='Downloadable')
        with patch.object(self.mod,'checked_file',return_value=(Record(file_name='paper.txt'),MagicMock(read_bytes=lambda:b'<script>text only</script>'))):
            for action in ('view','download'):
                self.mod.content('paper-upload-1',action)
                self.assertEqual(self.f.local.response['content_type'],'text/plain')
                self.assertEqual(self.f.local.response_headers['X-Content-Type-Options'],'nosniff')

    def test_foreign_institute_download_denied(self):
        self.f.get_doc.return_value=Record(name='paper-upload-1',classroom='room-A')
        with patch.object(self.mod,'scoped',side_effect=PermissionError('Foreign institute')):
            with patch.object(self.mod,'checked_file') as read:
                with self.assertRaises(PermissionError):self.mod.content('paper-upload-1','download')
                read.assert_not_called()
