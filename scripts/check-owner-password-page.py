"""Check public password page and source integrity, without resetting an account."""
import urllib.request,tarfile,json,hashlib
from pathlib import Path
APP=Path('/home/sisu/frappe-bench/apps/institute_lms')
def main():
 with tarfile.open('/tmp/sisu-owner-password-page.tgz') as t:manifest=json.load(t.extractfile('manifest.json'))
 for name,item in manifest.items():assert hashlib.sha256((APP/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==item['after'],name
 for path,marker in [('/sisu_password','id="password-form"'),('/assets/institute_lms/owner-password.js','event.preventDefault()')]:
  with urllib.request.urlopen('https://platform.sisuacademylk.com'+path,timeout=20) as response:
   assert response.status==200
   assert marker in response.read().decode('utf-8-sig')
 print('PASS: deployed sources, public password page and submit handler available over HTTPS. No password, token, account or message changed. Actual invitation/password acceptance remains a browser test.')
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('CHECK FAILED: '+type(exc).__name__)
  raise SystemExit(1) from None
