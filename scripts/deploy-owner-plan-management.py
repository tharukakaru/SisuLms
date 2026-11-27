"""Guarded owner-plan UI deployment; no migrations or subscription mutations."""
import argparse, fcntl, hashlib, json, os, pwd, shutil, signal, subprocess, tarfile, tempfile, urllib.request
from pathlib import Path
from datetime import datetime, timezone
APP=Path('/home/sisu/frappe-bench/apps/institute_lms')
BENCH=APP.parent.parent
ARCHIVE=Path('/tmp/sisu-owner-plan-management.tgz')
DIGEST='6e624dd7c8710464f3d32767c400013e64e138d3981f1105f41f9dbf00f2aae3'
SITES=('sisuacademylk.com','platform.sisuacademylk.com','staging.sisuacademylk.com')
SERVICES=('frappe-bench-web:frappe-bench-frappe-web','frappe-bench-workers:')
def sha(b):return hashlib.sha256(b).hexdigest()
def normalized(b):return b.replace(b'\r\n',b'\n')
def run(cmd):return subprocess.run(cmd,cwd=BENCH,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout

def get(url):
 with urllib.request.urlopen(url,timeout=30) as response:return response.read()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 if os.geteuid()!=0:raise RuntimeError('Run as root.')
 lock=open('/run/sisu-owner-plan.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if sha(ARCHIVE.read_bytes())!=DIGEST:raise RuntimeError('Package checksum mismatch.')
 with tarfile.open(ARCHIVE) as archive:
  members=archive.getmembers()
  if any(not m.isfile() or m.name.startswith('/') or '..' in Path(m.name).parts for m in members):raise RuntimeError('Unsafe archive member.')
  contents={m.name:archive.extractfile(m).read() for m in members}
 manifest=json.loads(contents.pop('manifest.json'))
 if set(contents)!=set(manifest['files']):raise RuntimeError('Manifest mismatch.')
 for name,info in manifest['files'].items():
  target=APP/name
  if not target.resolve().is_relative_to(APP.resolve()):raise RuntimeError('Unsafe target.')
  proposed=contents[name]
  if sha(proposed)!=info['sha256']:raise RuntimeError('Corrupt payload: '+name)
  if target.exists():
   current=sha(normalized(target.read_bytes()))
   if current not in (info['before'],sha(normalized(proposed))):raise RuntimeError('Live file changed; nothing installed: '+name)
  elif info['before'] is not None:raise RuntimeError('Missing baseline: '+name)
  if name.endswith('.py'):compile(proposed,name,'exec')
 for name,digest in manifest['dependencies'].items():
  data=contents.get(name)
  if data is None:data=(APP/name).read_bytes()
  if sha(normalized(data))!=digest:raise RuntimeError('Asset dependency mismatch: '+name)
 print('PREFLIGHT PASS: owner institute search and plan management.',flush=True)
 if not args.apply:return
 before_catalog=get('https://www.sisuacademylk.com/api/method/institute_lms.plan_catalog.public_catalog')
 backup=Path('/home/sisu/.sisu-secrets')/('owner-plan-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
 backup.mkdir(mode=0o700)
 for name in contents:
  target=APP/name
  if target.exists():
   dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,dest)
 (backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print('Private deployment log: '+str(backup/'deployment.log'),flush=True)
 signal.signal(signal.SIGHUP,signal.SIG_IGN)
 owner=pwd.getpwnam('sisu')
 installed=[]
 def write(name,data):
  target=APP/name;target.parent.mkdir(parents=True,exist_ok=True)
  fd,temp=tempfile.mkstemp(dir=target.parent,prefix='.owner-plan-')
  try:
   with os.fdopen(fd,'wb') as f:f.write(data)
   os.chmod(temp,0o644);os.chown(temp,owner.pw_uid,owner.pw_gid);os.replace(temp,target)
  finally:
   if os.path.exists(temp):os.unlink(temp)
 def restart():
  for service in SERVICES:log.write(run(['supervisorctl','restart',service]))
 def clear():
  for site in SITES:log.write(run(['sudo','-H','-u','sisu','--','/usr/local/bin/bench','--site',site,'clear-cache']))
 with (backup/'deployment.log').open('w',buffering=1) as log:
  try:
   # Backend and assets first, entry pages last. Retain old asset URLs for open tabs.
   for name in sorted(contents,key=lambda n:n.endswith('.html')):
    write(name,contents[name]);installed.append(name)
   clear();restart()
   if json.loads(get('https://www.sisuacademylk.com/api/method/institute_lms.plan_catalog.public_catalog'))!=json.loads(before_catalog):raise RuntimeError('Public catalogue changed unexpectedly.')
   for asset in manifest['entry_assets']:
    if sha(get('https://www.sisuacademylk.com/assets/institute_lms/portal/assets/'+asset))!=manifest['files']['institute_lms/public/portal/assets/'+asset]['sha256']:raise RuntimeError('Published asset mismatch.')
   for site in SITES:
    body=get('https://'+site+'/campus')
    if site!='platform.sisuacademylk.com' and manifest['entry_assets'][0].encode() not in body:raise RuntimeError('Campus entry is stale: '+site)
   status=run(['supervisorctl','status']);log.write(status)
   if any('RUNNING' not in line for line in status.splitlines() if line.startswith('frappe-bench-')):raise RuntimeError('Bench services not running.')
   log.write('DEPLOYED: owner institute search and plan management. No database migrations or subscription changes.\n')
  except BaseException:
   import traceback;log.write(traceback.format_exc())
   for name in reversed(installed):
    old=backup/name
    if old.exists():write(name,old.read_bytes())
    elif not name.startswith('institute_lms/public/portal/assets/'):(APP/name).unlink(missing_ok=True)
   clear();restart();log.write('ROLLED BACK: previous sources and entry restored.\n');raise
 print('DEPLOYED. Backup: '+str(backup),flush=True)
if __name__=='__main__':main()
