"""Point marketing entry buttons to the campus role/sign-in screen."""
import os
import subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('/var/www/sisu-marketing-releases/20261101T201903806657Z')
OLD='const signup=()=>`${base}/campus?signup=1`;'
NEW='const signup=()=>`${base}/campus`;'


def main():
    if os.name!='posix' or os.geteuid()!=0:raise RuntimeError('Run as root')
    path=ROOT/'app.js'
    if path.is_symlink():raise RuntimeError('Unexpected source symlink')
    old=path.read_bytes();text=old.decode()
    if text.count(OLD)!=1:raise RuntimeError('Expected entry link not found; nothing changed')
    new=text.replace(OLD,NEW).encode()
    backup=Path('/root/sisu-public-provision-isolated')/('marketing-entry-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.js')
    os.umask(0o077);backup.write_bytes(old)
    path.write_bytes(new);path.chmod(0o644)
    result=subprocess.run(['curl','--noproxy','*','--resolve','www.sisuacademylk.com:443:127.0.0.1','-fsS','--max-time','15','https://www.sisuacademylk.com/marketing/app.js'],capture_output=True)
    if result.returncode or result.stdout!=new:
        path.write_bytes(old)
        raise RuntimeError('HTTPS verification failed; previous script restored')
    print('UPDATED: marketing entry buttons open /campus role/sign-in page.')
    print('Create-account controls inside the LMS unchanged. Hard-refresh the main website.')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__));raise SystemExit(1)
