"""Update live marketing pricing from the same guest-safe published catalogue."""
import os,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from marketing_shared_plans import patch_marketing
ROOT=Path('/var/www/sisu-marketing-releases/20261101T201903806657Z')
def main():
    if os.name!='posix' or os.geteuid()!=0:raise RuntimeError('Run as root')
    target=ROOT/'app.js'
    if target.is_symlink():raise RuntimeError('Unexpected marketing symlink')
    response=subprocess.run(['curl','--noproxy','*','--resolve','www.sisuacademylk.com:443:127.0.0.1','-fsS','--max-time','15','https://www.sisuacademylk.com/api/method/institute_lms.plan_catalog.public_catalog'],capture_output=True)
    if response.returncode:raise RuntimeError('Public catalogue HTTP check failed; website unchanged')
    data=json.loads(response.stdout).get('message',{})
    if set(data.get('plans',{}))!={'Individual','Silver','Gold','Platinum'}:raise RuntimeError('Unexpected public catalogue')
    old=target.read_bytes();updated=patch_marketing(old.decode('utf-8')).encode('utf-8')
    backup=Path('/root/sisu-public-provision-isolated')/('marketing-before-shared-plans-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.js')
    backup.parent.mkdir(mode=0o700,exist_ok=True);backup.write_bytes(old);backup.chmod(0o600)
    temp=ROOT/'app.catalog-tmp.js';temp.write_bytes(updated)
    result=subprocess.run(['/opt/node-v24.15.0-linux-x64/bin/node','--check',str(temp)],capture_output=True)
    if result.returncode:temp.unlink();raise RuntimeError('Website syntax check failed; website unchanged')
    temp.chmod(0o644);os.replace(temp,target)
    try:
        served=subprocess.run(['curl','--noproxy','*','--resolve','www.sisuacademylk.com:443:127.0.0.1','-fsS','--max-time','15','https://www.sisuacademylk.com/marketing/app.js'],capture_output=True)
        if served.returncode or served.stdout!=updated:raise RuntimeError('Marketing asset verification failed')
    except Exception:target.write_bytes(old);raise
    print('PASS: main website cards, comparison and calculator read published prices/features. Hard-refresh once for the new website script. No DNS or Nginx changes.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__))
        raise SystemExit(1) from None
