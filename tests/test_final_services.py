"""Service boundary tests with an explicit Frappe double, not DB acceptance."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

class Row(dict):
    def __getattr__(self,k):return self.get(k)

class Boundaries(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.PermissionError=PermissionError;self.f.db=MagicMock();self.f.get_doc=MagicMock()
        self.f.conf=Row();self.f.session=Row(user='student');self.f.get_attr=MagicMock()
        self.f.throw=lambda message,exc=ValueError:(_ for _ in ()).throw(exc(message))
        u=types.ModuleType('frappe.utils');u.now_datetime=lambda:datetime(2026,10,6);u.get_datetime=lambda x:x;u.get_url=lambda:'https://tenant.example'
        self.inst=Row(name='I');self.member=Row(user='student',name='M',role='Student');self.room=Row(name='C',institute='I',teacher='T',owner_user='teacher')
        self.api=types.ModuleType('institute_lms.api');self.api.identity=lambda:(self.inst,self.member)
        self.api.accessible_room=MagicMock(return_value=(self.inst,self.member,self.room))
        self.api.classroom_for=MagicMock(return_value=(self.inst,self.member,self.room))
        saas=types.ModuleType('institute_lms.saas');saas.managed=lambda x:x;saas.audit=MagicMock()
        self.modules=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':u,'institute_lms.api':self.api,'institute_lms.saas':saas})
        self.modules.start();self.addCleanup(self.modules.stop)
    def load(self,name):
        spec=importlib.util.spec_from_file_location('institute_lms.'+name,Path(__file__).resolve().parents[1]/'institute_lms'/f'{name}.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def test_foreign_lecture_denied(self):
        self.f.get_doc.return_value=Row(institute='OTHER')
        with self.assertRaises(PermissionError):self.load('lectures').checked('foreign')
    def test_live_listing_filters_authorized_class_before_query_limit(self):
        self.api.room_filters=lambda *a: {'institute':'I'}
        self.f.get_all=MagicMock(side_effect=[['C','OTHER'],[]])
        self.load('live_classes').listing(classroom='C')
        self.api.accessible_room.assert_called_once_with('C')
        self.assertEqual(self.f.get_all.call_args.kwargs['filters']['classroom'],['in',['C']])
    def test_live_listing_denies_locked_class(self):
        self.api.room_filters=lambda *a: {}
        self.f.get_all=MagicMock(return_value=['C'])
        self.api.accessible_room.side_effect=PermissionError('Payment required')
        with self.assertRaises(PermissionError):self.load('live_classes').listing(classroom='C')
        self.assertEqual(self.f.get_all.call_count,1)
    def test_lecture_listing_filters_class_before_query_limit(self):
        self.api.require_role=MagicMock()
        self.f.get_all=MagicMock(return_value=[])
        self.load('lectures').listing(classroom='C')
        self.api.accessible_room.assert_called_once_with('C')
        sql,params=self.f.db.sql.call_args.args
        self.assertIn('institute=%s',sql)
        self.assertIn('`classroom`=%s',sql)
        self.assertIn('`status`=%s',sql)
        self.assertEqual(params,('I','C','Published'))
        self.assertLess(sql.index('`classroom`=%s'),sql.index('LIMIT 100'))
    def test_lecture_listing_denies_locked_class(self):
        self.api.require_role=MagicMock()
        self.f.get_all=MagicMock()
        self.api.accessible_room.side_effect=PermissionError('Payment required')
        with self.assertRaises(PermissionError):self.load('lectures').listing(classroom='C')
        self.f.get_all.assert_not_called()
    def test_purchase_history_keeps_user_and_class_filters(self):
        self.f.get_all=MagicMock(side_effect=[['P1'],[]])
        self.load('lectures').history(classroom='C')
        self.api.accessible_room.assert_called_once_with('C')
        filters=self.f.get_all.call_args.kwargs['filters']
        self.assertEqual(filters,{'institute':'I','user':'student','product':['in',['P1']]})
    def test_unpurchased_paid_video_never_reaches_provider(self):
        self.f.get_doc.return_value=Row(institute='I',price_minor=100,status='Published')
        m=self.load('lectures');m.owned=lambda *a:None
        with self.assertRaises(PermissionError):m.playback('paid')
        self.f.get_attr.assert_not_called()
    def test_student_cannot_control_live_room(self):
        self.f.get_doc.return_value=Row(institute='I',classroom='C')
        with self.assertRaises(PermissionError):self.load('live_classes').checked('L',True)
    def test_named_teacher_can_control_live_room(self):
        self.member.update(user='teacher',name='T',role='Teacher')
        self.f.get_doc.return_value=Row(institute='I',classroom='C')
        self.assertEqual(self.load('live_classes').checked('L',True)[1].name,'T')
    def test_cross_tenant_live_denied(self):
        self.f.get_doc.return_value=Row(institute='OTHER',classroom='C')
        with self.assertRaises(PermissionError):self.load('live_classes').checked('L')
    def test_not_live_does_not_issue_token(self):
        self.f.get_doc.return_value=Row(institute='I',classroom='C',status='Upcoming')
        with self.assertRaisesRegex(ValueError,'not active'):self.load('live_classes').join('L')
    def test_unsupported_recording_cannot_be_published(self):
        self.member.update(user='teacher',name='T',role='Teacher')
        self.f.get_doc.return_value=Row(institute='I',classroom='C',recording_status='Processing')
        with self.assertRaisesRegex(ValueError,'not ready'):self.load('live_classes').lecture_draft('L')
    def test_playback_binds_confirmed_storage_version(self):
        m=self.load('private_media');provider=MagicMock();m.client=lambda:(provider,'private-bucket')
        self.f.db.get_value.return_value=Row(backend='s3_media',media_state='Ready',storage_version='immutable-version')
        m.grant('object','teacher')
        self.assertEqual(provider.generate_presigned_url.call_args.kwargs['Params']['VersionId'],'immutable-version')
    def test_unversioned_uploaded_media_is_not_served(self):
        m=self.load('private_media');provider=MagicMock();m.client=lambda:(provider,'private-bucket')
        self.f.db.get_value.return_value=Row(backend='s3_media',media_state='Ready',storage_version=None)
        with self.assertRaisesRegex(ValueError,'version'):m.grant('object','teacher')
        provider.generate_presigned_url.assert_not_called()
    def test_confirmed_upload_cannot_be_rebound(self):
        teaching=types.ModuleType('institute_lms.teaching');teaching.require=MagicMock()
        with patch.dict(sys.modules,{'institute_lms.teaching':teaching}):
            m=self.load('private_media');m.client=MagicMock()
            self.f.get_doc.return_value=Row(institute='I',classroom='C',owner_user='student',backend='s3_media',status='ACTIVE',media_state='Ready',storage_key='original')
            self.assertEqual(m.complete('object')['media_key'],'original');m.client.assert_not_called()

    def test_pending_r2_upload_cannot_be_played(self):
        m=self.load('private_media');provider=MagicMock();m.client=lambda:(provider,'private-bucket')
        self.f.db.get_value.return_value=Row(backend='r2_media',media_state='Uploading',storage_version=None)
        with self.assertRaisesRegex(ValueError,'Complete'):m.grant('object','teacher')
        provider.generate_presigned_url.assert_not_called()
    def test_r2_playback_uses_confirmed_immutable_key_without_s3_version(self):
        m=self.load('private_media');provider=MagicMock();m.client=lambda:(provider,'private-bucket')
        self.f.db.get_value.return_value=Row(backend='r2_media',media_state='Ready',storage_version='etag')
        m.grant('object','teacher')
        self.assertNotIn('VersionId',provider.generate_presigned_url.call_args.kwargs['Params'])
