"""Install pinned HTTPS routing; preserve maintenance and service settings."""
import hashlib
import os
import subprocess
import tempfile
import time
from pathlib import Path

TARGET = Path('/etc/nginx/conf.d/sisu-main-public.conf')
SOURCE = Path('/tmp/sisu-main-https.conf')
EXPECTED_OLD = 'cc20333e40f94868cbc2dd6188d142b4b9f752529ebf6b52704c913ff038557f'
EXPECTED_NEW = '87f36393c8f822ca6c3b44bc186ea21c50c042ac13870e36ab881c82a6bbec29'


def replace(data):
    fd, name = tempfile.mkstemp(dir=TARGET.parent, prefix='.sisu-https-')
    with os.fdopen(fd, 'wb') as out:
        out.write(data)
    os.chmod(name, 0o644)
    os.replace(name, TARGET)


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root')
    old = TARGET.read_bytes()
    new = SOURCE.read_bytes()
    if TARGET.is_symlink() or SOURCE.is_symlink() or hashlib.sha256(old).hexdigest() != EXPECTED_OLD or hashlib.sha256(new).hexdigest() != EXPECTED_NEW:
        raise RuntimeError('Routing differs from reviewed configuration; nothing replaced')
    backup = Path('/root/sisu-public-provision-isolated/main-http-before-https.conf')
    os.umask(0o077)
    with backup.open('xb') as out:
        out.write(old)
    replace(new)
    try:
        if subprocess.run(['nginx', '-t'], capture_output=True).returncode:
            raise RuntimeError('HTTPS Nginx validation failed')
        subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True, check=True)
        time.sleep(2)
        for host in ('www.sisuacademylk.com', 'sisuacademylk.com'):
            result = subprocess.run(['curl', '--noproxy', '*', '--resolve', host+':443:127.0.0.1', '--max-time', '15', '-sS', '-o', '/dev/null', '-w', '%{http_code}', 'https://'+host+'/'], capture_output=True, text=True)
            expected = '200' if host.startswith('www.') else '301'
            if result.returncode or result.stdout != expected:
                raise RuntimeError('TLS or main-page response check failed for '+host)
            print('PASS: verified HTTPS '+host+'; HTTP '+result.stdout, flush=True)
    except Exception:
        replace(old)
        subprocess.run(['systemctl', 'reload', 'nginx'], capture_output=True)
        print('RESTORED: previous HTTP routing.')
        raise
    print('CONNECTED: main website HTTPS and /campus routing to the separate public LMS.')
    print('Public LMS remains in maintenance. Signup/services activation and browser testing remain pending.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__))
        raise SystemExit(1)
