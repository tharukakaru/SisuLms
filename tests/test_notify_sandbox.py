import importlib.util,sys,types,unittest
from pathlib import Path
from unittest.mock import MagicMock,patch

class NotifySandbox(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe')
        def throw(message):raise ValueError(message)
        self.f.throw=throw
        self.stub=patch.dict(sys.modules,{'frappe':self.f});self.stub.start()
        self.adapter=self.load('notify_adapter');self.sandbox=self.load('notify_sandbox')
    def tearDown(self):self.stub.stop()
    def load(self,name):
        spec=importlib.util.spec_from_file_location('test_'+name,Path(__file__).parents[1]/'institute_lms'/f'{name}.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def test_other_recipient_rejected_before_provider(self):
        with patch.object(self.sandbox,'credentials',return_value={'test_phone':'+94711111111'}):
            with self.assertRaisesRegex(ValueError,'authorized'):self.sandbox.send('+94722222222','Test')
    def test_demo_sender_rejected(self):
        with patch.object(self.adapter.requests,'post') as post:
            with self.assertRaises(ValueError):self.adapter.send_config(dict(user_id='1',api_key='fake',sender_id='NotifyDEMO'),'+94711111111','Test')
            post.assert_not_called()
    def test_credentials_only_in_post_body_and_private_fields_excluded(self):
        response=MagicMock(ok=True);response.json.return_value={'status':'success','data':'Sent'}
        with patch.object(self.adapter.requests,'post',return_value=response) as post:
            result=self.adapter.send_config(dict(user_id='1',api_key='fake',sender_id='SisuAcademy',test_phone='+94711111111'),'+94711111111','Your code is 123456')
            self.assertTrue(result['accepted']);args=post.call_args
            self.assertEqual(args.args[0],'https://app.notify.lk/api/v1/send')
            self.assertFalse(args.kwargs['allow_redirects']);self.assertNotIn('test_phone',args.kwargs['data'])
            self.assertTrue(args.kwargs['data']['message'].startswith('SISU:'))
    def test_error_body_not_disclosed(self):
        response=MagicMock(ok=False);response.json.return_value={'status':'error','data':'secret-value'}
        with patch.object(self.adapter.requests,'post',return_value=response):
            with self.assertRaises(ValueError) as result:self.adapter.send_config(dict(user_id='1',api_key='fake',sender_id='SisuAcademy'),'+94711111111','Test')
            self.assertNotIn('secret-value',str(result.exception))
