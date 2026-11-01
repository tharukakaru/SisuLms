import base64
import sys
import types
import unittest
from unittest.mock import MagicMock, patch
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from institute_lms import firebase_push as service


class WebConfig(unittest.TestCase):
    def setUp(self):
        self.config = dict(apiKey='public-key', projectId='sisu-lms', messagingSenderId='123', appId='1:123:web:abc')
        raw = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        self.vapid = base64.urlsafe_b64encode(raw).decode().rstrip('=')

    def test_public_config_only(self):
        self.assertEqual(service.web_settings(self.config, self.vapid)['config'], self.config)
        with self.assertRaises(ValueError): service.web_settings({**self.config, 'private_key': 'secret'}, self.vapid)

    def test_wrong_project_sender_and_vapid(self):
        for data, vapid in [({**self.config, 'projectId': 'other'}, self.vapid),
                            ({**self.config, 'appId': '1:456:web:abc'}, self.vapid),
                            (self.config, 'invalid'), (self.config, 'B' * 87)]:
            with self.assertRaises(ValueError): service.web_settings(data, vapid)


class SelfTest(unittest.TestCase):
    def setUp(self):
        self.f = types.SimpleNamespace(local=types.SimpleNamespace(site=service.SITE),
            session=types.SimpleNamespace(user='tester'),
            conf={'il_firebase_sandbox': {'test_user': 'tester', 'self_test_enabled': True}},
            cache=MagicMock(), get_doc=MagicMock())
        self.row = types.SimpleNamespace(user='tester', revoked=0, platform='web', token_hash='hash', get_password=lambda field:'secret-token')
        self.f.get_doc.return_value = self.row
        self.cache = {}
        self.f.cache.get_value.side_effect = self.cache.get
        self.f.cache.set_value.side_effect = lambda key,value,**kw:self.cache.update({key:value})
        self.messaging = MagicMock(); self.messaging.send.return_value = 'projects/sisu-lms/messages/test'
        modules = {'frappe': self.f, 'firebase_admin': types.SimpleNamespace(messaging=self.messaging),
            'institute_lms.registration': types.SimpleNamespace(limit=MagicMock())}
        p = patch.dict(sys.modules, modules); p.start(); self.addCleanup(p.stop)
        p = patch('institute_lms.firebase_backend.get_app', return_value=object()); p.start(); self.addCleanup(p.stop)
        self.nonce = '12345678-1234-1234-1234-123456789abc'

    def test_production_and_other_user_denied(self):
        self.f.local.site = 'production'
        self.assertFalse(service.browser_config()['available'])
        with self.assertRaises(PermissionError):service.self_test('device',self.nonce)
        self.f.local.site = service.SITE; self.f.session.user = 'customer'
        with self.assertRaises(PermissionError):service.self_test('device',self.nonce)
        self.messaging.send.assert_not_called()

    def test_foreign_revoked_and_mobile_denied(self):
        for attribute,value in [('user','another'),('revoked',1),('platform','android')]:
            old = getattr(self.row,attribute); setattr(self.row,attribute,value)
            with self.assertRaises(PermissionError):service.self_test('device',self.nonce)
            setattr(self.row,attribute,old)
        self.messaging.send.assert_not_called()

    def test_actual_send_requires_validation(self):
        with self.assertRaises(ValueError):service.self_test('device',self.nonce,False)
        self.messaging.send.assert_not_called()

    def test_validate_then_send_and_duplicate_rejected(self):
        self.assertEqual(service.self_test('device',self.nonce)['status'],'validated')
        self.assertTrue(self.messaging.send.call_args.kwargs['dry_run'])
        nonce = '22345678-1234-1234-1234-123456789abc'
        self.assertEqual(service.self_test('device',nonce,False)['status'],'accepted')
        self.assertFalse(self.messaging.send.call_args.kwargs['dry_run'])
        with self.assertRaises(ValueError):service.self_test('device',nonce,False)
        self.assertEqual(self.messaging.send.call_count,2)

    def test_uncertain_failure_is_redacted_and_not_retried(self):
        self.messaging.send.side_effect = RuntimeError('secret-token')
        with self.assertRaises(ValueError) as error:service.self_test('device',self.nonce)
        self.assertNotIn('secret-token',str(error.exception))
        with self.assertRaises(ValueError):service.self_test('device',self.nonce)
        self.assertEqual(self.messaging.send.call_count,1)

    def test_disabled_and_bad_nonce(self):
        with self.assertRaises(ValueError):service.self_test('device','bad')
        self.f.conf['il_firebase_sandbox']['self_test_enabled'] = False
        with self.assertRaises(PermissionError):service.self_test('device',self.nonce)
