from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
from test_upload_provisioning import function
class PublicNotify(TestCase):
 def setUp(self):
  def fail(message):raise ValueError(message)
  self.f=NS(local=NS(site='sisuacademylk.com'),conf={'il_public_sms_enabled':1,'il_shared_campus_enabled':1},throw=fail)
  self.secret=Mock(return_value={'sender_id':'SisuAcademy'});self.send=Mock(return_value={'accepted':True})
  import re
  self.call=function('notify_public','send',{'frappe':self.f,'re':re,'credentials':self.secret})
  p=patch.dict('sys.modules',{'institute_lms.notify_adapter':NS(send_config=self.send)});p.start();self.addCleanup(p.stop)
 def test_verified_public_configuration_uses_protected_credentials(self):
  self.assertTrue(self.call('+94761234567','code')['accepted']);self.send.assert_called_once_with({'sender_id':'SisuAcademy'},'94761234567','code')
  self.assertNotIn('il_notify',self.f.conf)
 def test_disabled_flag_denies_before_credentials(self):
  self.f.conf['il_public_sms_enabled']=0
  with self.assertRaises(ValueError):self.call('+94761234567','code')
  self.secret.assert_not_called();self.send.assert_not_called()
 def test_other_sites_and_control_plane_denied(self):
  for site in ('teen.sisuacademylk.com','hnb-checkout.localhost','../other'):
   self.f.local.site=site
   with self.assertRaises(ValueError):self.call('+94761234567','code')
  self.f.local.site='sisuacademylk.com';self.f.conf['il_control_plane']=1
  with self.assertRaises(ValueError):self.call('+94761234567','code')
  self.send.assert_not_called()
 def test_invalid_number_never_sends(self):
  for number in ('+12025550123','+9476','94761234567&to=other'):
   with self.assertRaises(ValueError):self.call(number,'code')
  self.secret.assert_not_called();self.send.assert_not_called()
 def test_uncertain_acceptance_is_not_retried(self):
  self.send.side_effect=ValueError('uncertain')
  with self.assertRaises(ValueError):self.call('+94761234567','code')
  self.send.assert_called_once()
