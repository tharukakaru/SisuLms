import hashlib,json,time
from contextlib import nullcontext
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
from test_upload_provisioning import function
from institute_lms import signup_rules
class Record:
    def __init__(self,data):object.__setattr__(self,'data',data)
    def __getattr__(self,key):return self.data.get(key)
    def __setattr__(self,key,value):self.data[key]=value
    def update(self,values):self.data.update(values)
    def insert(self,**kwargs):return self
    def save(self,**kwargs):return self

class PublicAccountCompletion(TestCase):
    def setUp(self):
        self.data=dict(kind='Student',email='student@example.invalid',phone='+94761234567',first_name='Test',last_name='Student',username='test_student',country='Sri Lanka',birth_date='2005-02-28',bio='',qualifications='',privacy_policy_url='/privacy',privacy_policy_version='v1')
        self.state=dict(flow='public-account-v1',details=self.data,expires=time.time()+600,email_verified=True,phone_verified=True)
        self.docs=[]
        def doc(data):
            self.docs.append(data)
            return Record(data)
        def fail(message):raise ValueError(message)
        self.f=NS(session=NS(user='Guest'),cache=NS(lock=lambda *a,**k:nullcontext()),db=NS(exists=Mock(return_value=False),get_value=Mock(return_value=None),commit=Mock()),get_doc=doc,throw=fail)
        self.challenges=NS(key=lambda t:t,store=Mock(),google_identity=Mock(return_value=False))
        self.registered=Mock(return_value=False)
        self.complete=function('public_signup','complete',dict(frappe=self.f,ready=lambda:None,rules=signup_rules,read=lambda t:self.state,time=time,hashlib=hashlib,json=json,challenges=self.challenges,google_identity=self.challenges.google_identity,registered_google_account=self.registered))
        self.modules=patch.dict('sys.modules',{'institute_lms.account_confirmations':NS(queue=Mock()),'institute_lms.portal_policy':NS(public=lambda:{'privacy_policy_url':'/privacy','privacy_policy_version':'v1'}),'institute_lms.profiles':NS(write=Mock()),'frappe.utils':NS(now_datetime=lambda:'now')})
        self.modules.start();self.addCleanup(self.modules.stop)
    def test_all_account_types_create_identity_without_workspace_privileges(self):
        for kind in ('Student','Individual Teacher','Institute'):
            with self.subTest(kind=kind):
                self.docs.clear();self.state.pop('consumed',None);self.data['kind']=kind
                self.assertTrue(self.complete('token','a-password-123','a-password-123')['created'])
                self.assertEqual([d['doctype'] for d in self.docs],['User','IL Verified Phone','IL Public Profile','IL Registration Request'])
                user=self.docs[0];self.assertEqual(user['user_type'],'Website User');self.assertNotIn('roles',user)
                self.assertEqual(user.get('birth_date'),'2005-02-28' if kind=='Student' else None)
                profile=self.docs[2];self.assertNotIn('workspace',profile)
                self.assertNotIn('birth_date',profile)
                self.assertEqual(profile['status'],'Verified' if kind=='Student' else 'Pending')
    def test_google_signup_saves_birthday_on_the_existing_user(self):
        self.state['google_user']=self.data['email']
        self.f.session.user=self.data['email']
        self.challenges.google_identity.return_value=True
        existing=Record({'doctype':'User','email':self.data['email']})
        original=self.f.get_doc
        self.f.get_doc=lambda *args:existing if args[0]=='User' else original(*args)
        with patch.dict('sys.modules',{'frappe.utils.password':NS(update_password=Mock())}):
            self.complete('token','a-password-123','a-password-123')
        self.assertEqual(existing.birth_date,'2005-02-28')
        profile=next(d for d in self.docs if d['doctype']=='IL Public Profile')
        self.assertNotIn('birth_date',profile)

    def test_old_or_invalid_birthday_challenge_writes_nothing(self):
        for value in (None,'2005-02-30','2999-01-01'):
            self.data['birth_date']=value
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'date of birth|Date of birth'):
                self.complete('token','a-password-123','a-password-123')
            self.assertEqual(self.docs,[])
        self.f.db.commit.assert_not_called()

    def test_missing_phone_verification_writes_nothing(self):
        self.state['phone_verified']=False
        with self.assertRaisesRegex(ValueError,'required verification'):self.complete('token','a-password-123','a-password-123')
        self.assertEqual(self.docs,[]);self.f.db.commit.assert_not_called()
    def test_changed_google_session_writes_nothing(self):
        self.state['google_user']=self.data['email']
        with self.assertRaisesRegex(ValueError,'Google session changed'):self.complete('token','a-password-123','a-password-123')
        self.assertEqual(self.docs,[])
    def test_existing_account_is_not_overwritten(self):
        self.f.db.exists.return_value=True
        with self.assertRaisesRegex(ValueError,'already exists'):self.complete('token','a-password-123','a-password-123')
        self.assertEqual(self.docs,[])
    def test_consumed_challenge_is_not_reused(self):
        self.state['consumed']=True
        with self.assertRaises(ValueError):self.complete('token','a-password-123','a-password-123')
        self.assertEqual(self.docs,[])

    def test_provider_creation_defers_phone_without_claiming_verification(self):
        for kind in ('Individual Teacher', 'Institute'):
            with self.subTest(kind=kind):
                self.docs.clear(); self.state.pop('consumed', None)
                self.data['kind'] = kind; self.state['phone_verified'] = False
                self.assertTrue(self.complete('token','a-password-123','a-password-123')['created'])
                self.assertEqual([d['doctype'] for d in self.docs],
                                 ['User','IL Public Profile','IL Registration Request'])
                self.assertEqual(self.docs[1]['status'], 'Pending')
                self.assertNotIn('workspace', self.docs[1])
                self.assertNotIn('roles', self.docs[0])

    def test_provider_without_email_proof_cannot_create_account(self):
        self.data['kind'] = 'Individual Teacher'
        self.state['email_verified'] = False
        with self.assertRaises(ValueError):
            self.complete('token','a-password-123','a-password-123')
        self.assertEqual(self.docs, [])

    def test_registered_google_account_cannot_have_password_overwritten(self):
        self.state['google_user']=self.data['email'];self.f.session.user=self.data['email']
        self.challenges.google_identity.return_value=True;self.registered.return_value=True
        with self.assertRaisesRegex(ValueError,'Account already exists'):
            self.complete('token','a-password-123','a-password-123')
        self.assertEqual(self.docs,[])
        self.f.db.commit.assert_not_called()

    def test_teacher_paths_are_saved_without_granting_institute_permissions(self):
        from institute_lms.onboarding_navigation import teaching_path
        for path in ('individual','institute'):
            self.docs.clear();self.state.pop('consumed',None)
            self.data.update(kind='Individual Teacher',teaching_path=path)
            self.complete('token','a-password-123','a-password-123')
            profile=next(d for d in self.docs if d['doctype']=='IL Public Profile')
            registration=next(d for d in self.docs if d['doctype']=='IL Registration Request')
            self.assertEqual(profile['kind'],'Teacher');self.assertEqual(profile['status'],'Pending')
            self.assertEqual(teaching_path([registration],self.data['email']),path)
            self.assertFalse(any(d['doctype']=='IL Member' for d in self.docs))
            self.assertNotIn('roles',self.docs[0])
