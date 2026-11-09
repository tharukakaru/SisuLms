"""Bounded public upload allocation; optional server-local reuse of private media.

No credentials printed, provider calls, messages, payments or database changes.
Source/config backups are private. Refuses to replace an existing different
allocation or media setting. Restart processes after this script succeeds.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH/'apps/institute_lms'
PUBLIC = BENCH/'sites/sisuacademylk.com/site_config.json'
STAGING = BENCH/'sites/staging.sisuacademylk.com/site_config.json'
SOURCE = APP/'institute_lms/account_storage.py'
PAYLOAD = Path('/tmp/sisu-account-storage.py')
OLD_SHA = 'c13a7f617b4ac72264ed1779ac48f2099018fef0d97e635674af075d62bf11c3'
NEW_SHA = 'e890215fcb7f0597352cc1a308f8f532047ef247b0526ca4ba3facdac0c7b3ce'


def digest(raw):
    return hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()


def atomic(path, raw, mode):
    temporary = path.with_name(path.name+'.sisu-storage-new')
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode), 'wb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    path.chmod(mode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-staging-media', action='store_true')
    args = parser.parse_args()
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o077)
    for path in (PUBLIC, STAGING, SOURCE, PAYLOAD):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError('Expected regular configuration/source files')
    raw = PUBLIC.read_bytes()
    config = json.loads(raw)
    staged = json.loads(STAGING.read_bytes())
    if config.get('il_shared_campus_enabled') != 1 or config.get('il_tenant_id') or config.get('il_control_plane'):
        raise RuntimeError('Expected standalone shared public campus')
    if not config.get('il_payments_paused') or (config.get('il_cybersource') or {}).get('enabled'):
        raise RuntimeError('Expected public gateway payments disabled')
    allocation = 5*1024**3
    if config.get('il_account_storage_bytes') not in (None, allocation):
        raise RuntimeError('Existing allocation differs; not overwritten')
    config['il_account_storage_bytes'] = allocation
    if args.reuse_staging_media:
        media = staged.get('il_private_media_s3') or {}
        recording = staged.get('il_live_recording_s3') or {}
        for value in (media, recording):
            if not isinstance(value, dict) or not all(value.get(k) for k in ('bucket', 'region', 'access_key', 'secret')):
                raise RuntimeError('Staging media configuration incomplete')
        for field in ('bucket', 'region', 'access_key', 'secret'):
            if media[field] != recording[field]:
                raise RuntimeError('Staging recording and playback storage differ; review required')
        if media.get('endpoint_url', '') != recording.get('endpoint', ''):
            raise RuntimeError('Staging storage endpoints differ; review required')
        for endpoint in (media.get('endpoint_url'), recording.get('endpoint')):
            if endpoint:
                parsed = urlsplit(endpoint)
                if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                    raise RuntimeError('Trusted HTTPS media endpoint required')
        hosts = staged.get('il_private_video_hosts')
        if not isinstance(hosts, list) or not hosts or not all(isinstance(h, str) and h and '/' not in h and '*' not in h for h in hosts):
            raise RuntimeError('Exact staging playback host allowlist required')
        if staged.get('il_private_video_adapter') != 'institute_lms.private_media.grant':
            raise RuntimeError('Expected protected playback adapter')
        # Never silently mix a different public LiveKit service with staging's
        # egress storage. The already-installed public live credentials stay put.
        for key in ('il_livekit_url', 'il_livekit_api_key', 'il_livekit_api_secret'):
            if not config.get(key) or config[key] != staged.get(key):
                raise RuntimeError('Public/staging LiveKit configuration differs; review required')
        for key in ('il_private_media_s3', 'il_live_recording_s3', 'il_private_video_adapter', 'il_private_video_hosts'):
            if config.get(key) not in (None, '', [], {}) and config[key] != staged[key]:
                raise RuntimeError('Existing public media setting differs; not overwritten')
            config[key] = staged[key]
    source = SOURCE.read_bytes()
    payload = PAYLOAD.read_bytes()
    if digest(source) not in (OLD_SHA, NEW_SHA) or digest(payload) != NEW_SHA:
        raise RuntimeError('Source version conflict; not overwritten')
    compile(payload, str(SOURCE), 'exec')
    root = Path.home()/'.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise RuntimeError('Private backup directory required')
    backup = root/('public-learning-storage-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700)
    (backup/'site_config.json').write_bytes(raw)
    (backup/'account_storage.py').write_bytes(source)
    for path in backup.iterdir():
        path.chmod(0o600)
    if PUBLIC.read_bytes() != raw or SOURCE.read_bytes() != source:
        raise RuntimeError('Configuration changed during preparation; retry after review')
    try:
        atomic(SOURCE, payload, 0o644)
        atomic(PUBLIC, (json.dumps(config, indent=2)+'\n').encode(), 0o600)
        import frappe
        os.chdir(BENCH/'sites')
        frappe.init(site='sisuacademylk.com', sites_path=str(BENCH/'sites'))
        frappe.connect()
        try:
            from institute_lms.account_storage import configured
            from institute_lms.usage import used
            if not configured():
                raise RuntimeError('Public storage allocation did not activate')
            if used('storage_bytes') >= allocation:
                raise RuntimeError('Existing usage exceeds chosen allocation; configuration restored')
        finally:
            frappe.db.rollback()
            frappe.destroy()
    except Exception:
        atomic(SOURCE, source, 0o644)
        atomic(PUBLIC, raw, 0o600)
        raise
    print('CONFIGURED: public shared-campus uploads with a 5 GiB infrastructure ceiling; legacy usage billing unchanged.')
    print('CONFIGURED: private recording/playback settings reused server-side.' if args.reuse_staging_media else 'UNCHANGED: recording configuration.')
    print('Private backup: '+str(backup))
    print('Restart web and workers. No payment settings, WhatsApp, accounts or database records changed; no provider requests or messages.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+type(exc).__name__+'. '+(str(exc) if isinstance(exc, RuntimeError) else 'No configuration values or credentials displayed.'))
        raise SystemExit(1) from None
