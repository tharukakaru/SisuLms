import importlib.util,sys,types,unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock,patch
class OwnerInvitationDeliveryTests(unittest.TestCase):
 def setUp(self):
  self.f=types.ModuleType('frappe');self.f.conf={'il_control_plane':1,'il_owner_invitation_delivery_enabled':1};self.f.db=MagicMock();self.f.db.sql.return_value=[(1,)]
  utils=types.ModuleType('frappe.utils');utils.now_datetime=lambda:datetime(2026,11,10,12);utils.get_datetime=lambda v:v
  self.p=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':utils});self.p.start();self.addCleanup(self.p.stop)
  spec=importlib.util.spec_from_file_location('invitation_delivery_test',Path(__file__).parents[1]/'institute_lms/owner_invitation_delivery.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
 def doc(self,subject,status='Not Sent',recipient='owner@example.test',hour=12):
  d=MagicMock();d.message='Subject: '+subject+'\n\nbody';d.status=status;d.creation=datetime(2026,11,10,hour);d.recipients=[types.SimpleNamespace(recipient=recipient)];return d
 def run_docs(self,docs):
  self.f.get_all=MagicMock(return_value=[types.SimpleNamespace(name=str(i)) for i in range(len(docs))]);self.f.get_doc=MagicMock(side_effect=docs)
  with patch.object(self.m,'permitted',return_value=True):self.m.dispatch()
 def test_other_sites_do_not_dispatch(self):
  self.f.conf['il_control_plane']=False;self.m.dispatch();self.f.db.sql.assert_not_called()
 def test_only_fresh_authorized_invitation_sent(self):
  invite=self.doc('Your SISU Platform owner access');ordinary=self.doc('Payment reminder');old=self.doc('Your SISU institute billing access',hour=8)
  self.run_docs([invite,ordinary,old]);invite.send.assert_called_once_with(force_send=True);ordinary.send.assert_not_called();old.send.assert_not_called()
 def test_newer_sent_invitation_blocks_older_token(self):
  latest=self.doc('Your SISU Platform owner access','Sent');old=self.doc('Your SISU Platform owner access');self.run_docs([latest,old]);latest.send.assert_not_called();old.send.assert_not_called()
 def test_disabled_or_unapproved_recipient_not_sent(self):
  d=self.doc('Your SISU institute billing access');self.f.get_all=MagicMock(return_value=[types.SimpleNamespace(name='a')]);self.f.get_doc=MagicMock(return_value=d)
  with patch.object(self.m,'permitted',return_value=False):self.m.dispatch()
  d.send.assert_not_called()
 def test_unrecognized_and_multiple_recipients_not_sent(self):
  d=self.doc('Your SISU Platform owner access');d.recipients.append(types.SimpleNamespace(recipient='other@example.test'));self.run_docs([d]);d.send.assert_not_called()
 def test_lock_released_when_sending_fails(self):
  d=self.doc('Your SISU Platform owner access');d.send.side_effect=RuntimeError('failure')
  with self.assertRaises(RuntimeError):self.run_docs([d])
  self.assertIn('RELEASE_LOCK',self.f.db.sql.call_args.args[0])
