import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from institute_lms.signup_environment import local_signup_allowed, student_kind_allowed
from test_upload_provisioning import function

class LocalStudentSignup(unittest.TestCase):
    def setUp(self):
        self.config={'il_local_student_signup_enabled':1,'host_name':'http://127.0.0.1:5400','il_student_signup_only':1}

    def test_explicit_loopback_origin_passes(self):
        self.assertTrue(local_signup_allowed(self.config,'http://127.0.0.1:5400/api/method/institute_lms.registration.self_start'))

    def test_flag_is_required(self):
        self.assertFalse(local_signup_allowed({'host_name':self.config['host_name']},self.config['host_name']))

    def test_public_host_cannot_use_local_exception(self):
        for url in ('http://sisuacademylk.com','http://127.0.0.1.example.com','http://192.168.1.5','http://localhost@evil.example'):
            self.assertFalse(local_signup_allowed(dict(self.config,host_name=url),url))

    def test_mismatched_request_and_control_plane_denied(self):
        for url in ('http://127.0.0.1:5401','http://localhost:5400','http://evil.example','http://127.0.0.1:bad'):
            self.assertFalse(local_signup_allowed(self.config,url))
        self.assertFalse(local_signup_allowed(dict(self.config,il_control_plane=1),self.config['host_name']))

    def test_student_only_does_not_grant_provider_signup(self):
        self.assertTrue(student_kind_allowed(self.config,'Student'))
        for kind in ('Individual Teacher','Institute','Admin','Institute Teacher'):
            self.assertFalse(student_kind_allowed(self.config,kind))
        self.assertTrue(student_kind_allowed({},'Individual Teacher'))

    def test_readiness_keeps_email_and_sms_requirements(self):
        def fail(message): raise ValueError(message)
        config=dict(self.config,encryption_key='test',il_sms_adapter='test.adapter',il_self_signup_phone_channel='SMS')
        f=NS(conf=config,local=NS(request=NS(url=self.config['host_name'])),throw=fail,db=NS(exists=lambda *a:True))
        ready=function('public_signup','ready',{'frappe':f,'enabled':lambda:True})
        with patch.dict('sys.modules',{'frappe.utils':NS(get_url=lambda:config['host_name'])}):
            ready()
            config['il_sms_adapter']=''
            with self.assertRaisesRegex(ValueError,'SMS'):ready()
            config['il_sms_adapter']='test.adapter'
            config['encryption_key']=''
            with self.assertRaisesRegex(ValueError,'Email'):ready()

    def test_http_public_site_is_still_rejected(self):
        def fail(message): raise ValueError(message)
        f=NS(conf=self.config,local=NS(request=NS(url='http://public.example')),throw=fail)
        ready=function('public_signup','ready',{'frappe':f,'enabled':lambda:True})
        with patch.dict('sys.modules',{'frappe.utils':NS(get_url=lambda:'http://public.example')}):
            with self.assertRaisesRegex(ValueError,'not available'):ready()
