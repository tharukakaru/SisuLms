"""Read-only source drift check before the full SISU release migration."""
import hashlib
import json
import os
import re
import tarfile
from pathlib import Path, PurePosixPath

APP = Path('/home/sisu/frappe-bench/apps/institute_lms')
ARCHIVE = Path('/tmp/sisu-public-campus-source.tgz')


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def generated_entry_matches(current, expected, app):
    """Allow only Vite entry hash changes, with real public assets present."""
    portal = app / 'institute_lms/public/portal'
    index = portal / 'index.html'
    if index.is_symlink() or not index.is_file():
        return False
    if current.replace(b'\r\n', b'\n') != index.read_bytes().replace(b'\r\n', b'\n'):
        return False
    pattern = rb'/assets/institute_lms/portal/assets/index-[A-Za-z0-9_-]+\.(?:js|css)'
    urls = re.findall(pattern, current)
    if len(urls) != 2 or not any(u.endswith(b'.js') for u in urls) or not any(u.endswith(b'.css') for u in urls):
        return False
    def normalize(value):
        return re.sub(pattern, lambda m: b'/ENTRY.' + m[0].rsplit(b'.', 1)[1], value.replace(b'\r\n', b'\n'))
    if normalize(current) != normalize(expected):
        return False
    for url in urls:
        asset = portal / 'assets' / url.decode('ascii').rsplit('/', 1)[1]
        if asset.is_symlink() or not asset.is_file() or not asset.resolve().is_relative_to(portal.resolve()):
            return False
        if not asset.stat().st_mode & 0o004:
            return False
    return True


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    with tarfile.open(ARCHIVE, 'r:gz') as archive:
        manifest = json.load(archive.extractfile('release-manifest.json'))
        for entry in archive.getmembers():
            path = PurePosixPath(entry.name)
            if path.is_absolute() or '..' in path.parts or not entry.isfile():
                raise RuntimeError('Invalid archive member')
            if entry.name != 'release-manifest.json':
                if entry.name not in manifest or digest(archive.extractfile(entry).read()) != manifest[entry.name]['release']:
                    raise RuntimeError('Archive checksum mismatch')
        conflicts = []
        changes = 0
        for rel, hashes in manifest.items():
            path = PurePosixPath(rel)
            if path.is_absolute() or '..' in path.parts:
                raise RuntimeError('Invalid manifest path')
            current = APP / rel
            if not current.resolve().is_relative_to(APP.resolve()) or current.is_symlink():
                conflicts.append(rel)
                continue
            if not current.exists():
                if hashes['previous']:
                    conflicts.append(rel)
                else:
                    changes += 1
                continue
            actual = digest(current.read_bytes())
            if actual not in hashes['previous'] + [hashes['release']]:
                if rel == 'institute_lms/www/campus.html' and generated_entry_matches(
                    current.read_bytes(), archive.extractfile(rel).read(), APP
                ):
                    print('PASS: generated campus entry differs only in validated build asset names.')
                    changes += 1
                else:
                    conflicts.append(rel)
            elif actual != hashes['release']:
                changes += 1
        print('Reviewed source files:', len(manifest))
        print('Files to update or add:', changes)
        for rel in conflicts:
            print('SOURCE CONFLICT:', rel)
        print(('BLOCKED' if conflicts else 'PASS') + ': release source compatibility')
        print('No extraction, configuration changes, migrations, restarts or messages performed.')
        print('Public signup activation is separate. This check does not establish launch readiness.')
        if conflicts:
            raise SystemExit(2)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('CHECK FAILED [' + type(exc).__name__ + ']. No live source modified.')
        raise SystemExit(1) from None
