"""Enable sandbox subscription checkout for two named public test users only."""
import os,json,hashlib,shutil,copy
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit

def digest(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
def main():
 if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
 bench=Path('/home/sisu/frappe-bench');app=bench/'apps/institute_lms'
 target=bench/'sites/sisuacademylk.com/site_config.json'
 old=target.read_bytes();config=json.loads(old)
 staging=json.loads((bench/'sites/staging.sisuacademylk.com/site_config.json').read_text())
 root=staging.get('il_cybersource') or {}
 if root.get('mode')!='sandbox' or root.get('enabled') is not True:raise RuntimeError('Configured staging sandbox required')
 merchant=(root.get('merchants') or {}).get('platform') or {}
 if not all(merchant.get(k) for k in ('merchant_id','key_id','p12_path','p12_password','methods')):raise RuntimeError('Incomplete sandbox credentials')
 from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
 key,cert,_=load_key_and_certificates(Path(merchant['p12_path']).read_bytes(),merchant['p12_password'].encode())
 if key is None or cert is None:raise RuntimeError('Invalid certificate')
 origin=config.get('host_name','').rstrip('/')
 if origin not in ('https://sisuacademylk.com','https://www.sisuacademylk.com'):raise RuntimeError('Unexpected public host_name; no changes')
 code=app/'institute_lms/cybersource.py';payload=Path('/tmp/cybersource.py').read_bytes();manifest=json.loads(Path('/tmp/public-sandbox-source.json').read_text())
 if digest(payload)!=manifest['after'] or digest(code.read_bytes()) not in (manifest['before'],manifest['after']):raise RuntimeError('Source conflict; no changes')
 compile(payload,str(code),'exec')
 users=['sisu.student.test+teacher@gmail.com','sisu.student.test+institute.admin@gmail.com']
 os.chdir(bench/'sites')
 import frappe
 frappe.init(site='sisuacademylk.com');frappe.connect()
 try:
  for user in users:
   if not frappe.db.get_value('User',user,'enabled'):raise RuntimeError('Named test account missing or disabled')
 finally:frappe.destroy()
 private=Path('/home/sisu/.sisu-secrets')
 if private.is_symlink() or not private.is_dir() or private.stat().st_mode&0o077:raise RuntimeError('Private backup directory required')
 backup=private/('public-sandbox-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));backup.mkdir(mode=0o700)
 (backup/'site_config.json').write_bytes(old);(backup/'site_config.json').chmod(0o600)
 shutil.copy2(code,backup/'cybersource.py')
 config['il_cybersource']={'enabled':True,'mode':'sandbox','origin':origin,'merchants':{'platform':copy.deepcopy(merchant)}}
 config['il_cybersource_test_users']=users
 config['il_payments_paused']=True
 tmp=target.with_name('site_config.public-sandbox.tmp')
 try:
  code.write_bytes(payload)
  with os.fdopen(os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:json.dump(config,f,indent=2)
  os.replace(tmp,target)
 except Exception:
  shutil.copy2(backup/'cybersource.py',code);target.write_bytes(old);raise
 print('ENABLED: sandbox subscription checkout for the two named public teacher/admin test accounts only.')
 print('All other public accounts remain held. Student card checkout is blocked. Teen/staging configuration unchanged.')
 print('No payment initiated, no invoice settled, no secret printed. Open '+origin+'/campus after restart.')
 print('Private backup: '+str(backup))
if __name__=='__main__':
 try:main()
 except Exception as e:
  print('STOPPED: '+str(e) if isinstance(e,RuntimeError) else 'STOPPED: configuration/certificate validation failed; inspect privately.')
  raise SystemExit(1)
