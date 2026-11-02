"""Prepare HTTP marketing and certificate validation; keep LMS closed until TLS."""
import os
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TARGET = Path('/etc/nginx/conf.d/sisu-main-public.conf')
RELEASE = Path('/var/www/sisu-marketing-releases/20261101T201903806657Z')
CONFIG = '''server {
    listen 80;
    listen [::]:80;
    server_name sisuacademylk.com www.sisuacademylk.com;
    root /var/www/sisu-marketing-releases/20261101T201903806657Z;
    index index.html;
    add_header X-Content-Type-Options nosniff always;
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/sisu-acme;
        try_files $uri =404;
    }
    location ~ ^/(campus|api|login|logout|app|private|protected|socket\\.io)(/|$) {
        default_type text/html;
        add_header Retry-After 300 always;
        return 503 '<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SISU is getting ready</title><body style="font-family:system-ui;max-width:36rem;margin:15vh auto;padding:2rem"><h1>Your learning space is almost ready.</h1><p>We are finishing setup. Please check back shortly.</p><a href="/">Back to SISU</a></body></html>';
    }
    location ~ /\\. { deny all; }
    location / { try_files $uri $uri/ =404; }
}
'''


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def inspect_routes():
    expected = (RELEASE/'index.html').read_bytes()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    passed = True
    print(json.dumps({'routing_file_present': TARGET.is_file(),
                      'routing_matches_prepared': TARGET.is_file() and TARGET.read_text() == CONFIG,
                      'nginx_valid': subprocess.run(['nginx', '-t'], capture_output=True).returncode == 0}))
    for host in ('sisuacademylk.com', 'www.sisuacademylk.com'):
        for path in ('/', '/index.html', '/campus'):
            request = urllib.request.Request('http://127.0.0.1'+path,
                headers={'Host':host, 'Accept-Encoding':'identity'})
            try:
                response = opener.open(request, timeout=10)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                body = response.read(2_000_000)
                match = body == expected
                ok = (response.code == 503 and b'Your learning space is almost ready.' in body) if path == '/campus' else (response.code == 200 and match)
                passed = passed and ok
                print(json.dumps({'host':host, 'path':path, 'status':response.code,
                    'content_type':response.headers.get('Content-Type'),
                    'encoding':response.headers.get('Content-Encoding'),
                    'bytes':len(body), 'matches_staged_index':match, 'pass':ok,
                    'response_sha256':hashlib.sha256(body).hexdigest()}))
    print(('PASS' if passed else 'BLOCKED')+': main website routes and closed LMS checks.')
    print('Inspection only: no configuration changes; no response bodies or credentials displayed.')
    return passed


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root on deployment server')
    if sys.argv[1:] == ['--inspect']:
        if not inspect_routes():
            raise SystemExit(2)
        return
    if sys.argv[1:]:
        raise RuntimeError('Unknown arguments')
    if TARGET.exists() or TARGET.is_symlink():
        raise RuntimeError('Main routing file already exists; inspect before replacing')
    if not (RELEASE/'index.html').is_file() or not (RELEASE/'app.js').is_file():
        raise RuntimeError('Staged marketing release missing')
    app = (RELEASE/'app.js').read_text()
    if "const base='';" not in app or '/campus?signup=1' not in app:
        raise RuntimeError('Same-host LMS links missing')
    result = subprocess.run(['nginx', '-T'], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Existing Nginx configuration invalid')
    import re
    for declaration in re.findall(r'\bserver_name\s+([^;]+);', result.stdout):
        if set(declaration.split()) & {'sisuacademylk.com', 'www.sisuacademylk.com'}:
            raise RuntimeError('Main domain already has an active routing declaration')
    Path('/var/www/sisu-acme/.well-known/acme-challenge').mkdir(parents=True, exist_ok=True, mode=0o755)
    with TARGET.open('x') as out:
        out.write(CONFIG)
    TARGET.chmod(0o644)
    try:
        if subprocess.run(['nginx', '-t'], capture_output=True).returncode:
            raise RuntimeError('Candidate Nginx validation failed')
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True, capture_output=True)
        # Reload signals the master; allow new workers to accept connections.
        time.sleep(1)
    except Exception:
        TARGET.unlink()
        subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True)
        raise
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for host in ('sisuacademylk.com', 'www.sisuacademylk.com'):
        request = urllib.request.Request('http://127.0.0.1/', headers={'Host':host})
        with opener.open(request, timeout=10) as response:
            if response.status != 200 or response.read() != (RELEASE/'index.html').read_bytes():
                raise RuntimeError('Local marketing route did not match staged website')
        print('PASS: '+host+' serves the staged main website over local HTTP.')
    print('PREPARED: marketing routing and certificate challenge path. LMS shows a setup page until HTTPS is installed.')
    print('DNS and existing tenant routes unchanged. Next: point main-domain DNS to 13.140.131.250, then obtain HTTPS certificate.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__)+'. No credentials displayed.')
        raise SystemExit(1)
