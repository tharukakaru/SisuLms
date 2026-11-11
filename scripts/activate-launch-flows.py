"""Activate published LKR pricing and normal student password login; preserve gateway holds."""
import os,json,shutil
from pathlib import Path
from datetime import datetime,timezone
SITES=Path('/home/sisu/frappe-bench/sites')
def main():
 if Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
 root=Path.home()/'.sisu-secrets'
 if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:raise RuntimeError('Private backup directory required')
 backup=root/('launch-flows-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));backup.mkdir(mode=0o700)
 changes=[]
 for site in ('sisuacademylk.com','teen.sisuacademylk.com'):
  path=SITES/site/'site_config.json'
  if path.is_symlink():raise RuntimeError('Unexpected configuration symlink')
  old=path.read_bytes();config=json.loads(old)
  if config.get('il_control_plane'):raise RuntimeError('Unexpected owner site')
  if config.get('il_plan_catalog_source_site')!='platform.sisuacademylk.com':raise RuntimeError('Shared catalogue must already be activated')
  (backup/(site+'.json')).write_bytes(old);(backup/(site+'.json')).chmod(0o600)
  config['il_four_plan_lkr_enabled']=1
  config['il_student_password_login_enabled']=1
  changes.append((path,old,json.dumps(config,indent=2).encode()))
 try:
  for path,old,new in changes:
   temp=path.with_name('launch-flows-config.tmp');temp.write_bytes(new);temp.chmod(0o600);os.replace(temp,path)
 except Exception:
  for path,old,new in changes:path.write_bytes(old)
  raise
 print('ACTIVATED: published LKR provider pricing and student password sign-in on public/Teen sites. No passwords, invoices, account dates, gateway holds or scheduled jobs changed.')
if __name__=='__main__':main()
