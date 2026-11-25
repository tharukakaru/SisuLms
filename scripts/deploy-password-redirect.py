"""Install only the verified login password-recovery transport fix."""
from pathlib import Path
import hashlib, shutil, os, datetime
TARGET=Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms/public/login-presentation.js')
PAYLOAD=Path('/tmp/login-password-redirect.js')
OLD='0b54af9fb535c74d188c6fe13da1e9918dccab0e92efe49437149a6a3a4391da'
NEW='e7eff7f414de795e5229fd201a382b7f7926d3a6cd9712ab2af15e0a38167c55'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if sha(PAYLOAD)!=NEW: raise SystemExit('STOPPED: payload checksum mismatch')
if sha(TARGET)==NEW: print('Already installed'); raise SystemExit(0)
if sha(TARGET)!=OLD: raise SystemExit('STOPPED: live login script changed; inspect before applying')
backup=Path('/home/sisu/.sisu-secrets')/('password-redirect-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
backup.mkdir(mode=0o700,parents=True)
shutil.copy2(TARGET,backup/'login-presentation.js')
stat=TARGET.stat()
temp=TARGET.with_name(TARGET.name+'.recovery-tmp')
shutil.copyfile(PAYLOAD,temp)
os.chown(temp,stat.st_uid,stat.st_gid); os.chmod(temp,stat.st_mode & 0o777)
os.replace(temp,TARGET)
assert sha(TARGET)==NEW
print('INSTALLED: password reset campus redirect fix. No migrations or service restarts. Backup:',backup)
print('Hard-refresh login, use a fresh reset link and enter a new password privately.')
