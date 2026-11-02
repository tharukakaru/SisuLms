"""Repair public build permissions and retain assets referenced by cached pages."""
import os
import re
import shutil
import subprocess
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH / 'apps/institute_lms'
BACKUP = Path('/home/sisu/.sisu-secrets/setup-ui-20261101T174849210866Z')


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    portal = APP / 'institute_lms/public/portal'
    old = BACKUP / 'institute_lms/public/portal'
    if portal.is_symlink() or not old.is_dir():
        raise RuntimeError('Expected public build and backup required')
    # Validate everything before touching permissions. This is public frontend only.
    for root in (portal, old):
        for path in root.rglob('*'):
            if path.is_symlink():
                raise RuntimeError('Unexpected symlink in frontend build')
    restored = 0
    for source in old.rglob('*'):
        target = portal / source.relative_to(old)
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            restored += 1
    portal.chmod(0o755)
    for path in portal.rglob('*'):
        path.chmod(0o755 if path.is_dir() else 0o644)
    entry = APP / 'institute_lms/www/campus.html'
    if entry.is_symlink():
        raise RuntimeError('Unexpected entry-page symlink')
    entry.chmod(0o644)
    assets = re.findall(r'(?:src|href)="(/assets/institute_lms/portal/[^"?]+)', entry.read_text())
    if not assets:
        raise RuntimeError('No frontend entry assets found')
    for asset in assets:
        path = portal / asset.split('/portal/', 1)[1]
        if not path.resolve().is_relative_to(portal.resolve()) or not path.is_file():
            raise RuntimeError('Referenced entry asset missing')
    print('PASS: public asset permissions repaired; missing previous assets restored:', restored)
    for site in ('teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-website-cache'], cwd=BENCH, check=True)
    print('PASS: website caches cleared. Hard refresh /campus. Browser rendering still needs confirmation.')
    print('Private credentials and backup permissions unchanged. No process restart or messages sent.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED [' + type(exc).__name__ + ']. Browser recovery not yet confirmed.')
        raise SystemExit(1) from None
