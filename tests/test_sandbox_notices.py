import unittest,importlib.util,types,sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock,patch

class SandboxNotices(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.local=types.SimpleNamespace(site='hnb-checkout.localhost');self.f.conf={'il_signup_notices_enabled':1,'il_self_signup_test_email':'student@example.com','il_self_signup_role_emails':{'Individual Teacher':'teacher@example.com'}}
        self.f.db=MagicMock();self.f.get_doc=MagicMock();self.f.log_error=MagicMock()
        self.modules=patch.dict(sys.modules,{'frappe':self.f});self.modules.start()
        spec=importlib.util.spec_from_file_location('notice_test',Path(__file__).parents[1]/'institute_lms/sandbox_notices.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
    def tearDown(self):self.modules.stop()
    def test_daily_window_is_exactly_final_ten_days(self):
        end=datetime(2026,11,30,12)
        for day,expected in [(19,None),(20,10),(25,5),(29,1),(30,None)]:self.assertEqual(self.m.reminder_days(end,datetime(2026,11,day)),expected)
    def test_production_never_queues_notices(self):
        self.f.local.site='production';self.m.queue('student@example.com','key','Subject','Body');self.f.get_doc.assert_not_called()
    def test_unknown_recipient_never_queues(self):
        self.m.queue('customer@example.com','key','Subject','Body');self.f.get_doc.assert_not_called()
    def test_duplicate_never_creates_second_notice(self):
        self.f.db.exists.return_value=True;self.m.queue('student@example.com','key','Subject','Body');self.f.get_doc.assert_not_called()
    def test_notice_failure_does_not_rollback_payment_transaction(self):
        with patch.object(self.m,'_observe',side_effect=ValueError('private detail')):
            self.m.observe(object())
        self.f.db.rollback.assert_called_once_with(save_point='sisu_notice')
        self.assertNotIn('private detail',str(self.f.log_error.call_args))
