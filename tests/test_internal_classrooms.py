"""Exercise the shared save implementation with an isolated document store double."""
import sys
import types
import unittest
from unittest.mock import MagicMock, patch
from test_upload_provisioning import function


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    def set(self,key,value):self[key]=value
    def is_new(self):return True
    def save(self,**kwargs):self['saved']=True;self['name']='internal-test'


class InternalClassrooms(unittest.TestCase):
    def setUp(self):
        self.inst=Row(name='INVTEST');self.member=Row(name='admin',role='Admin',active=1,user='admin@example.com')
        self.teacher=Row(name='teacher',institute='INVTEST',role='Teacher',active=1,user='teacher@example.com')
        self.room=Row()
        self.f=types.SimpleNamespace(session=Row(user='admin@example.com'),db=MagicMock(),
            get_all=MagicMock(return_value=[]),new_doc=lambda dt:self.room,PermissionError=PermissionError)
        def throw(message,kind=ValueError):raise kind(message)
        self.f.throw=throw;self.f.db.get_value.return_value=1;self.f.db.exists.return_value=True
        def scoped(dt,name,inst):
            if name!=self.teacher.name or self.teacher.institute!=inst.name:raise PermissionError('Foreign teacher')
            return self.teacher
        def role(member,*roles):
            if member.role not in roles:raise PermissionError('Role denied')
        internal=types.ModuleType('institute_lms.internal_classrooms')
        env=dict(frappe=self.f,scoped=scoped)
        internal.validate_admin=function('internal_classrooms','validate_admin',env)
        internal.teacher_affiliated=function('internal_classrooms','teacher_affiliated',env)
        internal.validate_request=function('internal_classrooms','validate_request',env)
        internal.teacher_for=function('internal_classrooms','teacher_for',env)
        catalog=types.ModuleType('institute_lms.catalog')
        catalog.validate_publication=function('catalog','validate_publication',dict(frappe=self.f,cint=int,
            publishing_options=lambda:[{'name':'provider'}]))
        rules=types.ModuleType('institute_lms.commercial_rules')
        rules.duration_days=lambda x:30;rules.access_window=lambda *a:None
        self.teaching=types.ModuleType('institute_lms.teaching')
        self.teaching.institute_profile=MagicMock(return_value='provider')
        self.teaching.approved_teacher=MagicMock()
        self.modules={'institute_lms.internal_classrooms':internal,'institute_lms.catalog':catalog,
            'institute_lms.commercial_rules':rules,'institute_lms.teaching':self.teaching}
        self.save=function('api','_save_classroom',dict(frappe=self.f,identity=lambda:(self.inst,self.member),
            require_role=role,payload=Row,scoped=scoped,limited=lambda v,*a:v,money=float,cint=int,now_datetime=lambda:None))
        self.data=dict(title='Internal',subject='Science',teacher='teacher',description='',motivation='',published=0)

    def run_save(self,internal=True):
        with patch.dict(sys.modules,self.modules):return self.save(self.data,internal=internal)

    def test_active_admin_creates_internal_in_current_institute(self):
        self.assertEqual(self.run_save(),'internal-test')
        self.assertEqual(self.room.institute,'INVTEST');self.assertEqual(self.room.owner_type,'Institute')
        self.assertEqual(self.room.published,0);self.assertIsNone(self.room.public_provider)
        self.assertEqual(self.room.teacher,'teacher');self.assertEqual(self.room.access_duration_days,30)
        self.teaching.institute_profile.assert_not_called()

    def test_students_teachers_inactive_admins_and_guest_rejected(self):
        for role in ('Student','Teacher'):
            self.member.role=role
            self.f.db.exists.return_value=False
            with self.assertRaises(PermissionError):self.run_save()
        self.member.role='Admin'
        with self.assertRaises(PermissionError):self.run_save()
        self.f.db.exists.return_value=True;self.f.session.user='Guest'
        with self.assertRaises(PermissionError):self.run_save()

    def test_foreign_or_inactive_teacher_rejected(self):
        self.teacher.institute='OTHER'
        with self.assertRaises(PermissionError):self.run_save()
        self.teacher.institute='INVTEST';self.teacher.active=0
        with self.assertRaises(PermissionError):self.run_save()

    def test_payload_cannot_publish_or_select_owner(self):
        for field,value in [('published',1),('published','false'),('public_provider','provider'),
                ('institute','OTHER'),('owner_user','attacker'),('owner_type','Teacher'),('administrator','attacker')]:
            with self.subTest(field=field):
                original=self.data.copy();self.data[field]=value
                with self.assertRaises(PermissionError):self.run_save()
                self.data=original
        self.assertFalse(self.room.get('saved'))

    def test_existing_profile_requires_teacher_consent(self):
        self.f.get_all.return_value=['provider']
        self.f.db.exists.side_effect=lambda dt,*a,**kw:dt=='IL Member'
        with self.assertRaisesRegex(PermissionError,'approved institute membership'):self.run_save()
        self.f.db.exists.side_effect=None;self.f.db.exists.return_value=True
        self.assertEqual(self.run_save(),'internal-test')

    def test_original_provider_creation_still_uses_existing_checks(self):
        self.data['published']=1
        self.assertEqual(self.run_save(internal=False),'internal-test')
        self.teaching.approved_teacher.assert_called_once_with(self.inst,'teacher','provider')
        self.assertEqual(self.room.public_provider,'provider');self.assertEqual(self.room.published,1)

    def test_internal_management_stays_internal_until_explicit_publishing(self):
        self.data['name']='internal-test'
        self.room.update(name='internal-test',published=0,public_provider=None,teacher='teacher')
        self.teaching.require=MagicMock()
        self.save.__globals__['classroom_for']=lambda *a,**k:(self.inst,self.member,self.room)
        self.run_save(internal=False)
        self.assertIsNone(self.room.public_provider)
        self.teaching.institute_profile.assert_not_called()
        self.data['published']=1
        self.run_save(internal=False)
        self.teaching.approved_teacher.assert_called_once()

    def test_teacher_rights_recheck_internal_affiliation(self):
        # Coverage has its own tests; this test isolates affiliation revocation.
        self.modules['institute_lms.institute_coverage']=__import__('types').SimpleNamespace(room_allowed=lambda room,member:True)
        rights=function('teaching','rights',dict(frappe=self.f,capabilities=lambda r,m,a:a))
        room=Row(institute='INVTEST',owner_type='Institute',public_provider=None)
        self.f.get_all.return_value=['provider']
        with patch.dict(sys.modules,self.modules):
            self.f.db.exists.return_value=True
            self.assertTrue(rights(room,self.teacher))
            self.f.db.exists.return_value=False
            self.assertFalse(rights(room,self.teacher))


if __name__=='__main__':unittest.main()
