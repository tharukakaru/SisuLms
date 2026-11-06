"""Deploy institute teacher controls; retain old assets for open tabs."""
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH / 'apps/institute_lms'
ALLOWED = {'institute_lms/commercial.py'}


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o022)
    with tarfile.open('/tmp/sisu-bank-proof-upload.tgz') as archive:
        manifest = json.load(archive.extractfile('manifest.json'))
        if set(manifest) != ALLOWED or len(archive.getmembers()) != len(ALLOWED)+1:
            raise RuntimeError('Unexpected UI payload')
        payload = {}
        for name in ALLOWED:
            entry = archive.getmember(name)
            if not entry.isfile():
                raise RuntimeError('Unexpected archive member')
            payload[name] = archive.extractfile(entry).read()
            path = APP / name
            if path.is_symlink() or digest(payload[name]) != manifest[name]['after']:
                raise RuntimeError('UI payload mismatch')
            actual = digest(path.read_bytes()) if path.exists() else None
            if actual not in (manifest[name]['before'], manifest[name]['after']):
                raise RuntimeError('Source conflict: ' + name)
    root = Path.home() / '.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise RuntimeError('Private backup directory required')
    backup = root / ('bank-proof-upload-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700)
    paths = list(ALLOWED)
    absent = []
    for name in paths:
        src, dst = APP / name, backup / name
        if not src.exists():
            absent.append(name)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    try:
        for name, data in payload.items():
            (APP / name).parent.mkdir(parents=True, exist_ok=True)
            (APP / name).write_bytes(data)
            (APP / name).chmod(0o644)
        for site in ('sisuacademylk.com', 'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
            subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-cache'], cwd=BENCH, check=True)
    except Exception:
        for name in paths:
            src, dst = backup / name, APP / name
            if name in absent:
                if dst.is_file():
                    dst.unlink()
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        print('Previous sources/UI restored. Private build log:', backup / 'build.log')
        raise
    for site in ('sisuacademylk.com', 'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-cache'], cwd=BENCH, check=True)
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-website-cache'], cwd=BENCH, check=True)
    print('DEPLOYED: private bank proof upload from submitted bytes; restart web/workers and run checks. Hard-refresh before testing.')
    print('No schema or bank-account data changes by deployment. Existing enrollments/payments unchanged. Run rollback checks, then hard-refresh. Gateway remains held.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED [' + type(exc).__name__ + ']. ' + (str(exc) if isinstance(exc, RuntimeError) else 'Check private build log; browser result not confirmed.'))
        raise SystemExit(1) from None
