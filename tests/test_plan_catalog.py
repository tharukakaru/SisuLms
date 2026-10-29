import unittest,types,sys,importlib
from unittest.mock import patch,Mock
from institute_lms.plan_catalog_rules import defaults,validate
class Rules(unittest.TestCase):
    def test_defaults_and_copy(self):
        p=defaults();v=validate(p);v['Gold']['monthly_lkr']=1
        self.assertEqual(p['Gold']['monthly_lkr'],15000)
    def test_bad_price_and_unknown_features(self):
        for value in [True,-1,0,1.5,'2500',10000001]:
            p=defaults();p['Gold']['monthly_lkr']=value
            with self.assertRaises(ValueError):validate(p)
        p=defaults();p['Gold']['features']['imaginary']=True
        with self.assertRaises(ValueError):validate(p)
    def test_missing_plan_and_non_boolean(self):
        p=defaults();p.pop('Silver')
        with self.assertRaises(ValueError):validate(p)
        p=defaults();p['Gold']['features']['news']='false'
        with self.assertRaises(ValueError):validate(p)
class Service(unittest.TestCase):
    def setUp(self):
        f=types.ModuleType('frappe');f.whitelist=lambda **kw:lambda fn:fn
        with patch.dict(sys.modules,{'frappe':f}):
            self.m=importlib.import_module('institute_lms.plan_catalog')
        self.fake=types.SimpleNamespace(db=types.SimpleNamespace(sql=Mock()),throw=lambda message:(_ for _ in ()).throw(ValueError(message)),get_doc=Mock())
        self.guard=types.ModuleType('institute_lms.account_billing');self.guard.require_owner=Mock()
        self.addCleanup(patch.stopall)
        patch.object(self.m,'frappe',self.fake).start()
        patch.dict(sys.modules,{'institute_lms.account_billing':self.guard}).start()
    def test_unauthorized_cannot_read_or_publish(self):
        self.guard.require_owner.side_effect=PermissionError()
        for fn,args in [(self.m.admin_get,()),(self.m.publish,(defaults(),0,'Updated plan pricing'))]:
            with self.assertRaises(PermissionError):fn(*args)
        self.fake.db.sql.assert_not_called()
    def test_stale_revision_never_writes(self):
        with patch.object(self.m,'current',return_value=dict(plans=defaults(),revision=3)):
            with self.assertRaisesRegex(ValueError,'changed'):self.m.publish(defaults(),2,'Updated plan pricing')
        self.fake.get_doc.assert_not_called()
    def test_first_publish_inserts(self):
        doc=types.SimpleNamespace(flags=types.SimpleNamespace(),save=Mock(),insert=Mock())
        self.fake.get_doc.return_value=doc
        audit=types.ModuleType('institute_lms.saas');audit.audit=Mock()
        with patch.dict(sys.modules,{'institute_lms.saas':audit}),patch.object(self.m,'current',return_value=dict(plans=defaults(),revision=0)):
            self.m.publish(defaults(),0,'Initial plan publication')
        doc.insert.assert_called_once_with(ignore_permissions=True);doc.save.assert_not_called()

    def test_success_audits_and_increments(self):
        doc=types.SimpleNamespace(flags=types.SimpleNamespace(),save=Mock())
        self.fake.get_doc.return_value=doc
        audit=types.ModuleType('institute_lms.saas');audit.audit=Mock()
        with patch.dict(sys.modules,{'institute_lms.saas':audit}),patch.object(self.m,'current',return_value=dict(plans=defaults(),revision=1)):
            p=defaults();p['Silver']['monthly_lkr']=6000
            result=self.m.publish(p,1,'Approved new price')
        self.assertEqual(result['revision'],2);self.assertEqual(result['plans']['Silver']['monthly_lkr'],6000)
        self.assertTrue(doc.flags.plan_catalog_service);doc.save.assert_called_once();audit.audit.assert_called_once()
if __name__=='__main__':unittest.main()
