import importlib.util,json,sys,types,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
class ProvisionEvidenceTests(unittest.TestCase):
 def setUp(self):
  with patch.dict(sys.modules,{'frappe':types.ModuleType('frappe')}):
   spec=importlib.util.spec_from_file_location('provision_evidence_test',Path(__file__).parents[1]/'institute_lms/provision_verification.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
  self.now=datetime(2026,11,10,tzinfo=timezone.utc);self.key='test-only-attestation-key-'*2
  self.job=types.SimpleNamespace(name='job-test');self.org=types.SimpleNamespace(name='org-test',site_hostname='example.test',institute_code='TEST',admin_contact='owner@example.test')
  self.e={'job':'job-test','tenant_id':'org-test','hostname':'example.test','code':'TEST','admin_contact':'owner@example.test','verified_at':self.now.isoformat(),'checks':dict.fromkeys(['tenant_identity','installed_apps','database','institute','admin','signing_keys'],True)}
 def record(self):return json.dumps({'evidence':self.e,'signature':self.m.signature(self.e,self.key)})
 def test_valid_signed_current_evidence(self):self.assertTrue(self.m.valid_record(self.record(),self.job,self.org,self.key,self.now))
 def test_stale_future_or_unsigned_evidence_rejected(self):
  for delta in [-16,1]:
   self.e['verified_at']=(self.now+timedelta(minutes=delta)).isoformat();self.assertFalse(self.m.valid_record(self.record(),self.job,self.org,self.key,self.now))
  self.assertFalse(self.m.valid_record('{}',self.job,self.org,self.key,self.now))
 def test_wrong_tenant_or_missing_check_rejected(self):
  self.e['tenant_id']='another';self.assertFalse(self.m.valid_record(self.record(),self.job,self.org,self.key,self.now))
  self.e['tenant_id']='org-test';self.e['checks']['admin']=False;self.assertFalse(self.m.valid_record(self.record(),self.job,self.org,self.key,self.now))
 def test_tampered_signature_rejected(self):
  record=self.record();self.e['code']='DIFFERENT';self.assertFalse(self.m.valid_record(record.replace('TEST','DIFFERENT'),self.job,self.org,self.key,self.now))
