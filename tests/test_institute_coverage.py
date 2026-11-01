import unittest, importlib.util, types, sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

class InstituteCoverage(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe')
        self.f.local=types.SimpleNamespace(site='hnb-checkout.localhost')
        self.f.conf={'il_institute_teacher_coverage':1}
        self.f.db=MagicMock(); self.f.db.exists.return_value=True
        self.f.db.get_value.side_effect=lambda dt,*args: 'profile' if dt=='IL Public Profile' else 'subscription'
        self.account=types.SimpleNamespace(name='subscription',trial_until=None,enabled=1,paid_until=datetime.now()+timedelta(days=1))
        self.f.get_doc=MagicMock(return_value=self.account)
        billing=types.ModuleType('institute_lms.account_billing'); billing.state=MagicMock(return_value={'available':True})
        utils=types.ModuleType('frappe.utils'); utils.get_datetime=lambda x:x; utils.now_datetime=datetime.now
        self.modules=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':utils,'institute_lms.account_billing':billing});self.modules.start()
        spec=importlib.util.spec_from_file_location('institute_lms.coverage_test',Path(__file__).parents[1]/'institute_lms/institute_coverage.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.billing=billing
    def tearDown(self):self.modules.stop()
    def test_paid_confirmed_membership_covered(self):
        self.assertEqual(self.m.sponsor('school','teacher')['profile'],'profile')
        self.assertEqual(self.f.db.exists.call_args.args[1]['status'],'Active')
    def test_missing_membership_denied(self):
        self.f.db.exists.return_value=False
        self.assertIsNone(self.m.sponsor('school','teacher'))
    def test_expired_disabled_trial_or_suspended_denied(self):
        for enabled,until,available in [(0,datetime.now()+timedelta(days=1),True),(1,None,True),(1,datetime.now()-timedelta(seconds=1),True),(1,datetime.now()+timedelta(days=1),False)]:
            self.account.enabled=enabled;self.account.paid_until=until;self.billing.state.return_value={'available':available}
            self.assertIsNone(self.m.sponsor('school','teacher'))
    def test_production_disabled(self):
        self.f.local.site='production';self.assertIsNone(self.m.sponsor('school','teacher'))
    def test_no_independent_or_generic_api_bypass(self):
        for method in ['institute_lms.api.create_classroom','frappe.client.get_list','institute_lms.teaching.overview']:
            self.assertFalse(self.m.request_allowed(method,'school','teacher'))
        self.assertTrue(self.m.request_allowed('institute_lms.api.classrooms','school','teacher'))
    def test_room_scope(self):
        class Room(dict):
            institute='school'
        member=types.SimpleNamespace(role='Teacher',user='teacher',name='member')
        room=Room(owner_type='Institute',public_provider='profile',teacher='member',teacher_assignment_active=1)
        with patch.object(self.m,'personal',return_value=False):
            self.assertTrue(self.m.room_allowed(room,member))
            for key,value in [('owner_type','Teacher'),('public_provider','another'),('teacher','another'),('teacher_assignment_active',0)]:
                changed=Room(room);changed[key]=value
                self.assertFalse(self.m.room_allowed(changed,member))

    def test_explicit_trial_grant_expires_and_is_account_scoped(self):
        self.account.paid_until=None
        self.account.trial_until=datetime.now()+timedelta(days=20)
        self.assertIsNone(self.m.sponsor('school','teacher'))
        self.f.conf['il_institute_trial_grants']={'school':{'subscription':'subscription','expires_at':self.account.trial_until}}
        self.assertIsNotNone(self.m.sponsor('school','teacher'))
        self.assertIsNone(self.m.sponsor('other-school','teacher'))
        self.f.conf['il_institute_trial_grants']['school']['subscription']='other'
        self.assertIsNone(self.m.sponsor('school','teacher'))
        self.f.conf['il_institute_trial_grants']['school']={'subscription':'subscription','expires_at':datetime.now()-timedelta(seconds=1)}
        self.assertIsNone(self.m.sponsor('school','teacher'))
