import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class NotifyAdapter(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType('frappe')
        self.f.conf = {'il_notify':{'user_id':'test','api_key':'test','sender_id':'SISU'}}
        def fail(message): raise ValueError(message)
        self.f.throw=fail
        self.modules=patch.dict(sys.modules,{'frappe':self.f})
        self.modules.start(); self.addCleanup(self.modules.stop)
        spec=importlib.util.spec_from_file_location('notify_test',Path(__file__).parents[1]/'institute_lms/notify_adapter.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.post=patch.object(self.m.requests,'post').start();self.addCleanup(patch.stopall)
        self.post.return_value=Mock(ok=True,json=lambda:{'status':'success','data':'Sent'})

    def test_acceptance_does_not_invent_delivery_or_provider_id(self):
        value=self.m.send('+94771234567','Test')
        self.assertTrue(value['accepted']);self.assertIsNone(value['provider_id'])
        self.assertNotIn('delivered',value)
        self.assertEqual(self.post.call_args.kwargs['data']['message'],'SISU: Test')

    def test_unsupported_destination_never_calls_provider(self):
        with self.assertRaises(ValueError): self.m.send('+14155551234','Test')
        self.post.assert_not_called()

    def test_provider_rejection_is_not_success(self):
        self.post.return_value=Mock(ok=True,json=lambda:{'status':'error','data':'Rejected'})
        with self.assertRaises(ValueError): self.m.send('+94771234567','Test')

    def test_ambiguous_timeout_is_not_retried(self):
        self.post.side_effect=self.m.requests.Timeout()
        with self.assertRaisesRegex(ValueError,'uncertain'):self.m.send('+94771234567','Test')
        self.post.assert_called_once()
