import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch,MagicMock

class PublicStudent(unittest.TestCase):
 def setUp(self):
  self.f=NS(local=NS(student_request_institute=None),PermissionError=ValueError,whitelist=lambda **kw:lambda fn:fn)
  self.f.throw=lambda text,*a:(_ for _ in ()).throw(ValueError(text))
  self.member=NS(role='Student')
  self.lookup=MagicMock(return_value=self.member)
  self.p=patch.dict(sys.modules,{'frappe':self.f,'institute_lms.campus_context':NS(membership=self.lookup)})
  self.p.start();self.addCleanup(self.p.stop)
  spec=importlib.util.spec_from_file_location('institute_lms._public_student_test',Path(__file__).parents[1]/'institute_lms/public_student.py')
  self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
 def test_context_is_restored_after_error(self):
  self.f.local.student_request_institute='previous'
  with self.assertRaises(RuntimeError):
   with self.mod.workspace('authorized'):
    self.assertEqual(self.f.local.student_request_institute,'authorized')
    raise RuntimeError('transaction failure')
  self.assertEqual(self.f.local.student_request_institute,'previous')
  self.lookup.assert_called_once_with('authorized')
 def test_non_student_rejected(self):
  self.member.role='Teacher'
  with self.assertRaises(ValueError):
   with self.mod.workspace('other'):self.fail('must not enter')
  self.assertIsNone(self.f.local.student_request_institute)
 def test_revoked_membership_rejected_before_context(self):
  self.lookup.side_effect=ValueError('revoked')
  with self.assertRaises(ValueError):
   with self.mod.workspace('other'):self.fail('must not enter')
  self.assertIsNone(self.f.local.student_request_institute)

 def test_public_endpoints_reach_membership_checks_without_selected_institute(self):
  import ast
  methods=['billing','classes','choices','schedule','action','upload_proof','proof']
  self.f.conf={};self.f.session=NS(user='student@example.invalid')
  for filename in ['saas.py','account_billing.py']:
   tree=ast.parse((Path(__file__).parents[1]/'institute_lms'/filename).read_text(encoding='utf-8'))
   fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='guard_request')
   require=MagicMock(side_effect=AssertionError('Must not require an institute before bridge authorization'))
   env={'frappe':self.f,'privileged':lambda:False,'require':require,'__name__':'institute_lms.guard_test'}
   exec(compile(ast.Module(body=[fn],type_ignores=[]),filename,'exec'),env)
   with patch.dict(sys.modules,{'institute_lms.wallet':NS(admin_actor=lambda:False),'institute_lms.commercial':NS(request_policy=lambda *a:False)}):
    for method in methods:
     self.f.form_dict={};self.f.local.request=NS(path='/api/method/institute_lms.public_student.'+method)
     env['guard_request']()
   require.assert_not_called()
 def test_schedule_scopes_each_membership_and_restores_context(self):
  self.mod.memberships=lambda:['one','two']
  calls=[]
  def scoped(**kwargs):
   calls.append(self.f.local.student_request_institute)
   return [{'name':calls[-1],'starts_at':'2026-11-05 12:00:00'}]
  with patch.dict(sys.modules,{'institute_lms.api':NS(schedule=scoped)}):
   result=self.mod.schedule(starts_on='2026-11-01',ends_on='2026-11-30')
  self.assertEqual(calls,['one','two'])
  self.assertEqual({r['institute'] for r in result},{'one','two'})
  self.assertIsNone(self.f.local.student_request_institute)
