"""Sandbox-only loopback gateway. Expose this port, never the whole Frappe bench."""
import hashlib
import hmac
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlsplit

PATH = '/api/method/institute_lms.notification_service.whatsapp_webhook'
CONFIG = Path.home() / 'sisu-hnb-sandbox-bench/sites/hnb-checkout.localhost/site_config.json'
MAX_BODY = 262144
SLOTS = threading.BoundedSemaphore(8)


class Gateway(BaseHTTPRequestHandler):
    server_version = 'SISU-Webhook'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *args):
        pass  # GET verification token is in the query; never log request URLs.

    def reply(self, status, body=b'Request rejected'):
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_GET(self):
        self.handle_webhook()

    def do_POST(self):
        self.handle_webhook()

    def handle_webhook(self):
        if not SLOTS.acquire(blocking=False):
            return self.reply(503)
        try:
            self.process_webhook()
        except Exception:
            # No exception trace, request body or credentials in public responses/logs.
            self.reply(503, b'Webhook temporarily unavailable')
        finally:
            SLOTS.release()

    def process_webhook(self):
        url = urlsplit(self.path)
        if url.scheme or url.netloc or url.fragment or url.path != PATH:
            return self.reply(404)
        config = json.loads(CONFIG.read_text())
        if self.command == 'GET':
            query = parse_qs(url.query, keep_blank_values=True, max_num_fields=3)
            if set(query) != {'hub.mode', 'hub.verify_token', 'hub.challenge'} or any(len(v) != 1 for v in query.values()):
                return self.reply(400)
            token = str(config.get('il_whatsapp_verify_token') or '')
            if not token or not hmac.compare_digest(token.encode(), query['hub.verify_token'][0].encode()):
                return self.reply(403)
            challenge = query['hub.challenge'][0]
            if query['hub.mode'] != ['subscribe'] or not challenge or len(challenge) > 512:
                return self.reply(400)
            # Answer here so the verify token never reaches Frappe's request-URL logs.
            return self.reply(200, challenge.encode())
        if url.query or self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
            return self.reply(400)
        if self.headers.get_content_type() != 'application/json':
            return self.reply(415)
        try:
            size = int(self.headers['Content-Length'])
        except (ValueError, TypeError):
            return self.reply(400)
        if not 0 < size <= MAX_BODY:
            return self.reply(413)
        raw = self.rfile.read(size)
        if len(raw) != size:
            return self.reply(400)
        secret = str(config.get('il_whatsapp_app_secret') or '')
        signature = self.headers.get('X-Hub-Signature-256', '')
        expected = 'sha256=' + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        if not secret or not hmac.compare_digest(expected.encode(), signature.encode()):
            return self.reply(403)
        try:
            data = json.loads(raw)
            # Prevent Frappe cmd/form dispatch overrides at this public boundary.
            if not isinstance(data, dict) or set(data) - {'object', 'entry'}:
                return self.reply(400)
        except ValueError:
            return self.reply(400)
        connection = HTTPConnection('127.0.0.1', 8001, timeout=20)
        try:
            connection.request('POST', PATH, body=raw, headers={
                'Host': 'hnb-checkout.localhost', 'Content-Type': 'application/json',
                'X-Hub-Signature-256': signature})
            response = connection.getresponse()
            body = response.read(1024)
            if response.status == 200 and body == b'EVENT_RECEIVED':
                return self.reply(200, body)
            # Never relay redirects, cookies, traceback pages or upstream headers.
            return self.reply(response.status if response.status in (400, 403, 413) else 503)
        finally:
            connection.close()


def main():
    if not CONFIG.is_file():
        raise SystemExit('Dedicated sandbox configuration missing.')
    server = ThreadingHTTPServer(('127.0.0.1', 8102), Gateway)
    server.daemon_threads = True
    print('Webhook-only gateway listening on 127.0.0.1:8102. Request logging disabled.', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
