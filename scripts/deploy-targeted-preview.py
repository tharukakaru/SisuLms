"""Install a verified incremental merged snapshot ONLY in the isolated invoice preview bench."""
import hashlib, json, os, pwd, shutil, subprocess, tarfile, time, urllib.request
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
ROOT=Path('/home/sisu/frappe-invoice-test')
PROD=Path('/home/sisu/frappe-bench')
APP=ROOT/'apps/institute_lms'
SITE='invoice-test.local'
UNIT='sisu-invoice-preview.service'
ARCHIVE=Path('/tmp/sisu-targeted-preview.tgz')
DIGEST='44cd93ddb53643b6e2e7d2dc449d31e4dbae9c4fc25a8ad7a7253d72f9dc5536'

def run(cmd, log, user=True):
    subprocess.run((['sudo','-H','-u','sisu','--'] if user else [])+cmd,cwd=ROOT,stdout=log,stderr=log,check=True)
def bench(*args): return ['/usr/local/bin/bench','--site',SITE,*args]

def main():
    if os.geteuid()!=0: raise RuntimeError('Run as root')
    import fcntl
    lock=os.open('/var/lock/sisu-isolated-preview.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.umask(0o077)
    if ROOT.resolve()==PROD.resolve(): raise RuntimeError('Preview is production')
    if ROOT.is_symlink() or APP.is_symlink() or ROOT.resolve() in PROD.resolve().parents:
        raise RuntimeError('Unexpected preview layout')
    common=json.loads((ROOT/'sites/common_site_config.json').read_text())
    production=json.loads((PROD/'sites/common_site_config.json').read_text())
    config_path=ROOT/'sites'/SITE/'site_config.json'
    config=json.loads(config_path.read_text())
    merged={**common,**config}
    for key in ('redis_cache','redis_queue','redis_socketio'):
        if not common.get(key) or common[key]==production.get(key): raise RuntimeError('Redis isolation not confirmed')
    for path in (PROD/'sites').glob('*/site_config.json'):
        other={**production,**json.loads(path.read_text())}
        if all(merged.get(k,default)==other.get(k,default) for k,default in [('db_host','127.0.0.1'),('db_port',3306),('db_name',None)]):
            raise RuntimeError('Preview shares a production database')
    if (ROOT/'env').resolve()==(PROD/'env').resolve(): raise RuntimeError('Shared Python environment')
    for name in ('frappe','payments','lms','institute_lms'):
        if (ROOT/'apps'/name).resolve()==(PROD/'apps'/name).resolve(): raise RuntimeError('Shared application source')
    service=subprocess.check_output(['systemctl','show',UNIT,'-p','WorkingDirectory','--value'],text=True).strip()
    if Path(service).resolve() not in (ROOT.resolve(),(ROOT/'sites').resolve()):
        raise RuntimeError('Unexpected preview service working directory: '+service)
    subprocess.run(['sudo','-H','-u','sisu','--',str(ROOT/'env/bin/python'),'-m','pip','check'],cwd=ROOT,check=True)
    if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()!=DIGEST: raise RuntimeError('Archive checksum mismatch')
    payload={}
    with tarfile.open(ARCHIVE) as archive:
        for item in archive.getmembers():
            p=PurePosixPath(item.name)
            if p.is_absolute() or '..' in p.parts or not (item.name.startswith('institute_lms/') or item.name=='institute_lms' or item.name=='pyproject.toml' or item.name=='preview-manifest.json'):
                raise RuntimeError('Unexpected archive path')
            if item.isdir(): continue
            if not item.isfile() or item.name in payload: raise RuntimeError('Unexpected archive entry')
            dst=APP/item.name
            if any(parent.is_symlink() for parent in [dst,*list(dst.parents)[:len(p.parts)]]): raise RuntimeError('Symlink destination')
            payload[item.name]=archive.extractfile(item).read()
    manifest=json.loads(payload.pop('preview-manifest.json'))
    for name, expected in manifest.items():
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or not (name.startswith('institute_lms/') or name=='pyproject.toml'):
            raise RuntimeError('Unexpected manifest path')
        dst=APP/name
        if any(parent.is_symlink() for parent in [dst,*list(dst.parents)[:len(p.parts)]]):
            raise RuntimeError('Symlink manifest destination')
        data=payload[name] if name in payload else dst.read_bytes()
        if expected['text']: data=data.replace(b'\r\n',b'\n')
        if hashlib.sha256(data).hexdigest()!=expected['sha256']:
            raise RuntimeError('Preview dependency mismatch: '+name)
    if not set(payload).issubset(manifest): raise RuntimeError('Incomplete manifest')
    print('Preview source and asset dependencies verified.',flush=True)
    account=pwd.getpwnam('sisu')
    backup=Path('/home/sisu/.sisu-secrets')/('isolated-preview-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700);os.chown(backup,account.pw_uid,account.pw_gid)
    print('Preview log: '+str(backup/'deploy.log'),flush=True)
    with (backup/'deploy.log').open('w') as log:
        try:
            # Preserve configuration and source before changing this test environment.
            shutil.copy2(config_path,backup/'site_config.private.json')
            with tarfile.open(backup/'source-before.tgz','w:gz') as saved:
                saved.add(APP/'institute_lms',arcname='institute_lms')
                saved.add(APP/'pyproject.toml',arcname='pyproject.toml')
            run(bench('set-maintenance-mode','on'),log)
            run(['systemctl','stop',UNIT],log,False)
            run(bench('backup','--with-files'),log)
            with tarfile.open(backup/'site-before.tgz','w:gz') as saved:
                saved.add(ROOT/'sites'/SITE,arcname=SITE)
            config.update(disable_scheduler=1,mute_emails=1,il_payments_paused=1,
                          il_shared_campus_enabled=1,il_control_plane=0,
                          il_notify={},il_platform_sms_enabled=0,il_cybersource={'enabled':False})
            config_path.write_text(json.dumps(config,indent=2));os.chown(config_path,account.pw_uid,account.pw_gid)
            for name,data in payload.items():
                dst=APP/name;dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes(data);os.chown(dst,account.pw_uid,account.pw_gid);dst.chmod(0o644)
                for parent in dst.parents:
                    if parent==APP: break
                    os.chown(parent,account.pw_uid,account.pw_gid);parent.chmod(0o755)
            run([str(ROOT/'env/bin/python'),'-c','import pyotp, reportlab, pypdf, cryptography'],log)
            run(bench('migrate'),log)
            run([str(ROOT/'env/bin/python'),'-m','pip','check'],log)
            run(bench('clear-cache'),log);run(bench('clear-website-cache'),log)
            run(bench('set-maintenance-mode','off'),log)
            run(['systemctl','start',UNIT],log,False)
            import re
            assets=re.findall(r'(?:src|href)="(/assets/institute_lms/portal/assets/index-[^"]+\.(?:js|css))"',(APP/'institute_lms/www/campus.html').read_text())
            if len(assets)!=2: raise RuntimeError('Unexpected entry assets')
            for attempt in range(12):
                try:
                    with urllib.request.urlopen('https://preview.sisuacademylk.com/campus',timeout=20) as response: html=response.read().decode()
                    if not all(a in html for a in assets): raise RuntimeError('Preview entry mismatch')
                    for asset in assets:
                        with urllib.request.urlopen('https://preview.sisuacademylk.com'+asset,timeout=20) as response: data=response.read()
                        name='institute_lms/public/'+asset.removeprefix('/assets/institute_lms/')
                        if data!=(APP/name).read_bytes(): raise RuntimeError('Preview asset mismatch')
                    break
                except Exception:
                    if attempt==11: raise
                    time.sleep(5)
            print('PREVIEW READY: https://preview.sisuacademylk.com/campus - targeted live-baseline candidate (approval + removal only). Production files/services untouched. Test payments, SMS and outgoing email disabled; scheduler disabled. Browser workflow testing still required.',flush=True)
        except Exception:
            import traceback
            traceback.print_exc(file=log)
            print('PREVIEW STOPPED: inspect '+str(backup/'deploy.log')+'. Production unchanged.',flush=True)
            raise
if __name__=='__main__': main()
