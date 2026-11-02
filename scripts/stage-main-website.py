"""Stage the reviewed marketing website without changing DNS or active Nginx."""
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ARCHIVE = Path('/tmp/sisu-main-website.tgz')
ROOT = Path('/var/www/sisu-marketing-releases')
EXTENSIONS = {'.html', '.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.woff2', '.mp4', '.webm', '.ico'}


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root on the deployment server')
    os.umask(0o022)
    if ROOT.is_symlink():
        raise RuntimeError('Unexpected release-root symlink')
    ROOT.mkdir(mode=0o755, exist_ok=True)
    target = ROOT / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    with tarfile.open(ARCHIVE, 'r:gz') as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(names) != len(set(names)) or len(names) > 500:
            raise RuntimeError('Unexpected website archive')
        for member in members:
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or path.suffix.lower() not in EXTENSIONS:
                raise RuntimeError('Unsafe website archive entry')
        if sum(m.size for m in members) > 100 * 1024**2:
            raise RuntimeError('Website archive exceeds expected size')
        for name in ('index.html', 'app.js', 'style.css', 'theme.css', 'students/index.html', 'teachers/index.html', 'institutes/index.html', 'contact/index.html'):
            if name not in names:
                raise RuntimeError('Website page missing')
        app = archive.extractfile('app.js').read().decode()
        if '/campus?signup=1' not in app or "const base='';" not in app:
            raise RuntimeError('Expected same-host LMS links missing')
        target.mkdir(mode=0o755)
        for member in members:
            path = target / member.name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.extractfile(member).read())
            path.chmod(0o644)
    print('STAGED:', target)
    print('Website pages and same-host LMS links checked.')
    print('Not published: no DNS, Nginx, certificate, LMS database or account changes.')
    print('Public /campus must be implemented and verified before the domain is switched.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED [' + type(exc).__name__ + ']. Existing websites unchanged.')
        raise SystemExit(1) from None
