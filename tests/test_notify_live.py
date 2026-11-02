import hashlib,importlib.util,sys,types,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock

class RestrictedNotify(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.local=types.SimpleNamespace(site='teen.sisuacademylk.com')
        self.f.conf={'il_notify_live':{'test_mode':True,'test_recipient_sha256':hashlib.sha256(b'94761234567').hexdigest()}}
        self.f.throw=MagicMock(side_effect=ValueError('blocked'))
        self.delegate=MagicMock(return_value={'accepted':True})
        self.patch=patch.dict(sys.modules,{'frappe':self.f,'institute_lms.notify_adapter':types.SimpleNamespace(send=self.delegate)});self.patch.start()
        spec=importlib.util.spec_from_file_location('institute_lms.notify_live_test',Path(__file__).parents[1]/'institute_lms/notify_live.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
    def tearDown(self):self.patch.stop()
    def test_other_recipient_never_loads_secret_or_sends(self):
        with patch.object(self.m,'credentials') as creds:
            with self.assertRaises(ValueError):self.m.send('+94761111111','test')
            creds.assert_not_called();self.delegate.assert_not_called()
    def test_other_site_blocked(self):
        self.f.local.site='other.example'
        with self.assertRaises(ValueError):self.m.send('+94761234567','test')
        self.delegate.assert_not_called()
    def test_missing_mode_blocked(self):
        self.f.conf['il_notify_live']={}
        with self.assertRaises(ValueError):self.m.send('+94761234567','test')
        self.delegate.assert_not_called()
    def test_config_restored_after_send_and_failure(self):
        original={'sentinel':'original'};self.f.conf['il_notify']=original
        for failure in (False,True):
            self.delegate.side_effect=RuntimeError('uncertain') if failure else None
            with patch.object(self.m,'credentials',return_value={'sender_id':'SisuAcademy'}):
                if failure:
                    with self.assertRaises(RuntimeError):self.m.send('+94761234567','test')
                else:self.assertTrue(self.m.send('+94761234567','test')['accepted'])
            self.assertIs(self.f.conf['il_notify'],original)
    def test_missing_legacy_config_stays_missing(self):
        with patch.object(self.m,'credentials',return_value={'sender_id':'SisuAcademy'}):self.m.send('+94761234567','test')
        self.assertNotIn('il_notify',self.f.conf)
