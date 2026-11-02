"""Export only the three conflicted Python sources for local review."""
import ast
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path

SOURCE = Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms')
OUTPUT = Path('/tmp/sisu-public-source-review.tgz')
NAMES = ('native_access.py', 'portal_session.py', 'validation.py')


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu on deployment server')
    rows = {}
    for name in NAMES:
        path = SOURCE/name
        if path.is_symlink() or path.resolve().parent != SOURCE.resolve():
            raise RuntimeError('Unexpected source path')
        data = path.read_bytes()
        if len(data) > 2_000_000:
            raise RuntimeError('Unexpected source size')
        ast.parse(data.decode('utf-8-sig'))
        rows[name] = data
    os.umask(0o077)
    # Exclusive creation prevents overwriting another user's file or following a symlink.
    with OUTPUT.open('xb') as out:
        with tarfile.open(fileobj=out, mode='w:gz') as archive:
            for name, data in rows.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o600
                archive.addfile(info, io.BytesIO(data))
    for name, data in rows.items():
        print(json.dumps({'source': name, 'sha256': hashlib.sha256(data).hexdigest()}))
    print('EXPORTED: /tmp/sisu-public-source-review.tgz')
    print('Only three Python source files copied. No live source, settings, databases or services changed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+type(exc).__name__+'. No source or credentials printed.')
        raise SystemExit(1)
