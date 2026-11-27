import ast
from contextlib import contextmanager
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch

class OwnerEndpointTests(unittest.TestCase):
 def test_denied_owner_never_queues_a_change(self):
  tree=ast.parse((Path(__file__).parents[1]/'institute_lms/owner_people.py').read_text())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='change_institute_plan');fn.decorator_list=[]
  namespace={'authorize':Mock(side_effect=PermissionError('Owner manager required'))}
  queue=Mock();jobs=types.ModuleType('frappe.utils.background_jobs');jobs.get_queue=queue
  rules=types.ModuleType('institute_lms.account_billing_rules');rules.PLANS=('Gold',)
  namespace['__package__']='institute_lms'
  with patch.dict('sys.modules',{'frappe.utils.background_jobs':jobs,'institute_lms.account_billing_rules':rules}):
   exec(compile(ast.Module(body=[fn],type_ignores=[]),'owner_endpoint','exec'),namespace)
   with self.assertRaises(PermissionError):namespace['change_institute_plan']('evil.site','user','sub','Gold','stamp','reason')
  queue.assert_not_called()
 def test_unconfigured_campus_is_rejected_before_connect(self):
  tree=ast.parse((Path(__file__).parents[1]/'institute_lms/owner_people.py').read_text())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='campus')
  def deny(*args):raise PermissionError('campus not configured')
  connect=Mock();ns={'contextmanager':contextmanager,'sources':lambda:['safe.site'],'connect':connect,'frappe':types.SimpleNamespace(throw=deny,PermissionError=PermissionError)}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'campus','exec'),ns)
  with self.assertRaises(PermissionError):
   with ns['campus']('evil.site'):pass
  connect.assert_not_called()

if __name__=='__main__':unittest.main()
