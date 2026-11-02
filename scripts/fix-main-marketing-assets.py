"""Restore the /marketing asset prefix used by the published website."""
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

TARGET=Path('/etc/nginx/conf.d/sisu-main-public.conf')
ROOT=Path('/var/www/sisu-marketing-releases/20261101T201903806657Z')
BLOCK='''    location /marketing/ {
        alias /var/www/sisu-marketing-releases/20261101T201903806657Z/;
    }
'''


def main():
    if os.name!='posix' or os.geteuid()!=0:raise RuntimeError('Run as root')
    if TARGET.is_symlink():raise RuntimeError('Unexpected routing symlink')
    old=TARGET.read_text()
    anchor='    location /assets/ {'
    if old.count(anchor)!=1:raise RuntimeError('Unexpected routing template')
    if 'location /marketing/' in old:raise RuntimeError('Marketing route already exists; inspect before changing')
    for name in ('app.js','style.css','theme.css'):
        if not (ROOT/name).is_file():raise RuntimeError('Marketing asset missing')
    backup=Path('/root/sisu-public-provision-isolated')/('routing-before-assets-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.conf')
    os.umask(0o077);backup.write_text(old)
    TARGET.write_text(old.replace(anchor,BLOCK+anchor));TARGET.chmod(0o644)
    try:
        if subprocess.run(['nginx','-t'],capture_output=True).returncode:raise RuntimeError('Nginx validation failed')
        subprocess.run(['systemctl','reload','nginx'],capture_output=True,check=True);time.sleep(2)
        for name in ('app.js','style.css','theme.css'):
            response=subprocess.run(['curl','--noproxy','*','--resolve','www.sisuacademylk.com:443:127.0.0.1','-fsS','--max-time','15','https://www.sisuacademylk.com/marketing/'+name],capture_output=True)
            if response.returncode or response.stdout!=(ROOT/name).read_bytes():raise RuntimeError('Asset check failed: '+name)
            print('PASS: /marketing/'+name,flush=True)
    except Exception:
        TARGET.write_text(old);subprocess.run(['systemctl','reload','nginx'],capture_output=True)
        print('RESTORED: previous routing');raise
    print('FIXED: main website JavaScript and stylesheet routes; hard-refresh the main website.')
    print('LMS accounts, verification state and service settings unchanged.')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__))
        raise SystemExit(1)
