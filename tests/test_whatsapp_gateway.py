import hashlib
import hmac
import importlib.util
from io import BytesIO
import json
from email.message import Message
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode


class Gateway(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('test_gateway_module',
            Path(__file__).resolve().parents[1] / 'scripts/whatsapp-webhook-gateway.py')
        self.m = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.m)
        self.m.CONFIG = MagicMock()
        self.m.CONFIG.read_text.return_value = json.dumps({'il_whatsapp_verify_token': 'token', 'il_whatsapp_app_secret': 'secret'})
        self.g = object.__new__(self.m.Gateway)
        self.g.path = self.m.PATH
        self.g.command = 'POST'
        self.g.reply = MagicMock()
        self.g.headers = Message()
        self.raw = b'{"object":"whatsapp_business_account","entry":[]}'
        self.g.headers['Content-Type'] = 'application/json'
        self.g.headers['Content-Length'] = str(len(self.raw))
        self.g.headers['X-Hub-Signature-256'] = 'sha256=' + hmac.new(b'secret', self.raw, hashlib.sha256).hexdigest()
        self.g.rfile = BytesIO(self.raw)
        self.connection = MagicMock()
        self.connection.getresponse.return_value.status = 200
        self.connection.getresponse.return_value.read.return_value = b'EVENT_RECEIVED'
        p = patch.object(self.m, 'HTTPConnection', return_value=self.connection)
        self.http = p.start(); self.addCleanup(p.stop)

    def test_login_not_forwarded(self):
        self.g.path = '/login'; self.g.process_webhook()
        self.g.reply.assert_called_once_with(404); self.http.assert_not_called()

    def test_encoded_path_not_forwarded(self):
        self.g.path = self.m.PATH + '%2f..%2flogin'; self.g.process_webhook()
        self.g.reply.assert_called_once_with(404); self.http.assert_not_called()

    def test_query_override_blocked(self):
        self.g.path += '?cmd=login'; self.g.process_webhook()
        self.g.reply.assert_called_once_with(400); self.http.assert_not_called()

    def test_chunked_rejected(self):
        self.g.headers['Transfer-Encoding'] = 'chunked'; self.g.process_webhook()
        self.g.reply.assert_called_once_with(400); self.http.assert_not_called()

    def test_bad_signature_rejected(self):
        self.g.headers.replace_header('X-Hub-Signature-256', 'bad'); self.g.process_webhook()
        self.g.reply.assert_called_once_with(403); self.http.assert_not_called()

    def test_signature_preserved_no_auth_cookies_forwarded(self):
        self.g.headers['Cookie'] = 'sid=not-forwarded'
        self.g.headers['Authorization'] = 'Bearer not-forwarded'
        self.g.process_webhook()
        call = self.connection.request.call_args
        self.assertEqual(call.kwargs['body'], self.raw)
        self.assertEqual(set(call.kwargs['headers']), {'Host', 'Content-Type', 'X-Hub-Signature-256'})
        self.g.reply.assert_called_once_with(200, b'EVENT_RECEIVED')

    def test_backend_traceback_suppressed(self):
        self.connection.getresponse.return_value.status = 500
        self.connection.getresponse.return_value.read.return_value = b'private traceback'
        self.g.process_webhook(); self.g.reply.assert_called_once_with(503)

    def test_backend_redirect_not_forwarded(self):
        self.connection.getresponse.return_value.status = 302
        self.g.process_webhook(); self.g.reply.assert_called_once_with(503)

    def test_get_secret_never_forwarded(self):
        self.g.command = 'GET'
        self.g.path += '?' + urlencode({'hub.mode': 'subscribe', 'hub.verify_token': 'token', 'hub.challenge': '123'})
        self.g.process_webhook()
        self.g.reply.assert_called_once_with(200, b'123'); self.http.assert_not_called()

    def test_get_wrong_token(self):
        self.g.command = 'GET'
        self.g.path += '?' + urlencode({'hub.mode': 'subscribe', 'hub.verify_token': 'wrong', 'hub.challenge': '123'})
        self.g.process_webhook()
        self.g.reply.assert_called_once_with(403); self.http.assert_not_called()

    def test_signed_cmd_payload_blocked(self):
        raw = b'{"cmd":"login"}'
        self.g.headers.replace_header('Content-Length', str(len(raw)))
        self.g.headers.replace_header('X-Hub-Signature-256', 'sha256='+hmac.new(b'secret', raw, hashlib.sha256).hexdigest())
        self.g.rfile = BytesIO(raw); self.g.process_webhook()
        self.g.reply.assert_called_once_with(400); self.http.assert_not_called()
