"""Pause online payments on the three existing deployment sites."""
import json,os,stat,tempfile
from pathlib import Path
from datetime import datetime,timezone
BENCH=Path('/home/sisu/frappe-bench')
SITES=('teen.sisuacademylk.com','platform.sisuacademylk.com','staging.sisuacademylk.com')
def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu on deployment server')
    os.umask(0o077)
    records=[]
    for site in SITES:
        path=BENCH/'sites'/site/'site_config.json'
        info=path.lstat()
        if path.is_symlink() or info.st_uid!=os.getuid():raise RuntimeError('Unexpected config ownership')
        original=path.read_bytes();cfg=json.loads(original)
        if cfg.get('il_whatsapp_token') or cfg.get('il_whatsapp_phone_id'):raise RuntimeError('WhatsApp configuration changed; review required')
        cfg['il_payments_paused']=1
        records.append((site,path,original,cfg))
    root=Path.home()/'.sisu-secrets'
    root.mkdir(mode=0o700,exist_ok=True)
    if root.is_symlink() or stat.S_IMODE(root.stat().st_mode)&0o077:raise RuntimeError('Private backup directory required')
    backup=root/('payment-pause-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700)
    for site,path,original,cfg in records:
        saved=backup/(site+'.json');saved.write_bytes(original);saved.chmod(0o600)
    for site,path,original,cfg in records:
        if path.read_bytes()!=original:raise RuntimeError('Concurrent configuration change; stop and inspect')
        fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.payment-pause-')
        try:
            with os.fdopen(fd,'w') as out:
                json.dump(cfg,out,indent=2);out.flush();os.fsync(out.fileno())
            os.chmod(tmp,0o600);os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        print('CONFIGURED: '+site+' payment pause; WhatsApp remains unconfigured.')
    print('Private backups saved. Restart bench processes to reload settings; verify checkout after restart.')
    print('No messages, subscriptions, balances or customer records changed.')
if __name__=='__main__':main()
