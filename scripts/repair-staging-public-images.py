"""Repair only staging public-directory traversal and verify saved fixture images."""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE = 'staging.sisuacademylk.com'
USER = 'sisu.student.test+hnb@gmail.com'
ROOT = Path('/home/sisu/frappe-bench/sites') / SITE


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    import frappe
    import requests
    public = ROOT / 'public'
    targets = [public, public / 'files']
    # Do not follow a site or public-directory symlink into another location.
    if ROOT.is_symlink() or ROOT.resolve() != ROOT:
        raise RuntimeError('Unexpected site directory')
    for target in targets:
        if target.is_symlink() or not target.is_dir() or target.resolve() != target:
            raise RuntimeError('Unexpected public directory')
        if target.stat().st_uid != os.getuid():
            raise RuntimeError('Public directory is not owned by sisu')
    os.chdir(ROOT.parent)
    frappe.init(site=SITE, sites_path=str(ROOT.parent))
    frappe.connect()
    try:
        rooms = frappe.get_all('IL Classroom', filters={'owner_user': USER},
                               fields=['name', 'profile_image', 'cover_image'], limit_page_length=10)
        images = []
        for room in rooms:
            for field in ('profile_image', 'cover_image'):
                value = room.get(field)
                if not value:
                    continue
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not parsed.path.startswith('/files/'):
                    raise RuntimeError('Unexpected classroom image URL')
                path = public / unquote(parsed.path).lstrip('/')
                if path.is_symlink() or public.resolve() not in path.resolve().parents or not path.is_file():
                    raise RuntimeError('Unexpected classroom image file')
                if path.stat().st_size > 5 * 1024 * 1024:
                    raise RuntimeError('Image exceeds verification limit')
                images.append((room.name, field, parsed.path, hashlib.sha256(path.read_bytes()).hexdigest()))
        if not images:
            raise RuntimeError('No saved test classroom images to verify')
        for target in targets:
            previous = oct(target.stat().st_mode & 0o777)
            target.chmod(0o755)
            print(json.dumps({'directory': str(target.relative_to(ROOT)), 'before': previous, 'after': '0o755'}))
        failed = False
        for room, field, url, expected in images:
            try:
                with requests.get('https://' + SITE + url, timeout=(5, 20),
                                  allow_redirects=False, stream=True) as response:
                    body = response.raw.read(5 * 1024 * 1024 + 1)
                    ok = (response.status_code == 200
                          and response.headers.get('Content-Type', '').split(';')[0] == 'image/webp'
                          and hashlib.sha256(body).hexdigest() == expected)
                    print(json.dumps({'classroom': room, 'field': field,
                                      'http_status': response.status_code, 'saved_image_verified': ok}))
                    failed = failed or not ok
            except requests.RequestException as exc:
                failed = True
                print(json.dumps({'field': field, 'http_check_error': type(exc).__name__}))
        if failed:
            print('PUBLIC DIRECTORY PERMISSIONS REPAIRED; HTTPS verification still failed. Send this output for routing diagnosis.')
            return 1
        print('FIXED: both public directories are readable by the web server; saved classroom images verified over HTTPS.')
        print('Hard-refresh the classroom. No re-upload or web restart needed. Private files and database records unchanged.')
        return 0
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        raise SystemExit('STOPPED: ' + type(exc).__name__ + '; no credentials displayed.') from None
