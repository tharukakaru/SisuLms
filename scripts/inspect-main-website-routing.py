"""Read-only routing inventory. No full Nginx/site configuration or secrets printed."""
import json
import re
import socket
import subprocess
from pathlib import Path

HOSTS = ('sisuacademylk.com', 'www.sisuacademylk.com',
         'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com')


def main():
    for host in HOSTS:
        try:
            addresses = sorted({row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
            print('DNS:', host, ', '.join(addresses))
        except socket.gaierror:
            print('DNS UNRESOLVED:', host)
    result = subprocess.run(['nginx', '-T'], capture_output=True, text=True)
    if result.returncode:
        print('BLOCKED: nginx configuration check failed. Raw configuration withheld.')
        raise SystemExit(1)
    filename = ''
    # Flatten whitespace across directives; keep only routing directives with safe syntax.
    text = result.stdout
    for part in re.split(r'(?m)^# configuration file ', text):
        if ':\n' not in part:
            continue
        filename, content = part.split(':\n', 1)
        if not re.fullmatch(r'/[A-Za-z0-9_./-]+', filename):
            continue
        content = re.sub(r'(?m)#.*$', '', content)
        directives = re.findall(r'(?:^|[;{}])\s*(server_name\s+[^;]+|listen\s+[^;]+|root\s+[^;]+|alias\s+[^;]+|proxy_pass\s+[^;]+|proxy_set_header\s+(?:Host|X-Frappe-Site-Name)\s+[^;]+|ssl_certificate\s+[^;]+|location\s+[^{};]+)(?:;|\{)', content)
        if not directives:
            continue
        print('CONFIG:', filename)
        for directive in directives:
            clean = ' '.join(directive.split())
            if len(clean) <= 300 and re.fullmatch(r'[A-Za-z0-9_./:$*~^?=+(){}|\\\[\] -]+', clean):
                print(' ', clean)
    sites = Path('/home/sisu/frappe-bench/sites')
    for config in sorted(sites.glob('*/site_config.json')):
        if config.parent.name not in HOSTS:
            continue
        data = json.loads(config.read_text())
        print('SITE:', config.parent.name, 'control_plane=', bool(data.get('il_control_plane')))
    print('Inspection complete. No files, DNS, certificates or services changed.')


if __name__ == '__main__':
    main()
