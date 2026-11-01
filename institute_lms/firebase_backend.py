"""Sandbox Firebase Admin initialization only. No push-sending entry point."""
import hashlib
import json
import os
from pathlib import Path
import stat

PROJECT = 'sisu-lms'


def validate_metadata(data):
    if not isinstance(data, dict) or data.get('type') != 'service_account':
        raise ValueError('Expected a service-account JSON file.')
    if data.get('project_id') != PROJECT:
        raise ValueError('Credential project does not match sisu-lms.')
    if data.get('token_uri') != 'https://oauth2.googleapis.com/token':
        raise ValueError('Unexpected OAuth token endpoint.')
    if not all(isinstance(data.get(k), str) and data[k] for k in ('private_key', 'client_email', 'private_key_id')):
        raise ValueError('Service-account fields missing.')
    return data


def initialize(path, name):
    path = Path(path)
    root = Path.home() / '.sisu-secrets'
    if os.name != 'posix' or path.is_symlink() or root.is_symlink():
        raise ValueError('Protected Linux credential storage required.')
    if root.resolve() not in path.resolve().parents:
        raise ValueError('Credential must be outside the bench in protected storage.')
    for item in (path, *list(path.parents)[:list(path.parents).index(root)+1]):
        info = item.lstat()
        if item.is_symlink() or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError('Credential storage permissions are not private.')
    if path.stat().st_size > 65536:
        raise ValueError('Credential file too large.')
    data = validate_metadata(json.loads(path.read_text()))
    from firebase_admin import credentials, initialize_app
    return initialize_app(credentials.Certificate(data), {'projectId': PROJECT}, name=name)


def get_app():
    import frappe
    if frappe.local.site != 'hnb-checkout.localhost':
        raise ValueError('This Firebase setup is restricted to the sandbox site.')
    settings = frappe.conf.get('il_firebase_sandbox') or {}
    if settings.get('project_id') != PROJECT or not settings.get('credential_path'):
        raise ValueError('Firebase sandbox configuration missing.')
    from firebase_admin import get_app as existing
    name = 'sisu-sandbox-' + hashlib.sha256(settings['credential_path'].encode()).hexdigest()[:16]
    try:
        return existing(name)
    except ValueError:
        return initialize(settings['credential_path'], name)
