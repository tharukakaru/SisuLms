"""Explicitly enabled public-campus SMS; secrets remain outside the repository."""
import json,os,re,stat
from pathlib import Path
import frappe

def credentials(site):
    if os.name!='posix' or site!='sisuacademylk.com':raise ValueError('Unsupported public site')
    root=Path.home()/'.sisu-secrets'
    folder=root/'notify-live'/site
    path=folder/'credentials.json'
    for item in (root,root/'notify-live',folder,path):
        info=item.lstat()
        if item.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:
            raise ValueError('Private credential permissions required')
    if not path.is_file() or path.stat().st_size>16384:raise ValueError('Invalid credential file')
    config=json.loads(path.read_text())
    if not isinstance(config,dict) or not all(config.get(k) for k in ('user_id','api_key','sender_id')) or config['sender_id']!='SisuAcademy':
        raise ValueError('Notify credentials incomplete')
    return {k:config[k] for k in ('user_id','api_key','sender_id')}

def send(phone,message,idempotency_key=None):
    site=getattr(frappe.local,'site',None)
    if (site!='sisuacademylk.com' or frappe.conf.get('il_public_sms_enabled')!=1
        or frappe.conf.get('il_control_plane') or frappe.conf.get('il_shared_campus_enabled')!=1):
        frappe.throw('Public SMS is not enabled on this site')
    number=str(phone).strip().lstrip('+')
    if not re.fullmatch(r'947[0-9]{8}',number):frappe.throw('Enter a Sri Lankan mobile number beginning with +947.')
    try:config=credentials(site)
    except (ValueError,OSError,TypeError):frappe.throw('SMS provider configuration is unavailable')
    from .notify_adapter import send_config
    # Caller owns verification throttling or outbox reservation. Never retry an
    # uncertain acceptance automatically and never change site-global secrets.
    return send_config(config,number,message)
