"""Install only the verified login password-recovery transport fix."""
from pathlib import Path
import hashlib, shutil, os, datetime
TARGET=Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms/public/login-presentation.js')
PAYLOAD=Path('/tmp/login-password-recovery.js')
OLD='f899a2f4bd6a4c519e78439b33dd90e73ecc5b4d93b02cc1f724297c16ce44db'
NEW='54db7d39e3031a85b3fa6d30296777b22d7715da2834a4e03a569f7e48c222ef'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if sha(PAYLOAD)!=NEW: raise SystemExit('STOPPED: payload checksum mismatch')
if sha(TARGET)==NEW: print('Already installed'); raise SystemExit(0)
if sha(TARGET)!=OLD: raise SystemExit('STOPPED: live login script changed; inspect before applying')
backup=Path('/home/sisu/.sisu-secrets')/('password-recovery-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
backup.mkdir(mode=0o700,parents=True)
shutil.copy2(TARGET,backup/'login-presentation.js')
stat=TARGET.stat()
temp=TARGET.with_name(TARGET.name+'.recovery-tmp')
shutil.copyfile(PAYLOAD,temp)
os.chown(temp,stat.st_uid,stat.st_gid); os.chmod(temp,stat.st_mode & 0o777)
os.replace(temp,TARGET)
assert sha(TARGET)==NEW
print('INSTALLED: password reset API routing fix. No migrations or service restarts. Backup:',backup)
print('Hard-refresh login, request a reset link and check the result. Email delivery still needs verification.')
