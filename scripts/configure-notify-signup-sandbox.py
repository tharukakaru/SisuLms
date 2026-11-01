"""Configure restricted Notify SMS and the sandbox privacy notice; sends nothing."""
import getpass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import warnings
from datetime import datetime,timezone

SITE='hnb-checkout.localhost'
FILES=('institute_lms/notify_adapter.py','institute_lms/notify_sandbox.py',
       'institute_lms/www/sandbox_privacy.py','institute_lms/www/sandbox_privacy.html')

def private_dir(path):
    if path.is_symlink():raise ValueError('Unsafe storage')
    path.mkdir(mode=0o700,exist_ok=True)
    info=path.stat()
    if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError('Storage is not owner-only')

def atomic_json(path,data):
    if path.is_symlink():raise ValueError('Unsafe file')
    fd,name=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w') as handle:
            json.dump(data,handle);handle.flush();os.fsync(handle.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def main():
    os.umask(0o077);logging.disable(logging.CRITICAL)
    warnings.simplefilter('error',getpass.GetPassWarning)
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise ValueError('Run in sandbox bench')
    source=Path(__file__).resolve().parents[1];app=bench/'apps/institute_lms'
    baseline=json.loads((source/'scripts/notify-baseline.json').read_text())
    for name in FILES:
        target=app/name
        if target.exists() and target.read_text().strip()!=(source/name).read_text().strip():
            if hashlib.sha256(target.read_text().strip().encode()).hexdigest()!=baseline.get(name):
                print('BLOCKED: source conflict in '+name);return
    config_path=bench/'sites'/SITE/'site_config.json'
    config=json.loads(config_path.read_text())
    if config.get('il_sms_adapter') not in (None,'','institute_lms.notify_adapter.send','institute_lms.notify_sandbox.send'):
        raise ValueError('Existing adapter requires review')
    user_id=getpass.getpass('Notify User ID (hidden; Settings > API Keys): ').strip()
    api_key=getpass.getpass('Notify API key (hidden): ').strip()
    phone=getpass.getpass('Your authorized test mobile, +94 followed by 9 digits (hidden): ').strip()
    if not user_id.isascii() or not user_id.isdigit() or not api_key or len(api_key)>1024 or any(c.isspace() for c in api_key):raise ValueError('Invalid credential fields')
    if not re.fullmatch(r'\+94\d{9}',phone):raise ValueError('Invalid test phone')
    root=Path.home()/'.sisu-secrets';private_dir(root)
    folder=root/'notify-sandbox';private_dir(folder)
    backup=folder/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');private_dir(backup)
    subprocess.run(['bench','--site',SITE,'backup','--backup-path',str(backup)],cwd=bench,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    import frappe
    os.chdir(bench/'sites');frappe.init(site=SITE,sites_path=str(bench/'sites'));frappe.connect()
    try:
        policy=frappe.get_single('IL Portal Settings')
        if policy.privacy_policy_url and policy.privacy_policy_url!='/sandbox_privacy':
            raise ValueError('Existing privacy notice requires review')
        for name in FILES:
            target=app/name
            if target.exists():
                saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text((source/name).read_text())
        credential=folder/'credentials.json'
        if credential.exists():shutil.copy2(credential,backup/'credentials.json')
        atomic_json(credential,dict(user_id=user_id,api_key=api_key,sender_id='SisuAcademy',test_phone=phone))
        # Only a path is placed in ordinary site configuration/backups.
        config=json.loads(config_path.read_text())
        config.update(il_sms_adapter='institute_lms.notify_sandbox.send',il_notify_sandbox_credentials=str(credential))
        atomic_json(config_path,config)
        policy.privacy_policy_url='/sandbox_privacy';policy.privacy_policy_version='sandbox-2026-10-31-v1'
        policy.save(ignore_permissions=True);frappe.db.commit();frappe.clear_cache()
        print('PASS: Notify credentials saved in owner-only Linux storage outside the bench.')
        print('PASS: SisuAcademy sender configured; SMS restricted to your test number.')
        print('PASS: sandbox privacy notice installed at /sandbox_privacy and version configured.')
        print('NOT TESTED: Notify authentication, credit balance and SMS delivery. No message sent.')
        print('Keep ~/.sisu-secrets excluded from shared backups. Restart only this sandbox after signup deployment.')
    finally:frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception:
        print('Configuration stopped safely. Check inputs, private permissions and source conflicts. No credentials printed.')
        raise SystemExit(1) from None
