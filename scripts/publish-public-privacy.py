"""Publish the authorized privacy notice and register its version; signup stays off."""
import hashlib
import os
import subprocess
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
SOURCE = Path('/tmp/sisu-public-privacy.html')
TARGET = Path('/var/www/sisu-marketing-releases/20261101T201903806657Z/privacy/index.html')
SHA = '3ff8650c9614f95328f43e3c6355dd39189f0a458eb616ae9442cc6a7af4cb53'
URL = 'https://www.sisuacademylk.com/privacy/'
VERSION = 'public-2026-11-02-v1'


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root')
    data = SOURCE.read_bytes()
    if SOURCE.is_symlink() or hashlib.sha256(data).hexdigest() != SHA:
        raise RuntimeError('Privacy page checksum mismatch')
    if TARGET.is_symlink() or TARGET.parent.is_symlink() or (TARGET.exists() and TARGET.read_bytes() != data):
        raise RuntimeError('Existing policy differs; nothing overwritten')
    prefix = ['sudo','-u','sisu','-H',str(BENCH/'env/bin/python'),'-c']
    common = '''import frappe,os
os.chdir('/home/sisu/frappe-bench/sites')
frappe.init(site='sisuacademylk.com',sites_path='/home/sisu/frappe-bench/sites')
frappe.connect()
frappe.set_user('Administrator')
assert frappe.conf.get('maintenance_mode') and not frappe.conf.get('il_public_signup_enabled')
doc=frappe.get_single('IL Portal Settings')
assert doc.privacy_policy_url in (None,'','https://www.sisuacademylk.com/privacy/')
assert doc.privacy_policy_version in (None,'','public-2026-11-02-v1')
'''
    result = subprocess.run(prefix+[common+'frappe.destroy()'], capture_output=True)
    if result.returncode:
        raise RuntimeError('Public site policy preflight failed; no policy published')
    TARGET.parent.mkdir(mode=0o755, exist_ok=True)
    TARGET.write_bytes(data)
    TARGET.chmod(0o644)
    result = subprocess.run(['curl','--noproxy','*','--resolve','www.sisuacademylk.com:443:127.0.0.1','--max-time','15','-fsS',URL], capture_output=True)
    if result.returncode or result.stdout != data:
        raise RuntimeError('Published policy HTTPS check failed; signup settings unchanged')
    write = common+'''doc.privacy_policy_url='https://www.sisuacademylk.com/privacy/'
doc.privacy_policy_version='public-2026-11-02-v1'
doc.provider_applications_enabled=0
doc.save(ignore_permissions=True)
frappe.db.commit()
frappe.clear_cache()
frappe.destroy()
'''
    if subprocess.run(prefix+[write], capture_output=True).returncode:
        raise RuntimeError('Policy page published but settings update failed; signup remains closed')
    print('PUBLISHED: '+URL)
    print('CONFIGURED: public privacy version '+VERSION+'. HTTPS page contents verified.')
    print('Signup/shared mode remain OFF. No messages, payments or WhatsApp enabled.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__)+'. No credentials printed.')
        raise SystemExit(1)
