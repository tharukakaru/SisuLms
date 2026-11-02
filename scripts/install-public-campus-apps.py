"""Install existing bench apps on the new, closed public site only."""
import datetime
import json
import os
import subprocess
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
SITE = 'sisuacademylk.com'


def main():
    if os.name != 'posix' or os.geteuid() != 0:
        raise RuntimeError('Run as root on deployment server')
    config = json.loads((BENCH/'sites'/SITE/'site_config.json').read_text())
    if config.get('db_host') != '127.0.0.1' or int(config.get('db_port', 0)) != 3309:
        raise RuntimeError('Unexpected public database target')
    if not all(config.get(k) for k in ('maintenance_mode', 'pause_scheduler', 'mute_emails', 'il_payments_paused')):
        raise RuntimeError('Expected closed-site settings missing')
    if any(config.get(k) for k in ('il_public_signup_enabled', 'il_shared_campus_enabled', 'il_public_sms_enabled')):
        raise RuntimeError('Public activation must remain off during installation')
    for app in ('payments', 'lms', 'institute_lms'):
        if not (BENCH/'apps'/app).is_dir():
            raise RuntimeError('Required app source missing: '+app)
    os.umask(0o077)
    folder = Path('/root/sisu-public-provision-isolated')
    if not folder.is_dir() or folder.is_symlink():
        raise RuntimeError('Expected private recovery directory missing')
    logpath = folder/('apps-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.log')
    prefix = ['sudo', '-u', 'sisu', '-H', 'env', 'PATH=/opt/node-v24.15.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin']
    probe = '''import json,os,sys,traceback
stage="import"
try:
 import frappe
 os.chdir("/home/sisu/frappe-bench/sites")
 stage="initialize site"
 frappe.init(site="sisuacademylk.com",sites_path="/home/sisu/frappe-bench/sites")
 stage="database connection"
 frappe.connect()
 stage="installed app query"
 apps=frappe.get_installed_apps()
 print("SISU_PROBE:"+json.dumps({"apps":apps}))
except Exception as exc:
 frames=[{"file":os.path.basename(f.filename),"line":f.lineno,"function":f.name} for f in traceback.extract_tb(exc.__traceback__)[-5:]]
 print("SISU_PROBE:"+json.dumps({"stage":stage,"error_type":type(exc).__name__,"errno":getattr(exc,"errno",None),"frames":frames}))
 sys.exit(1)
finally:
 if "frappe" in globals(): frappe.destroy()
'''
    def installed():
        result = subprocess.run(prefix+[str(BENCH/'env/bin/python'), '-c', probe], cwd=BENCH/'sites', capture_output=True, text=True)
        records = [line[len('SISU_PROBE:'):] for line in result.stdout.splitlines() if line.startswith('SISU_PROBE:')]
        if not records:
            raise RuntimeError('Site probe failed before diagnostics; exit code '+str(result.returncode))
        report = json.loads(records[-1])
        if result.returncode or 'apps' not in report:
            print(json.dumps(report), flush=True)
            raise RuntimeError('Cannot read installed app list; diagnostic above contains no credentials')
        return report['apps']
    present = installed()
    with logpath.open('w') as log:
        for app in ('payments', 'lms', 'institute_lms'):
            if app in present:
                print('PRESENT: '+app, flush=True)
                continue
            print('INSTALLING: '+app+' on public site only; private log captures progress.', flush=True)
            result = subprocess.run(prefix+['/usr/local/bin/bench', '--site', SITE, 'install-app', app], cwd=BENCH, stdout=log, stderr=log)
            if result.returncode:
                raise RuntimeError('App installation failed at '+app+'; preserve private log for diagnosis')
            present = installed()
            if app not in present:
                raise RuntimeError('App missing after installation: '+app)
            print('INSTALLED: '+app, flush=True)
    print('PASS: public site has payments, LMS and Institute LMS installed from existing server source.')
    print('Public/shared signup remains OFF; maintenance ON; payments paused. Updated public release and services still pending.')
    print('No other sites migrated, no DNS changed, no shared process restart. Keep installation logs private.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__)+'. No credentials displayed.')
        raise SystemExit(1)
