"""Unit safeguards for the private campus worker; no database or email access."""
import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

class PlanChangeTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,11,27)
  self.profile=types.SimpleNamespace(user='owner@test.invalid',kind='Institute',status='Verified',workspace='inst-a')
  self.account=types.SimpleNamespace(role='Institute',institute='inst-a',enabled=1,modified=self.now,cancel_at_end=0,trial_started=self.now,trial_until=self.now+timedelta(days=14),paid_until=None,plan='Platinum',next_plan=None,add_comment=Mock())
  self.f=types.ModuleType('frappe');self.f.local=types.SimpleNamespace(request=None);self.f.session=types.SimpleNamespace(user='Administrator');self.f.conf={};self.f.PermissionError=PermissionError
  def throw(message,exc=ValueError):raise exc(message)
  self.f.throw=throw;self.f.get_doc=Mock(side_effect=lambda dt,*a,**k:self.profile if dt=='IL Public Profile' else self.account)
  self.f.db=types.SimpleNamespace(get_value=Mock(return_value=1),exists=Mock(return_value=True))
  utils=types.ModuleType('frappe.utils');utils.get_datetime=lambda x:x if isinstance(x,datetime) else datetime.fromisoformat(x);utils.now_datetime=lambda:self.now
  billing=types.ModuleType('institute_lms.account_billing');billing.ACCOUNT='IL Account Subscription';billing.save=Mock();billing.void_open=Mock();self.billing=billing
  rules=types.ModuleType('institute_lms.account_billing_rules');rules.PLANS=('Individual','Silver','Gold','Platinum')
  self.modules=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':utils,'institute_lms.account_billing':billing,'institute_lms.account_billing_rules':rules});self.modules.start();self.addCleanup(self.modules.stop)
  spec=importlib.util.spec_from_file_location('institute_lms.owner_plan_change',Path(__file__).parents[1]/'institute_lms/owner_plan_change.py');self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
 def apply(self,**kw):
  args=dict(profile='profile-a',user=self.profile.user,subscription='sub-a',plan='Gold',expected_modified=str(self.now),reason='Owner request',reviewer='platform-owner@test.invalid');args.update(kw);return self.module.apply(**args)
 def test_trial_dates_preserved_and_offers_voided(self):
  dates=(self.account.trial_started,self.account.trial_until,self.account.paid_until);self.assertTrue(self.apply()['ok']);self.assertEqual(self.account.plan,'Gold');self.assertEqual(dates,(self.account.trial_started,self.account.trial_until,self.account.paid_until));self.billing.void_open.assert_called_once();self.account.add_comment.assert_called_once()
 def test_paid_period_schedules_without_replacing_current(self):
  self.account.paid_until=self.now+timedelta(days=20);self.apply();self.assertEqual((self.account.plan,self.account.next_plan),('Platinum','Gold'))
 def test_cross_workspace_refused(self):
  self.account.institute='other';self.assertRaises(ValueError,self.apply);self.billing.save.assert_not_called()
 def test_stale_request_refused(self):
  self.assertRaises(ValueError,self.apply,expected_modified='2020-01-01');self.billing.save.assert_not_called()
 def test_http_and_non_admin_refused(self):
  self.f.local.request=object();self.assertRaises(PermissionError,self.apply);self.f.local.request=None;self.f.session.user='Guest';self.assertRaises(PermissionError,self.apply)
 def test_inactive_membership_refused(self):
  self.f.db.exists.return_value=False;self.assertRaises(ValueError,self.apply);self.billing.save.assert_not_called()
 def test_active_payment_prevents_save(self):
  self.billing.void_open.side_effect=ValueError('Payment in progress');self.assertRaises(ValueError,self.apply);self.billing.save.assert_not_called();self.account.add_comment.assert_not_called()
 def test_noop_does_not_void_invoices(self):
  self.account.plan='Gold';self.apply();self.billing.void_open.assert_not_called();self.billing.save.assert_not_called()
 def test_cancelled_subscription_refused(self):
  self.account.cancel_at_end=1;self.assertRaises(ValueError,self.apply)
 def test_invalid_plan_or_reason_refused(self):
  self.assertRaises(ValueError,self.apply,plan='Free');self.assertRaises(ValueError,self.apply,reason=' ')

if __name__=='__main__':unittest.main()
