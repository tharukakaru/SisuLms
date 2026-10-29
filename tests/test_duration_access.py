import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime,timedelta

class DurationAccess(unittest.TestCase):
    def setUp(self):
        def fail(message,*args):raise ValueError(message)
        f=types.ModuleType('frappe');f.throw=fail;f.whitelist=lambda **kw:lambda fn:fn
        f.get_doc=Mock()
        u=types.ModuleType('frappe.utils');u.now_datetime=lambda:datetime(2026,10,25);u.get_datetime=lambda v:datetime.fromisoformat(v) if isinstance(v,str) else v;u.getdate=lambda v:v
        self.patch=patch.dict(sys.modules,{'frappe':f,'frappe.utils':u});self.patch.start();self.addCleanup(self.patch.stop)
        spec=importlib.util.spec_from_file_location('institute_lms._duration_commercial',Path(__file__).parents[1]/'institute_lms/commercial.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m);self.f=f
    def test_saved_duration_controls_approved_access(self):
        for days in [1,14,30,90,180]:
            start,end=self.m.configured_access({'access_duration_days':days},'2026-10-25')
            self.assertEqual(end-start,timedelta(days=days))
    def test_programme_duration_overrides_module_duration(self):
        self.f.get_doc.return_value={'access_duration_days':90}
        start,end=self.m.configured_access({'programme':'P','access_duration_days':14},'2026-10-25')
        self.assertEqual(end-start,timedelta(days=90))
    def test_retired_usage_acknowledgment_has_no_billing_effect(self):
        self.m.account_for=lambda room:types.SimpleNamespace(name='A',plan='Gold')
        ack={'account':'A','plan':'Gold','unit_minor':5000,'policy':'access-30-v1','accepted':True}
        self.m.validate_pricing_ack({}, {'pricing_ack':ack})
        for change in [{'account':'B'},{'plan':'Silver'},{'unit_minor':10000},{'policy':'old'},{'accepted':False}]:
            self.assertIsNone(self.m.validate_pricing_ack({}, {'pricing_ack':{**ack,**change}}))
        self.f.get_doc.assert_not_called()
