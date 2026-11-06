import copy,hashlib,importlib,sys,time
from contextlib import nullcontext
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch

class PasswordReset(TestCase):
 def setUp(self):
  self.values={}
  def fail(message,error=ValueError):raise error(message)
  self.f=NS(whitelist=lambda **kw:lambda fn:fn,PermissionError=PermissionError,throw=fail,session=NS(user='student',sid='session-a'),cache=NS(lock=lambda *a,**kw:nullcontext(),get_value=lambda k:copy.deepcopy(self.values.get(k)),set_value=lambda k,v,**kw:self.values.update({k:copy.deepcopy(v)})))
  self.context=NS(require_user=lambda:self.f.session.user)
  self.update=Mock();self.receipt=Mock();self.clear=Mock()
  self.patch=patch.dict(sys.modules,{'frappe':self.f,'institute_lms.campus_context':self.context,'frappe.utils.password':NS(update_password=self.update),'frappe.sessions':NS(clear_sessions=self.clear),'institute_lms.account_confirmations':NS(queue=self.receipt)})
  self.patch.start();self.addCleanup(self.patch.stop)
  sys.modules.pop('institute_lms.password_reset',None)
  self.mod=importlib.import_module('institute_lms.password_reset');self.addCleanup(lambda:sys.modules.pop('institute_lms.password_reset',None))
  self.token='t'*48;self.proof='p'*48
  self.state={'user':'student','session':hashlib.sha256(b'session-a').hexdigest(),'expires':time.time()+600,'verified':False,'proof':hashlib.sha256(self.proof.encode()).hexdigest()}
  self.mod.store(self.token,self.state)
 def test_email_proof_and_original_session_required(self):
  with self.assertRaises(PermissionError):self.mod.confirm(self.token,'wrong')
  with self.assertRaises(ValueError):self.mod.finish(self.token,'example-password-123','example-password-123')
  self.mod.confirm(self.token,self.proof)
  self.f.session.sid='session-b'
  with self.assertRaises(PermissionError):self.mod.status(self.token)
  with self.assertRaises(PermissionError):self.mod.finish(self.token,'example-password-123','example-password-123')
  self.update.assert_not_called()
 def test_password_change_is_one_time_and_revokes_sessions(self):
  self.mod.confirm(self.token,self.proof)
  with self.assertRaises(ValueError):self.mod.finish(self.token,'short','short')
  with self.assertRaises(ValueError):self.mod.finish(self.token,'example-password-123','mismatch')
  self.mod.finish(self.token,'example-password-123','example-password-123')
  self.update.assert_called_once_with('student','example-password-123',logout_all_sessions=True)
  self.receipt.assert_called_once()
  self.clear.assert_called_once_with(user='student',keep_current=False,force=True)
  with self.assertRaises(ValueError):self.mod.finish(self.token,'another-password-123','another-password-123')
  self.assertEqual(self.update.call_count,1)
 def test_expired_proof_cannot_confirm(self):
  self.state['expires']=time.time()-1;self.mod.store(self.token,self.state)
  with self.assertRaises(ValueError):self.mod.confirm(self.token,self.proof)
 def test_start_uses_signed_in_email_and_does_not_change_password(self):
  mail=Mock();limit=Mock()
  with patch.dict(sys.modules,{'frappe.utils':NS(get_url=lambda:'https://www.sisuacademylk.com'),'institute_lms.registration':NS(limit=limit)}),patch.object(self.mod,'send_link',mail):
   result=self.mod.start()
  self.assertEqual(result['email'],'student')
  self.assertEqual(mail.call_args.args[0],'student')
  self.assertIn('/campus#password-confirm=',mail.call_args.args[1])
  self.update.assert_not_called();limit.assert_called_once()
