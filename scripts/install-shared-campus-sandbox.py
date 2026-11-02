"""Install reviewed backend functions only into the named local sandbox."""
import ast
import hashlib
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

PAYLOAD_SHA = '0164173c8d2dd692ca48695d857123c5921a97a9016053c4f7ba80d8e09c0a9c'
NAMES = {'api.py','saas.py','account_billing.py','native_access.py','portal_session.py',
         'teaching.py','campus_context.py','campus_join.py','campus_teachers.py',
         'membership_write.py','institute_coverage.py','validation.py','campus_provisioning.py'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replace(path, data, mode):
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def main():
    bench = (Path.home() / 'sisu-hnb-sandbox-bench').resolve()
    if os.name != 'posix' or Path.cwd().resolve() != bench:
        raise ValueError('Local sandbox only')
    config = json.loads((bench/'sites/hnb-checkout.localhost/site_config.json').read_text())
    if config.get('il_control_plane') or config.get('il_shared_campus_enabled'):
        raise ValueError('Expected disabled shared mode on local sandbox')
    raw = Path(__file__).with_name('shared-campus-sandbox-payload.json').read_bytes()
    if digest(raw) != PAYLOAD_SHA:raise ValueError('Payload changed')
    payload = json.loads(raw)
    if set(payload) != NAMES:raise ValueError('Unexpected payload files')
    app = (bench/'apps/institute_lms/institute_lms').resolve(strict=True)
    previous = {}; changes = {}
    for name, item in payload.items():
        path = app/name
        if path.is_symlink():raise ValueError('Symlink target')
        data = item['text'].encode('utf-8')
        ast.parse(item['text'])
        current = path.read_bytes() if path.exists() else None
        if current == data:continue
        if (digest(current) if current is not None else None) != item['before']:
            print('BLOCKED: source changed since review: '+name)
            return 1
        previous[name] = (current, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        changes[name] = data
    if not changes:
        print('PASS: reviewed sandbox backend already installed; shared mode remains off.')
        return 0
    backup = Path.home()/'.sisu-secrets'/('shared-campus-source-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True, mode=0o700, exist_ok=False)
    os.chmod(backup,0o700)
    for name,(data,mode) in previous.items():
        if data is not None:
            (backup/name).write_bytes(data);os.chmod(backup/name,0o600)
    (backup/'new-files.json').write_text(json.dumps([n for n,(data,_) in previous.items() if data is None]))
    os.chmod(backup/'new-files.json',0o600)
    applied=[]
    try:
        for name,data in changes.items():
            replace(app/name,data,previous[name][1]);applied.append(name)
    except Exception:
        for name in reversed(applied):
            data,mode=previous[name]
            if data is None:(app/name).unlink()
            else:replace(app/name,data,mode)
        raise
    print(f'INSTALLED: {len(applied)} reviewed sandbox backend files.')
    print('BACKUP: '+str(backup))
    print('Shared mode remains OFF. No database writes, messages, migrations or restarts.')
    print('Real Frappe integration test is still required. Do not enable shared mode yet.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'BLOCKED: sandbox install [{type(error).__name__}]. No credentials printed.')
        raise SystemExit(1)
