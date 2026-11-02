"""Create an empty public Frappe site; no DNS, routing or signup activation."""
import json,os,pwd,re,secrets,select,subprocess,tempfile,time
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench');SITE='sisuacademylk.com'

def main():
    if os.name!='posix' or os.geteuid()!=0 or not (BENCH/'sites').is_dir():raise RuntimeError('Run as root on deployment server')
    import pty,termios
    target=BENCH/'sites'/SITE
    if target.exists():raise RuntimeError('Public site path already exists; nothing overwritten. Inspect before resuming.')
    data=json.loads(subprocess.check_output(['docker','inspect','sisu-public-db'],text=True))[0]
    ports=data.get('NetworkSettings',{}).get('Ports',{}).get('3306/tcp') or []
    if not any(p.get('HostIp')=='127.0.0.1' and p.get('HostPort')=='3309' for p in ports):raise RuntimeError('Unexpected database port mapping')
    env=dict(x.split('=',1) for x in data.get('Config',{}).get('Env',[]) if '=' in x)
    database_password=env.get('MARIADB_ROOT_PASSWORD') or env.get('MYSQL_ROOT_PASSWORD')
    if not database_password or '\n' in database_password:raise RuntimeError('Database root credential unavailable')
    os.umask(0o077)
    recovery=Path('/root/sisu-public-provision-isolated')
    if recovery.exists():raise RuntimeError('Recovery directory exists; inspect previous attempt before retrying')
    recovery.mkdir(mode=0o700)
    admin_password=secrets.token_urlsafe(36)
    (recovery/'administrator-password.txt').write_text(admin_password+'\n')
    prefix=['sudo','-u','sisu','-H','env','PATH=/opt/node-v24.15.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin','/usr/local/bin/bench']
    command=prefix+['new-site',SITE,'--db-host','127.0.0.1','--db-port','3309','--db-root-username','root','--no-mariadb-socket']
    master,slave=pty.openpty()
    process=subprocess.Popen(command,cwd=BENCH,stdin=slave,stdout=slave,stderr=slave,start_new_session=True)
    os.close(slave)
    pending='';sent_root=False;sent_admin=False;deadline=time.monotonic()+600
    try:
        with (recovery/'creation.log').open('w') as log:
            while process.poll() is None:
                if time.monotonic()>deadline:raise RuntimeError('Site creation timed out; inspect private log')
                if not select.select([master],[],[],1)[0]:continue
                try:chunk=os.read(master,65536).decode(errors='replace')
                except OSError:break
                # Never retain raw credential text even if a CLI echoes unexpectedly.
                log.write(chunk.replace(database_password,'[REDACTED]').replace(admin_password,'[REDACTED]'));log.flush()
                pending=(pending+chunk)[-4000:]
                tail=pending.splitlines()[-1] if pending.splitlines() else pending
                if re.search(r'(?i)password[^\r\n]*:\s*$',tail):
                    if termios.tcgetattr(master)[3]&termios.ECHO:raise RuntimeError('Password prompt is not hidden; stopped')
                    if 'administrator' in tail.lower() or ('confirm' in tail.lower() and sent_admin):
                        secret=admin_password;sent_admin=True
                    elif any(x in tail.lower() for x in ('root','mariadb','mysql')) and not sent_root:
                        secret=database_password;sent_root=True
                    else:raise RuntimeError('Unexpected password prompt; inspect private log')
                    os.write(master,(secret+'\n').encode());pending=''
                elif re.search(r'(?i)\[y/N\]\s*:\s*$',tail):
                    os.write(master,b'n\n');pending=''
            code=process.wait(timeout=30)
            if code:raise RuntimeError('Site creation failed; private log retained. Do not retry blindly.')
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=30)
        os.close(master)
    config_path=target/'site_config.json'
    cfg=json.loads(config_path.read_text())
    cfg.update(host_name='https://www.sisuacademylk.com',il_payments_paused=1,il_public_signup_enabled=0,
        il_self_signup_enabled=0,il_shared_campus_enabled=0,il_public_sms_enabled=0,
        pause_scheduler=1,mute_emails=1,maintenance_mode=1)
    identity=pwd.getpwnam('sisu')
    fd,tmp=tempfile.mkstemp(dir=target,prefix='.public-config-')
    with os.fdopen(fd,'w') as out:json.dump(cfg,out,indent=2)
    os.chmod(tmp,0o600);os.chown(tmp,identity.pw_uid,identity.pw_gid);os.replace(tmp,config_path)
    # App installation is a separate step after the reviewed release is deployed.
    print('CREATED: separate empty Frappe database for '+SITE+'.')
    print('Signup, public SMS and scheduler remain off; maintenance on; payments paused.')
    print('No staging/Teen data copied. No DNS, Nginx, messages or shared-process restart.')
    print('Private recovery files: /root/sisu-public-provision-isolated. Do not paste their contents.')
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STOPPED: '+(str(e) if isinstance(e,RuntimeError) else type(e).__name__)+'. No credentials displayed.')
        raise SystemExit(1)
