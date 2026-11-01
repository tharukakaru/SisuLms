"""Restricted sandbox SMS credentials and single-recipient boundary."""
import json
import os
import stat
from pathlib import Path
import frappe


def credentials():
    if frappe.local.site != 'hnb-checkout.localhost' or os.name != 'posix':
        raise ValueError('Sandbox Linux storage required')
    path = Path(frappe.conf.get('il_notify_sandbox_credentials') or '')
    root = Path.home()/'.sisu-secrets'
    if not path.is_absolute() or root not in path.parents:
        raise ValueError('Private credential path required')
    for item in (path, *path.parents):
        info = item.lstat()
        if item.is_symlink() or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError('Private owner-only credential storage required')
        if item == root:break
    if path.stat().st_size > 8192:raise ValueError('Invalid credential file')
    return json.loads(path.read_text())


def send(phone,message,idempotency_key=None):
    config=credentials()
    if phone != config.get('test_phone'):
        frappe.throw('Only the authorized sandbox test phone can receive SMS')
    from .notify_adapter import send_config
    return send_config(config,phone,message)
