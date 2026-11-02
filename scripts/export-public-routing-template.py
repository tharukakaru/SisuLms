"""Export the existing tenant routing template, without reading certificate keys."""
import json
import os
import re
import socket
import subprocess
from pathlib import Path


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root on deployment server')
    source = Path('/etc/nginx/conf.d/sisu-new-tenants.conf')
    data = source.read_text()
    # No authentication headers, inline credentials or arbitrary include files
    # should be part of this simple tenant template.
    clean = re.sub(r'(?m)#.*$', '', data)
    if re.search(r'(?i)authorization|password|api[_-]?key|bearer|proxy_pass\s+https?://[^;\s]*@', clean):
        raise RuntimeError('Template contains sensitive directives; export withheld')
    if len(data) > 100_000 or 'teen.sisuacademylk.com' not in data:
        raise RuntimeError('Unexpected tenant template')
    result = subprocess.run(['nginx', '-t'], capture_output=True)
    if result.returncode:
        raise RuntimeError('Existing Nginx configuration fails validation')
    os.umask(0o077)
    with Path('/tmp/sisu-routing-template.conf').open('x') as out:
        out.write(data)
    for host in ('sisuacademylk.com', 'www.sisuacademylk.com'):
        try:
            addresses = sorted({r[4][0] for r in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
        except socket.gaierror:
            addresses = []
        print(json.dumps({'domain': host, 'addresses': addresses}))
    release = Path('/var/www/sisu-marketing-releases/20261101T201903806657Z')
    print(json.dumps({'marketing_release_present': (release/'index.html').is_file(),
                      'main_certificate_present': Path('/etc/letsencrypt/live/sisuacademylk.com/fullchain.pem').is_file()}))
    print('EXPORTED: /tmp/sisu-routing-template.conf. Routing unchanged; no private keys or site credentials read.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__))
        raise SystemExit(1)
