"""Exercise returning-login routing without a database or access mutations."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

class ReturningTeacherRouting(unittest.TestCase):
    def route(self, memberships, personal=None, selected=None):
        data={'campus':selected}
        user='teacher@example.invalid'
        db=types.SimpleNamespace(
            get_value=lambda doctype,filters,fields=None,**kw: (True if doctype=='User' else personal if doctype=='IL Public Profile' else types.SimpleNamespace(role='Teacher',name='member')),
            exists=lambda doctype,filters: filters.get('institute') in memberships if doctype=='IL Member' else True)
        frappe=types.SimpleNamespace(whitelist=lambda *a,**kw:lambda f:f,session=types.SimpleNamespace(user=user,data=data),db=db,
            sessions=types.SimpleNamespace(get_csrf_token=lambda:'csrf'),conf={},
            local=types.SimpleNamespace(session_obj=types.SimpleNamespace(update=lambda **kw:None)),
            get_all=lambda doctype,**kw:memberships if doctype=='IL Member' else [])
        modules={'frappe':frappe,
            'institute_lms.wallet':types.SimpleNamespace(owner=lambda:None,admin_actor=lambda:False),
            'institute_lms.campus_context':types.SimpleNamespace(enabled=lambda:True,SESSION_KEY='campus'),
            'institute_lms.api':types.SimpleNamespace(institute=lambda:types.SimpleNamespace(name=data['campus'])),
            'institute_lms.onboarding':types.SimpleNamespace(account_kind=lambda:'Teacher')}
        with patch.dict(sys.modules,modules):
            spec=importlib.util.spec_from_file_location('institute_lms.portal_session',Path(__file__).parents[1]/'institute_lms/portal_session.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            result=module.current()
        return result,data['campus']
    def test_personal_workspace_wins_multiple_memberships(self):
        result,selected=self.route(['INSTITUTE','PERSONAL'],'PERSONAL')
        self.assertEqual(selected,'PERSONAL');self.assertEqual(result['role'],'Teacher')
    def test_approved_institute_opens_without_choice(self):
        result,selected=self.route(['B','A'])
        self.assertEqual(selected,'A');self.assertIsNotNone(result['member'])
    def test_preserve_explicit_active_workspace(self):
        _,selected=self.route(['A','B'],'A','B');self.assertEqual(selected,'B')
    def test_inactive_personal_never_grants_access(self):
        _,selected=self.route(['A'],'REMOVED');self.assertEqual(selected,'A')
    def test_no_membership_stays_outside_dashboard(self):
        result,selected=self.route([])
        self.assertEqual(result['role'],'Campus');self.assertIsNone(result['member'])

if __name__=='__main__':unittest.main()
