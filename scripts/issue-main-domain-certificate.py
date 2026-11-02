"""Check main-domain DNS, then obtain TLS using the existing Certbot account."""
import json
import os
import re
import subprocess
from pathlib import Path

HOSTS = ('sisuacademylk.com', 'www.sisuacademylk.com')


def public_answers(host, resolver, record):
    result = subprocess.run(['dig', '@'+resolver, host, record, '+time=4',
        '+tries=1', '+noall', '+comments', '+answer'], capture_output=True, text=True, timeout=8)
    if result.returncode or not re.search(r'status:\s*NOERROR\b', result.stdout):
        raise RuntimeError('Public DNS query failed for '+host+' at '+resolver)
    rows = [line.split() for line in result.stdout.splitlines() if line and not line.startswith(';')]
    if any(len(row) >= 5 and row[3] == 'CNAME' for row in rows):
        raise RuntimeError('Unexpected CNAME; expected the configured direct A records')
    return sorted({row[4] for row in rows if len(row) >= 5 and row[3] == record})


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root on deployment server')
    ready = True
    for host in HOSTS:
        for resolver in ('1.1.1.1', '8.8.8.8'):
            addresses = public_answers(host, resolver, 'A')
            ipv6 = public_answers(host, resolver, 'AAAA')
            print(json.dumps({'domain':host, 'resolver':resolver, 'ipv4':addresses, 'ipv6':ipv6}), flush=True)
            ready = ready and addresses == ['13.140.131.250'] and not ipv6
    if not ready:
        raise RuntimeError('Public resolvers have not both converged to the expected address. Certificate request not attempted')
    if not Path('/etc/nginx/conf.d/sisu-main-public.conf').is_file():
        raise RuntimeError('Prepared main-domain routing missing')
    if subprocess.run(['nginx', '-t'], capture_output=True).returncode:
        raise RuntimeError('Nginx validation failed')
    accounts = list(Path('/etc/letsencrypt/accounts/acme-v02.api.letsencrypt.org/directory').glob('*/regr.json'))
    if len(accounts) != 1:
        raise RuntimeError('Expected one existing production Certbot account; review account selection')
    command = ['certbot', 'certonly', '--webroot', '-w', '/var/www/sisu-acme',
               '--cert-name', 'sisuacademylk.com', '-d', HOSTS[0], '-d', HOSTS[1],
               '--non-interactive', '--keep-until-expiring', '--account', accounts[0].parent.name]
    result = subprocess.run(command)
    if result.returncode:
        raise RuntimeError('Certificate request failed; review Certbot output before retrying')
    for name in ('fullchain.pem', 'privkey.pem'):
        if not (Path('/etc/letsencrypt/live/sisuacademylk.com')/name).is_file():
            raise RuntimeError('Expected certificate files missing')
    print('PASS: main-domain certificate files available. No private key displayed.')
    print('HTTPS routing still needs installation. LMS remains closed; payment and WhatsApp settings unchanged.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__))
        raise SystemExit(1)
