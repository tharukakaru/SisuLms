"""Focused release contracts with mocked Frappe, not integration acceptance."""
import importlib.util,sys,types,unittest
from pathlib import Path
from unittest.mock import MagicMock,patch

ROOT=Path(__file__).resolve().parents[1]/'institute_lms'
class R(dict):
    def __getattr__(self,k):return self.get(k)
    def __setattr__(self,k,v):self[k]=v

class ReleaseContracts(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda f:f
        self.f.PermissionError=PermissionError;self.f.DoesNotExistError=LookupError
        self.f.throw=lambda msg,kind=ValueError:(_ for _ in ()).throw(kind(msg))
        self.f.conf=R();self.f.session=R(user='billing@example.invalid');self.f.db=MagicMock();self.f.get_all=MagicMock(return_value=[])
        self.f.get_doc=MagicMock();self.f.cache=MagicMock();self.f.get_hooks=MagicMock(return_value=[])
        self.mods=patch.dict(sys.modules,{'frappe':self.f});self.mods.start();self.addCleanup(self.mods.stop)
    def fake(self,name,**attrs):
        m=types.ModuleType('institute_lms.'+name);m.__dict__.update(attrs);sys.modules[m.__name__]=m;return m
    def load(self,name):
        key='institute_lms.'+name;spec=importlib.util.spec_from_file_location(key,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m);return m
    def test_https_origin_rejects_tokens_paths_and_untrusted_protocols(self):
        r=self.load('release')
        self.assertEqual(r.https_origin('https://billing.example.invalid/'),'https://billing.example.invalid')
        for v in ['http://host','https://user:pass@host','https://host/path','https://host?token=x','javascript:x',None]:self.assertIsNone(r.https_origin(v))
    def test_billing_scoped_to_current_contact(self):
        self.fake('platform',control=lambda:None,organization=MagicMock());self.fake('wallet',signed_in=lambda:None,admin_actor=lambda:False)
        r=self.load('release');r.billing();self.assertEqual(self.f.get_all.call_args_list[0].kwargs['filters'],{'admin_contact':'billing@example.invalid'})
    def test_control_room_requires_owner(self):
        owner=MagicMock(side_effect=PermissionError());self.fake('platform',owner=owner,organizations=MagicMock())
        with self.assertRaises(PermissionError):self.load('release').control_room()
        self.f.get_all.assert_not_called()
    def test_control_plane_contact_does_not_require_tenant_institute(self):
        self.f.conf.il_control_plane=True;self.f.sessions=R(get_csrf_token=lambda:'csrf');self.f.db.get_value.return_value=True
        self.fake('wallet',owner=MagicMock(),admin_actor=lambda:False)
        self.assertEqual(self.load('portal_session').current()['role'],'Billing')
    def test_guest_session_remains_unauthenticated(self):
        self.f.session.user='Guest';self.fake('wallet',owner=MagicMock(),admin_actor=lambda:False)
        self.assertEqual(self.load('portal_session').current(),{'authenticated':False})
    def test_liveness_no_database_or_secrets(self):
        h=self.load('health');self.assertEqual(h.live(),{'service':'sisu','reachable':True});self.f.db.sql.assert_not_called()
    def test_readiness_owner_only(self):
        self.fake('wallet',owner=MagicMock(side_effect=PermissionError()))
        with self.assertRaises(PermissionError):self.load('health').readiness()
        self.f.db.sql.assert_not_called()
    def test_readiness_missing_heartbeat_not_ready(self):
        self.fake('wallet',owner=lambda:None);self.f.db.sql.return_value=[(1,)];self.f.db.exists.return_value=True
        self.f.get_installed_apps=lambda:['institute_lms'];self.f.cache.get_value.side_effect=[True,None];self.f.conf.update(il_tenant_id='T',host_name='https://tenant.example.invalid')
        self.assertFalse(self.load('health').readiness()['ready'])
    def test_missing_channels_not_operational(self):
        self.fake('wallet',signed_in=lambda:None);self.fake('notification_service',preference=MagicMock())
        self.fake('saas',resolved=lambda:dict(available=True,features={'integrations.sms':True,'integrations.push':True}))
        self.f.db.get_value.return_value=None;self.f.db.exists.return_value=False
        r=self.load('release').channels();self.assertFalse(r['available']['SMS']);self.assertFalse(r['browser_push_available']);self.assertTrue(r['available']['IN_APP'])
    def test_channels_preserve_event_preferences(self):
        self.fake('wallet',signed_in=lambda:None);self.fake('notification_service',preference=MagicMock());self.fake('saas',resolved=lambda:dict(available=True,features={}))
        self.f.db.get_value.return_value='{"events":{"announcement":{"EMAIL":false}}}'
        r=self.load('release').channels();self.assertFalse(r['settings']['events']['announcement']['EMAIL'])
    def test_starter_source_discovery_denied(self):
        self.fake('saas',resolved=lambda:dict(available=True,features={'ai.rag':False}))
        with self.assertRaises(PermissionError):self.load('release').learning_sources('C')
        self.f.get_all.assert_not_called()
    def test_source_discovery_delegates_course_authorization(self):
        self.fake('saas',resolved=lambda:dict(available=True,features={'ai.rag':True}))
        a=self.fake('ai_access',authorize=MagicMock(side_effect=PermissionError('foreign course')))
        with self.assertRaises(PermissionError):self.load('release').learning_sources('other')
        a.authorize.assert_called_once_with('ai.rag','other');self.f.get_all.assert_not_called()
    def test_custom_price_requires_owner_before_data(self):
        self.fake('platform',owner=MagicMock(side_effect=PermissionError()),organization=MagicMock());self.fake('owner_pricing',save=MagicMock());self.fake('saas',audit=MagicMock())
        with self.assertRaises(PermissionError):self.load('release').custom_price('T',100,'Monthly','approved')
        self.f.db.sql.assert_not_called()
    def test_custom_contract_scoped_to_registry_tenant_without_local_institute(self):
        from institute_lms.pricing_rules import integer
        self.fake('platform',owner=lambda:None,organization=lambda tenant:R(name=tenant,admin_contact='payer'))
        saved=[]
        self.fake('owner_pricing',save=lambda d:saved.append(d) or d)
        self.fake('saas',audit=MagicMock())
        self.f.get_doc.side_effect=lambda values:R(**values,name='contract-1')
        result=self.load('release').custom_price('org-A',10000,'Monthly','Reviewed commercial terms')
        self.assertEqual(result['assignment'],'contract-1');self.assertEqual(saved[-1].tenant_id,'org-A')
        self.assertEqual(saved[-1].customer,'payer');self.assertIsNone(saved[-1].get('institute'))
        self.assertEqual(self.f.get_all.call_args.kwargs['filters']['tenant_id'],'org-A')
    def test_custom_contract_zero_price_rejected(self):
        self.fake('platform',owner=lambda:None,organization=lambda tenant:R(admin_contact='payer'))
        self.fake('owner_pricing',save=MagicMock());self.fake('saas',audit=MagicMock())
        with self.assertRaises(ValueError):self.load('release').custom_price('org-A',0,'Monthly','Review')
        self.f.db.sql.assert_not_called()

if __name__=='__main__':unittest.main()
