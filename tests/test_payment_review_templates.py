import importlib.util
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock,patch
from institute_lms.payment_review_rules import review_note,REJECTION_REASONS

class ReviewRules(unittest.TestCase):
    def test_rejection_requires_known_reason(self):
        with self.assertRaises(ValueError):review_note('Rejected','anything','unknown')
        for reason in REJECTION_REASONS[:-1]:self.assertEqual(review_note('Rejected','',reason),reason)
    def test_other_and_approval_require_evidence(self):
        for decision,reason in [('Approved',''),('Rejected','Other')]:
            with self.assertRaises(ValueError):review_note(decision,'',reason)
        self.assertEqual(review_note('Rejected','Wrong payment period','Other'),'Other: Wrong payment period')

class Row(dict):
    def __getattr__(self,key):return self.get(key)

class Templates(unittest.TestCase):
    def setUp(self):
        f=types.ModuleType('frappe');f.whitelist=lambda **kw:lambda fn:fn;f.PermissionError=PermissionError
        f.throw=lambda text,exc=ValueError:(_ for _ in ()).throw(exc(text));f.db=MagicMock();f.db.exists.return_value=True;f.get_all=MagicMock(return_value=[])
        f.conf={'il_whatsapp_token':'test','il_whatsapp_phone_id':'test','il_whatsapp_graph_version':'test','il_whatsapp_event_templates':{e:{'en':{'name':'test','language':'en'}} for e in ['whatsapp.payment_approved','whatsapp.class_scheduled','whatsapp.enrolment_reminder']}}
        self.person=Row(name='S',role='Student',institute='I',active=1,full_name='Demo',user='s@example.invalid',language='en')
        self.payment=Row(name='P',classroom='C',student='S',institute='I',status='Approved');self.room=Row(name='C',title='Maths',active=1);self.account=Row(plan='Gold')
        f.get_doc=lambda doctype,name:self.person if doctype=='IL Member' else self.payment
        self.f=f;api=types.ModuleType('institute_lms.api');api.classroom_for=MagicMock(return_value=(Row(name='I'),Row(role='Teacher'),self.room));self.api=api
        commercial=types.ModuleType('institute_lms.commercial');commercial.account_for=lambda *a:self.account;commercial.locked_reason=lambda a:None;self.commercial=commercial
        notifications=types.ModuleType('institute_lms.notifications');notifications.whatsapp_allowed=lambda person:True;self.notifications=notifications
        service=types.ModuleType('institute_lms.notification_service');service.preference=lambda *a:{'WHATSAPP':True};service.emit=MagicMock(return_value='event');self.service=service
        util=types.ModuleType('frappe.utils');util.now_datetime=lambda:datetime(2026,10,16);util.get_datetime=lambda x:x
        catalogue=types.ModuleType('institute_lms.plan_catalog')
        from institute_lms.commercial_rules import plan_features
        catalogue.plan_features=plan_features
        p=patch.dict(sys.modules,{'institute_lms.plan_catalog':catalogue,'frappe':f,'frappe.utils':util,'institute_lms.api':api,'institute_lms.commercial':commercial,'institute_lms.notifications':notifications,'institute_lms.notification_service':service});p.start();self.addCleanup(p.stop)
        spec=importlib.util.spec_from_file_location('institute_lms.whatsapp_templates',Path(__file__).resolve().parents[1]/'institute_lms/whatsapp_templates.py');self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
    def test_silver_cannot_preview_or_send(self):
        self.account['plan']='Silver'
        with self.assertRaises(PermissionError):self.module.preview('C','S','enrolment_reminder')
        self.service.emit.assert_not_called()
    def test_unassigned_teacher_denied(self):
        self.api.classroom_for.side_effect=PermissionError('Not assigned')
        with self.assertRaises(PermissionError):self.module.options('C')
    def test_student_in_another_class_denied(self):
        self.f.db.exists.return_value=False
        with self.assertRaises(PermissionError):self.module.preview('C','S','enrolment_reminder')
    def test_unapproved_payment_cannot_generate_approval_message(self):
        self.payment['status']='Pending'
        with self.assertRaises(ValueError):self.module.preview('C','S','payment_approved',slip='P')
    def test_consent_rechecked_on_send(self):
        self.notifications.whatsapp_allowed=lambda person:False
        with self.assertRaises(ValueError):self.module.send('C','S','enrolment_reminder','1234567890abcdef')
        self.service.emit.assert_not_called()
    def test_missing_template_blocks_queue(self):
        self.f.conf['il_whatsapp_event_templates']={}
        with self.assertRaises(ValueError):self.module.send('C','S','enrolment_reminder','1234567890abcdef')
        self.service.emit.assert_not_called()
    def test_suspended_provider_blocks(self):
        self.module.locked_reason=lambda a:'Suspended'
        with self.assertRaises(PermissionError):self.module.send('C','S','enrolment_reminder','1234567890abcdef')
    def test_queue_only_whatsapp_and_deduplicates_context(self):
        self.f.db.get_value.return_value='Queued'
        for request_id in ('1234567890abcdef','abcdef1234567890'):self.module.send('C','S','payment_approved',request_id,slip='P')
        calls=self.service.emit.call_args_list
        self.assertEqual(calls[0].args[3],calls[1].args[3]);self.assertEqual(calls[0].kwargs,{'channels':('WHATSAPP',),'classroom':'C'})

if __name__=='__main__':unittest.main()
