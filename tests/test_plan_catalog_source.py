import importlib,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from institute_lms.plan_catalog_rules import defaults
class SharedSource(unittest.TestCase):
    def setUp(self):
        self.f=types.SimpleNamespace(conf={'il_plan_catalog_source_site':'platform.example.com'},local=types.SimpleNamespace(site='public.example.com'),PermissionError=PermissionError,throw=lambda message,*a:(_ for _ in ()).throw(PermissionError(message)))
        with patch.dict(sys.modules,{'frappe':self.f}):self.m=importlib.import_module('institute_lms.plan_catalog_source')
        self.p=patch.object(self.m,'frappe',self.f);self.p.start();self.addCleanup(self.p.stop)
    def test_consumers_cannot_publish(self):
        with self.assertRaises(PermissionError):self.m.require_source_writer()
        self.f.local.site='platform.example.com';self.m.require_source_writer()
        self.assertIsNone(self.m.read_source())
    def test_readonly_source_not_consumer_defaults_and_request_cache(self):
        with tempfile.TemporaryDirectory() as root:
            sites=Path(root);(sites/'platform.example.com').mkdir();(sites/'public.example.com').mkdir()
            (sites/'common_site_config.json').write_text('{}')
            (sites/'platform.example.com'/'site_config.json').write_text(json.dumps({'db_name':'source_db','db_password':'test-only'}))
            self.f.get_site_path=lambda:str(sites/'public.example.com')
            cursor=Mock();cursor.__enter__=Mock(return_value=cursor);cursor.__exit__=Mock(return_value=False)
            plans=defaults();plans['Gold']['monthly_lkr']=12345;cursor.fetchone.return_value=(json.dumps(plans),9)
            connection=Mock();connection.cursor.return_value=cursor
            driver=types.SimpleNamespace(connect=Mock(return_value=connection))
            with patch.dict(sys.modules,{'pymysql':driver}):
                result=self.m.read_source();self.assertEqual(result['revision'],9);self.assertEqual(result['plans']['Gold']['monthly_lkr'],12345)
                self.assertIs(self.m.read_source(),result);driver.connect.assert_called_once()
            self.assertEqual(cursor.execute.call_args_list[0].args,('START TRANSACTION READ ONLY',))
            self.assertIn('SELECT payload, revision',cursor.execute.call_args_list[1].args[0]);connection.close.assert_called_once()
    def test_invalid_source_path_rejected(self):
        self.f.conf['il_plan_catalog_source_site']='../secret'
        with self.assertRaises(RuntimeError):self.m.read_source()
if __name__=='__main__':unittest.main()
