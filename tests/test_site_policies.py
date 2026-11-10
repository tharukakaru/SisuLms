import importlib,sys,types,unittest
from datetime import datetime,timedelta
from unittest.mock import Mock,patch
class SitePolicies(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,7,8)
        f=types.ModuleType('frappe');f.whitelist=lambda **kw:lambda fn:fn
        utils=types.ModuleType('frappe.utils');utils.now_datetime=lambda:self.now;utils.get_datetime=lambda x:x if isinstance(x,datetime) else datetime.fromisoformat(x)
        with patch.dict(sys.modules,{'frappe':f,'frappe.utils':utils}):self.m=importlib.import_module('institute_lms.site_policies')
        self.fake=types.SimpleNamespace(conf={},db=types.SimpleNamespace(sql=Mock(),get_value=Mock(return_value='delivery')),get_doc=Mock(),throw=lambda msg:(_ for _ in ()).throw(ValueError(msg)))
        self.org=types.SimpleNamespace(name='test-org',site_hostname='test.example.com',provisioning_state='ready')
        self.platform=types.ModuleType('institute_lms.platform');self.platform.owner=Mock();self.platform.organization=Mock(return_value=self.org)
        self.saas=types.ModuleType('institute_lms.saas');self.saas.managed=Mock();self.saas.audit=Mock()
        self.addCleanup(patch.stopall);patch.object(self.m,'frappe',self.fake).start();patch.object(self.m,'now_datetime',return_value=self.now).start();patch.object(self.m,'get_datetime',side_effect=utils.get_datetime).start();patch.dict(sys.modules,{'institute_lms.platform':self.platform,'institute_lms.saas':self.saas}).start()
    def configure(self):self.fake.conf={'il_policy_delivery_hosts':['test.example.com'],'il_tenant_signing_keys':{'test-org':'k'*32}}
    def test_ack_is_not_current_when_pending_failed_or_stale(self):
        self.assertEqual(self.m.delivery_label({'status':'Pending','acknowledged_at':self.now},self.now),'Waiting for delivery')
        self.assertEqual(self.m.delivery_label({'status':'Failed','acknowledged_at':self.now},self.now),'Delivery needs attention')
        self.assertEqual(self.m.delivery_label({'status':'Delivered','acknowledged_at':self.now-timedelta(days=2)},self.now),'Confirmation is out of date')
        self.assertEqual(self.m.delivery_label({'status':'Delivered','acknowledged_at':self.now},self.now),'Delivery confirmed')
    def test_unconfigured_site_cannot_queue(self):
        with self.assertRaises(ValueError):self.m.retry('test-org','Retry corrected hosting')
        self.fake.db.sql.assert_not_called();self.saas.managed.assert_not_called()
    def test_authority_before_reads(self):
        self.platform.owner.side_effect=PermissionError()
        for call in [lambda:self.m.listing(),lambda:self.m.retry('test-org','Retry corrected hosting'),lambda:self.m.organization_details('test-org')]:
            with self.assertRaises(PermissionError):call()
        self.platform.organization.assert_not_called()
    def test_ready_retry_queues_only_and_audits(self):
        self.configure();doc=types.SimpleNamespace(status='Failed');self.fake.get_doc.return_value=doc
        result=self.m.retry('test-org','Retry corrected hosting')
        self.assertTrue(result['queued']);self.assertEqual(doc.status,'Pending');self.assertEqual(doc.next_attempt,self.now)
        self.saas.managed.assert_called_once_with(doc);self.saas.audit.assert_called_once()
        self.saas.managed.reset_mock();self.m.retry('test-org','Retry corrected hosting');self.saas.managed.assert_not_called()
    def test_short_reason_rejected(self):
        self.configure()
        with self.assertRaises(ValueError):self.m.retry('test-org','test')
        self.saas.managed.assert_not_called()
if __name__=='__main__':unittest.main()
