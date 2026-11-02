"""Package source using prior deployed archives as explicit drift baselines."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent/'release-candidate'


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def main():
    previous = {}
    for name in ('sisu-release-source.tgz', 'sisu-ui-update.tgz'):
        with tarfile.open(OUT/name) as archive:
            for member in archive.getmembers():
                if member.isfile() and not member.name.endswith('manifest.json'):
                    previous.setdefault(member.name, []).append(digest(archive.extractfile(member).read()))
    # Reviewed server export: existing single-site guards are retained by the
    # release; additional shared-campus checks are conditional on shared mode.
    reviewed = {
        'native_access.py': 'efb60f9a10a02e1127d98723a0a1053692e5163bad4174b0560d9af1d133b056',
        'portal_session.py': '577ed0c557c02cc78e33d55bcc6474cfb8a6aae40e43b570469811fa0ebdee1a',
        'validation.py': 'ec45942ea0dc0d42c0bba27ccab7ac33ce8eb8d3f06510a51a90b2d994ab5a5b',
    }
    with tarfile.open(OUT/'sisu-public-source-review.tgz') as archive:
        if sorted(archive.getnames()) != sorted(reviewed):
            raise ValueError('Unexpected reviewed export contents')
        for name, expected in reviewed.items():
            data = archive.extractfile(name).read()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Reviewed source changed: '+name)
            previous.setdefault('institute_lms/'+name, []).append(digest(data))
    files = {}
    for rel in previous:
        path = ROOT/rel
        if path.is_file() and not path.is_symlink():
            files[rel] = path.read_bytes()
    for folder, suffixes in (('institute_lms', {'.py', '.json'}), ('frontend/src', {'.vue', '.js'})):
        for path in (ROOT/folder).rglob('*'):
            if path.is_file() and not path.is_symlink() and path.suffix in suffixes and '__pycache__' not in path.parts and 'public' not in path.relative_to(ROOT).parts:
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    manifest = {rel: {'previous': sorted(set(previous.get(rel, []))), 'release': digest(data)} for rel, data in sorted(files.items())}
    target = OUT/'sisu-public-campus-source.tgz'
    with tarfile.open(target, 'w:gz') as archive:
        for rel, data in sorted(files.items()):
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
        data = json.dumps(manifest, sort_keys=True).encode()
        info = tarfile.TarInfo('release-manifest.json')
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    print('PACKAGED:', len(files), 'source files; bytes:', target.stat().st_size)
    print('SHA256:', hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
