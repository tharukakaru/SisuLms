"""Restricted deployment adapter: protected credentials and one permitted test recipient."""
import hashlib
import hmac
import json
import os
import re
import stat
from pathlib import Path
import frappe

SITES=('teen.sisuacademylk.com','platform.sisuacademylk.com')

def authorized_phone(value,settings):
    number=str(value).strip().lstrip('+')
    if not re.fullmatch(r'947[0-9]{8}',number):raise ValueError('Sri Lankan mobile required')
    expected=settings.get('test_recipient_sha256') if isinstance(settings,dict) else None
    if not isinstance(expected,str) or not re.fullmatch(r'[a-f0-9]{64}',expected):raise ValueError('Test recipient not configured')
    if not hmac.compare_digest(hashlib.sha256(number.encode()).hexdigest(),expected):raise ValueError('Recipient not authorized for deployment testing')
    return number

def credentials(site):
    if os.name!='posix' or site not in SITES:raise ValueError('Unsupported deployment site')
    root=Path.home()/'.sisu-secrets'
    folder=root/'notify-live'/site
    path=folder/'credentials.json'
    for item in (root,root/'notify-live',folder,path):
        info=item.lstat()
        if item.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError('Private credential permissions required')
    if not path.is_file() or path.stat().st_size>16384:raise ValueError('Invalid credential file')
    config=json.loads(path.read_text())
    if not isinstance(config,dict) or not all(config.get(k) for k in ('user_id','api_key','sender_id')) or config['sender_id']!='SisuAcademy':raise ValueError('Notify credentials incomplete')
    return {k:config[k] for k in ('user_id','api_key','sender_id')}

def send(phone,message,idempotency_key=None):
    site=getattr(frappe.local,'site',None)
    settings=frappe.conf.get('il_notify_live') or {}
    if site not in SITES or settings.get('test_mode') is not True:
        frappe.throw('Restricted SMS testing is not enabled')
    try:
        number=authorized_phone(phone,settings)
        config=credentials(site)
    except (ValueError,OSError,TypeError):
        frappe.throw('SMS recipient or protected configuration is unavailable')
    from .notify_adapter import send as delegate
    previous=frappe.conf.get('il_notify')
    existed='il_notify' in frappe.conf
    try:
        frappe.conf['il_notify']=config
        return delegate(phone=number,message=message,idempotency_key=idempotency_key)
    finally:
        if existed:frappe.conf['il_notify']=previous
        else:frappe.conf.pop('il_notify',None)
