import importlib.util
from pathlib import Path
import unittest


class AccessCheck(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('wa_access_checker',
            Path(__file__).resolve().parents[1] / 'scripts/verify-whatsapp-access.py')
        self.m = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.m)
        self.data = dict(is_valid=True, app_id='123', scopes=list(self.m.REQUIRED),
                         expires_at=200, data_access_expires_at=0)

    def test_valid(self):
        self.assertEqual(self.m.inspect_token(self.data, '123', 100)['expires_at'], 200)

    def test_wrong_app(self):
        with self.assertRaises(self.m.CheckError): self.m.inspect_token(self.data, '456', 100)

    def test_invalid(self):
        self.data['is_valid'] = False
        with self.assertRaises(self.m.CheckError): self.m.inspect_token(self.data, '123', 100)

    def test_missing_permission(self):
        self.data['scopes'] = ['whatsapp_business_management']
        with self.assertRaises(self.m.CheckError): self.m.inspect_token(self.data, '123', 100)

    def test_expired(self):
        with self.assertRaises(self.m.CheckError): self.m.inspect_token(self.data, '123', 201)

    def test_expired_data_access(self):
        self.data['data_access_expires_at'] = 50
        with self.assertRaises(self.m.CheckError): self.m.inspect_token(self.data, '123', 100)

    def test_unknown_expiry(self):
        self.data.pop('expires_at')
        with self.assertRaises(self.m.CheckError): self.m.inspect_token(self.data, '123', 100)

    def test_zero_expiry(self):
        self.data['expires_at'] = 0
        self.assertEqual(self.m.inspect_token(self.data, '123', 100)['expires_at'], 0)

    def test_phone_id_and_actual_number_required(self):
        row = dict(id='42', display_phone_number='+94 77 123 4567')
        self.assertTrue(self.m.phone_matches(row, '42', '94771234567'))
        self.assertFalse(self.m.phone_matches(row, '43', '94771234567'))
        self.assertFalse(self.m.phone_matches(row, '42', '15550001111'))

    def test_account_switch_preserves_other_configuration_and_stages_only(self):
        original = {'il_cybersource': {'enabled': False}, 'il_whatsapp_phone_id': 'old'}
        credentials = dict(app_id='123', waba_id='456', phone_id='789', access_token='private')
        result = self.m.staged_config(original, credentials, 'new-secret', 'x'*32)
        self.assertEqual(original['il_whatsapp_phone_id'], 'old')
        self.assertEqual(result['il_whatsapp_phone_id'], '789')
        self.assertEqual(result['il_cybersource'], original['il_cybersource'])
        self.assertNotIn('il_whatsapp_token', result)
        self.assertEqual(result['il_whatsapp_pending_credentials'], credentials)

    def test_switch_refuses_existing_outbound_token(self):
        with self.assertRaises(self.m.CheckError):
            self.m.staged_config({'il_whatsapp_token': 'existing'}, {}, 'new', 'x'*32)

    def test_switch_requires_strong_verify_token(self):
        with self.assertRaises(self.m.CheckError):
            self.m.staged_config({}, {}, 'new', 'short')

    def test_diagnostics_redact_credentials_urls_and_control_characters(self):
        message = {'message': 'Cannot access account short-secret https://example.com/?token=private ' + 'EAA'+'x'*70 + '\n\x1b[31m'}
        result = self.m.safe_meta_error(message, ['short-secret'])
        self.assertNotIn('short-secret', result)
        self.assertNotIn('https://', result)
        self.assertNotIn('EAA', result)
        self.assertNotIn('\x1b', result)
        self.assertIn('Cannot access account', result)
