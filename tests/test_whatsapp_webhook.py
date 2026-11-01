import hashlib
import hmac
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class Webhook(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType('frappe')
        self.f.conf = dict(il_whatsapp_verify_token='secret-token', il_whatsapp_app_secret='app-secret',
                           il_whatsapp_waba_id='W', il_whatsapp_phone_id='P')
        self.f.db = MagicMock()
        self.f.get_doc = MagicMock()
        self.f.get_all = MagicMock(return_value=[])
        self.f.request = types.SimpleNamespace(method='GET', args={'hub.mode': 'subscribe',
            'hub.verify_token': 'secret-token', 'hub.challenge': '12345'})
        api = types.ModuleType('institute_lms.api')
        api.institute = lambda: types.SimpleNamespace(name='I')
        p = patch.dict(sys.modules, {'frappe': self.f, 'institute_lms.api': api})
        p.start(); self.addCleanup(p.stop)
        spec = importlib.util.spec_from_file_location('institute_lms.whatsapp_webhook',
            Path(__file__).resolve().parents[1] / 'institute_lms/whatsapp_webhook.py')
        self.m = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.m)

    def data(self):
        return {'object': 'whatsapp_business_account', 'entry': [{'id': 'W', 'changes': [
            {'field': 'messages', 'value': {'messaging_product': 'whatsapp',
             'metadata': {'phone_number_id': 'P'}, 'messages': [{'id': 'M', 'type': 'text',
             'from': '94711111111', 'text': {'body': 'Hello'}}]}}]}]}

    def post(self, data=None):
        raw = json.dumps(self.data() if data is None else data).encode()
        signature = 'sha256=' + hmac.new(b'app-secret', raw, hashlib.sha256).hexdigest()
        self.f.request = types.SimpleNamespace(method='POST', content_length=len(raw),
            get_data=lambda **kw: raw, headers={'X-Hub-Signature-256': signature})

    def test_plain_challenge(self):
        response = self.m.handle()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(), b'12345')
        self.assertEqual(response.mimetype, 'text/plain')

    def test_wrong_token(self):
        self.f.request.args['hub.verify_token'] = 'bad'
        self.assertEqual(self.m.handle().status_code, 403)

    def test_wrong_mode(self):
        self.f.request.args['hub.mode'] = 'bad'
        self.assertEqual(self.m.handle().status_code, 400)

    def test_missing_challenge(self):
        del self.f.request.args['hub.challenge']
        self.assertEqual(self.m.handle().status_code, 400)

    def test_tampered_signature(self):
        self.post(); self.f.request.headers['X-Hub-Signature-256'] = 'sha256=bad'
        self.assertEqual(self.m.handle().status_code, 403)
        self.f.get_doc.assert_not_called()

    def test_missing_secret(self):
        self.post(); self.f.conf.pop('il_whatsapp_app_secret')
        self.assertEqual(self.m.handle().status_code, 403)

    def test_oversized(self):
        self.post(); self.f.request.content_length = 262145
        self.assertEqual(self.m.handle().status_code, 413)

    def test_foreign_waba(self):
        d = self.data(); d['entry'][0]['id'] = 'FOREIGN'
        self.assertEqual(list(self.m.events(d, 'W', 'P')), [])

    def test_foreign_phone(self):
        self.assertEqual(list(self.m.events(self.data(), 'W', 'FOREIGN')), [])

    def test_bad_object(self):
        self.post({'object': 'other'})
        self.assertEqual(self.m.handle().status_code, 400)

    def test_dedup_key_and_durable_ack(self):
        self.post(); self.assertEqual(self.m.handle().status_code, 200)
        self.f.get_doc.return_value.insert.assert_called_once_with(ignore_permissions=True, ignore_if_duplicate=True)
        self.f.db.commit.assert_called_once()
        rows = list(self.m.events(self.data(), 'W', 'P'))
        self.assertEqual(rows, list(self.m.events(self.data(), 'W', 'P')))
        self.assertEqual(rows[0][2]['text'], 'Hello')

    def test_database_failure_not_acknowledged(self):
        self.post(); self.f.get_doc.return_value.insert.side_effect = RuntimeError('db')
        with self.assertRaises(RuntimeError): self.m.handle()
        self.f.db.commit.assert_not_called()

    def status_fixture(self, current='Read'):
        receipt = MagicMock(state='Pending', institute='I', payload=json.dumps(
            {'id': 'M', 'status': 'delivered', 'recipient_id': '94711111111'}))
        delivery = MagicMock(institute='I', provider_id='M', channel='WhatsApp', recipient='R', status=current)
        member = types.SimpleNamespace(institute='I', phone='+94711111111')
        self.f.get_all.return_value = ['N']
        self.f.get_doc.side_effect = [receipt, delivery, member]
        return receipt, delivery

    def test_out_of_order_does_not_downgrade(self):
        receipt, delivery = self.status_fixture()
        self.m.process_status('K')
        delivery.save.assert_not_called()
        self.assertEqual(receipt.state, 'Processed')

    def test_delivery_updates_existing_outbox(self):
        receipt, delivery = self.status_fixture('Accepted')
        self.m.process_status('K')
        self.assertEqual(delivery.status, 'Delivered')
        self.assertEqual(receipt.state, 'Processed')

    def test_cross_tenant_outbox_rejected(self):
        receipt, delivery = self.status_fixture('Accepted'); delivery.institute = 'OTHER'
        self.m.process_status('K')
        delivery.save.assert_not_called()
        self.assertEqual(receipt.state, 'Pending')

    def test_early_callback_retained(self):
        receipt, _ = self.status_fixture(); self.f.get_all.return_value = []
        self.m.process_status('K')
        self.assertEqual(receipt.state, 'Pending')

    def test_processed_duplicate_no_effect(self):
        receipt, delivery = self.status_fixture(); receipt.state = 'Processed'
        self.m.process_status('K')
        self.f.get_all.assert_not_called()
        delivery.save.assert_not_called()
