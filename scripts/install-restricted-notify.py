"""Install an allowlisted SMS adapter on the two named sites. No send calls."""
import getpass,hashlib,json,logging,os,stat,tempfile,types,warnings
from datetime import datetime,timezone
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
SITES=('teen.sisuacademylk.com','platform.sisuacademylk.com')
ADAPTER='"""Restricted deployment adapter: protected credentials and one permitted test recipient."""\nimport hashlib\nimport hmac\nimport json\nimport os\nimport re\nimport stat\nfrom pathlib import Path\nimport frappe\n\nSITES=(\'teen.sisuacademylk.com\',\'platform.sisuacademylk.com\')\n\ndef authorized_phone(value,settings):\n    number=str(value).strip().lstrip(\'+\')\n    if not re.fullmatch(r\'947[0-9]{8}\',number):raise ValueError(\'Sri Lankan mobile required\')\n    expected=settings.get(\'test_recipient_sha256\') if isinstance(settings,dict) else None\n    if not isinstance(expected,str) or not re.fullmatch(r\'[a-f0-9]{64}\',expected):raise ValueError(\'Test recipient not configured\')\n    if not hmac.compare_digest(hashlib.sha256(number.encode()).hexdigest(),expected):raise ValueError(\'Recipient not authorized for deployment testing\')\n    return number\n\ndef credentials(site):\n    if os.name!=\'posix\' or site not in SITES:raise ValueError(\'Unsupported deployment site\')\n    root=Path.home()/\'.sisu-secrets\'\n    folder=root/\'notify-live\'/site\n    path=folder/\'credentials.json\'\n    for item in (root,root/\'notify-live\',folder,path):\n        info=item.lstat()\n        if item.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError(\'Private credential permissions required\')\n    if not path.is_file() or path.stat().st_size>16384:raise ValueError(\'Invalid credential file\')\n    config=json.loads(path.read_text())\n    if not isinstance(config,dict) or not all(config.get(k) for k in (\'user_id\',\'api_key\',\'sender_id\')) or config[\'sender_id\']!=\'SisuAcademy\':raise ValueError(\'Notify credentials incomplete\')\n    return {k:config[k] for k in (\'user_id\',\'api_key\',\'sender_id\')}\n\ndef send(phone,message,idempotency_key=None):\n    site=getattr(frappe.local,\'site\',None)\n    settings=frappe.conf.get(\'il_notify_live\') or {}\n    if site not in SITES or settings.get(\'test_mode\') is not True:\n        frappe.throw(\'Restricted SMS testing is not enabled\')\n    try:\n        number=authorized_phone(phone,settings)\n        config=credentials(site)\n    except (ValueError,OSError,TypeError):\n        frappe.throw(\'SMS recipient or protected configuration is unavailable\')\n    from .notify_adapter import send as delegate\n    previous=frappe.conf.get(\'il_notify\')\n    existed=\'il_notify\' in frappe.conf\n    try:\n        frappe.conf[\'il_notify\']=config\n        return delegate(phone=number,message=message,idempotency_key=idempotency_key)\n    finally:\n        if existed:frappe.conf[\'il_notify\']=previous\n        else:frappe.conf.pop(\'il_notify\',None)\n'

def atomic(path,text):
    fd,name=tempfile.mkstemp(prefix='.sisu-notify-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as out:out.write(text);out.flush();os.fsync(out.fileno())
        os.chmod(name,0o600);os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    os.umask(0o077);logging.disable(logging.CRITICAL);warnings.simplefilter('error',getpass.GetPassWarning)
    import re,frappe
    phone=re.sub(r'[ ()-]','',getpass.getpass('Only permitted SMS test mobile, 07XXXXXXXX or +947XXXXXXXX (hidden): ').strip())
    if re.fullmatch(r'07[0-9]{8}',phone):phone='94'+phone[1:]
    phone=phone.lstrip('+')
    if not re.fullmatch(r'947[0-9]{8}',phone):raise ValueError('Invalid mobile format')
    settings={'test_mode':True,'test_recipient_sha256':hashlib.sha256(phone.encode()).hexdigest()}
    module=types.ModuleType('prepared_notify_live');exec(compile(ADAPTER,'notify_live.py','exec'),module.__dict__)
    target=BENCH/'apps/institute_lms/institute_lms/notify_live.py'
    if target.is_symlink() or not target.parent.resolve().is_relative_to(Path.home()):raise ValueError('Unexpected application location')
    if target.exists() and target.read_text()!=ADAPTER:raise ValueError('Adapter source conflict')
    snapshots={}
    os.chdir(BENCH/'sites')
    for site in SITES:
        try:
            frappe.init(site=site,sites_path=str(BENCH/'sites'));frappe.connect()
            module.credentials(site)
            if frappe.get_hooks('il_send_verification_sms'):raise ValueError('Existing SMS hook needs review')
            path=BENCH/'sites'/site/'site_config.json'
            info=path.lstat()
            if path.is_symlink() or info.st_uid!=os.getuid():raise ValueError('Unexpected site configuration ownership')
            raw=path.read_text();cfg=json.loads(raw)
            if cfg.get('il_sms_adapter') not in (None,'','institute_lms.notify_live.send'):raise ValueError('Existing adapter needs review')
            if cfg.get('il_notify_live') not in (None,settings):raise ValueError('Existing recipient setting differs')
            if frappe.db.exists('DocType','IL Notification') and frappe.db.count('IL Notification',{'channel':'SMS','status':['not in',['Sent','Delivered','Cancelled']]}):raise ValueError('Existing SMS outbox requires review before activation')
            snapshots[site]=(path,raw,cfg)
            print('PASS: '+site+' protected credentials and SMS preflight.')
        finally:frappe.destroy()
    backup=Path.home()/'.sisu-secrets/notify-adapter-backups'
    backup.mkdir(mode=0o700,exist_ok=True)
    if backup.is_symlink() or backup.stat().st_uid!=os.getuid() or stat.S_IMODE(backup.stat().st_mode)&0o077:raise ValueError('Private backup directory required')
    saved=backup/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');saved.mkdir(mode=0o700)
    for site,(path,raw,cfg) in snapshots.items():(saved/(site+'.json')).write_text(raw)
    if not target.exists():atomic(target,ADAPTER)
    for site,(path,raw,cfg) in snapshots.items():
        if path.read_text()!=raw:raise ValueError('Concurrent site configuration change')
        cfg['il_sms_adapter']='institute_lms.notify_live.send';cfg['il_notify_live']=settings
        atomic(path,json.dumps(cfg,indent=2)+'\n')
        print('INSTALLED: '+site+' — only the entered test mobile is permitted.')
    print('No SMS sent. Other recipients are blocked. Existing workers may need a controlled restart before reading new settings.')

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print('INSTALL STOPPED ['+type(exc).__name__+']. No credentials printed. Do not assume both targets changed.');raise SystemExit(1) from None
