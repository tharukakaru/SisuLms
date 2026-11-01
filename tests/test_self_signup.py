import unittest, time, sys, types, importlib
from unittest.mock import MagicMock, patch
from institute_lms import signup_rules as rules

class SignupRules(unittest.TestCase):
    def form(self,kind='Student'):
        return dict(kind=kind,first_name='Test',last_name='Person',email='test@example.com',phone='+94741575022',username='testperson',country='LK',timezone='UTC',grade='Adult',subject='Maths',organization='Test Institute',job='Owner',backup_name='Recovery',backup_email='recovery@example.com',privacy_accepted=True)
    def test_required_fields_for_every_role(self):
        for role,extras in rules.EXTRA.items():
            for field in (*rules.COMMON,*extras):
                data=self.form(role);data[field]=' '
                with self.subTest(role=role,field=field),self.assertRaises(ValueError):rules.details(data)
    def test_client_privileges_and_verification_ignored(self):
        data=self.form();data.update(roles=['System Manager'],email_verified=True,phone_verified=True,password='secret')
        result=rules.details(data)
        for field in ('roles','email_verified','phone_verified','password'):self.assertNotIn(field,result)
        data['kind']='Super Admin'
        with self.assertRaises(ValueError):rules.details(data)
    def test_contact_and_consent_validation(self):
        for field,value in [('email','x\r\nBcc:a@b.c'),('phone','0741575022'),('privacy_accepted',False),('username','admin'),('timezone','../secret')]:
            data=self.form();data[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):rules.details(data)
    def test_password_confirmation(self):
        for value,confirmation in [('short','short'),('long enough password','different'),('x'*129,'x'*129)]:
            with self.assertRaises(ValueError):rules.password(value,confirmation)
        rules.password('Long example password','Long example password')
    def test_both_proofs_and_fresh_session_required(self):
        good=dict(expires=20,email_verified=True,phone_verified=True)
        self.assertTrue(rules.verified(good,10))
        for changes in ({'email_verified':False},{'phone_verified':False},{'consumed':True},{'expires':10}):self.assertFalse(rules.verified({**good,**changes},10))

class SignupOTP(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.conf=types.SimpleNamespace(encryption_key='test-only');self.f.cache=MagicMock()
        self.f.throw=lambda message:(_ for _ in ()).throw(ValueError(message))
        self.modules=patch.dict(sys.modules,{'frappe':self.f});self.modules.start()
        self.old=sys.modules.pop('institute_lms.self_signup',None)
        self.api=importlib.import_module('institute_lms.self_signup');self.ready=patch.object(self.api,'require_ready');self.ready.start()
        self.token='x'*32;self.state=dict(expires=time.time()+100,email_expires=time.time()+60,email_attempts=0,email_verified=False,phone_verified=False)
        self.state['email_digest']=self.api.digest(self.token,'email','123456');self.f.cache.get_value.return_value=self.state
    def tearDown(self):
        self.ready.stop();sys.modules.pop('institute_lms.self_signup',None)
        if self.old:sys.modules['institute_lms.self_signup']=self.old
        self.modules.stop()
    def test_invalid_codes_exhaust_after_five_attempts(self):
        for _ in range(5):
            with self.assertRaises(ValueError):self.api.verify(self.token,'email','999999')
        with self.assertRaises(ValueError):self.api.verify(self.token,'email','123456')
        self.assertFalse(self.state['email_verified'])
    def test_expired_code_rejected(self):
        self.state['email_expires']=0
        with self.assertRaises(ValueError):self.api.verify(self.token,'email','123456')
    def test_proof_bound_to_contact_channel(self):
        self.assertTrue(self.api.verify(self.token,'email','123456')['verified'])
        self.assertFalse(self.state['phone_verified'])
        self.assertNotEqual(self.api.digest(self.token,'phone','123456'),self.state['email_digest'])
    def test_missing_phone_proof_cannot_create_account(self):
        self.f.session=types.SimpleNamespace(user='Guest');self.f.get_doc=MagicMock()
        self.state['email_verified']=True
        with self.assertRaises(ValueError):self.api.complete(self.token,'Long example password','Long example password')
        self.f.get_doc.assert_not_called()

    def test_google_signup_requires_same_authenticated_identity(self):
        self.f.session=types.SimpleNamespace(user='google@example.com',data={'il_google_session':1})
        self.f.db=MagicMock();self.f.db.exists.return_value=False
        self.assertTrue(self.api.google_identity('google@example.com'))
        self.assertFalse(self.api.google_identity('other@example.com'))
        self.f.session.data={}
        self.assertFalse(self.api.google_identity('google@example.com'))
    def test_google_cannot_replace_an_existing_member_or_profile(self):
        self.f.session=types.SimpleNamespace(user='google@example.com',data={'il_google_session':1})
        self.f.db=MagicMock();self.f.db.exists.return_value=True
        self.assertFalse(self.api.google_identity('google@example.com'))
    def test_test_contacts_are_bound_to_selected_role(self):
        self.f.conf={'il_self_signup_test_email':'student@example.com','il_self_signup_test_phone':'+94711111111','il_self_signup_role_emails':{'Individual Teacher':'teacher@example.com','Institute':'institute@example.com'}}
        self.assertTrue(self.api.test_contact(dict(kind='Individual Teacher',email='teacher@example.com',phone='+94711111111')))
        self.assertFalse(self.api.test_contact(dict(kind='Institute',email='teacher@example.com',phone='+94711111111')))
        self.assertFalse(self.api.test_contact(dict(kind='Individual Teacher',email='teacher@example.com',phone='+94722222222')))
