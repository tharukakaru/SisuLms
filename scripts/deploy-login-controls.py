from pathlib import Path
import hashlib,shutil,datetime
src=Path('/tmp/login-presentation.css')
dst=Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms/public/login-presentation.css')
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
assert digest(src)=='d18e669e5153f5940d0f564b2c906326dcfdf2419b65b0d73205571fda037f9e','Upload mismatch'
assert digest(dst) in ('69481eeaab2666f17cfe75fb60fdb2698c071cec8c67a36fe25f064f9ac0c866','d18e669e5153f5940d0f564b2c906326dcfdf2419b65b0d73205571fda037f9e'),'Source conflict; stopped without changes'
backup=dst.with_name('login-presentation.css.'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+'.bak')
shutil.copy2(dst,backup)
dst.write_bytes(src.read_bytes());dst.chmod(0o644)
print('DEPLOYED: rounded pale login fields and purple pill sign-in button. Authentication unchanged. Hard-refresh the login page.')
