"""Create isolated public MariaDB on loopback 3309; preserve partial site files."""
import json,os,secrets,socket,subprocess,time
from pathlib import Path
NAME='sisu-public-db';VOLUME='sisu-public-db-data';ROOT=Path('/root/sisu-public-database')
def main():
    if os.name!='posix' or os.geteuid()!=0:raise RuntimeError('Run as root on deployment server')
    names=subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines()
    if NAME in names or ROOT.exists():raise RuntimeError('Public database preparation already exists; inspect before resuming')
    if VOLUME in subprocess.check_output(['docker','volume','ls','--format','{{.Name}}'],text=True).splitlines():raise RuntimeError('Public volume already exists; not reused')
    with socket.socket() as sock:sock.bind(('127.0.0.1',3309))
    image=json.loads(subprocess.check_output(['docker','inspect','sisu-staging-db'],text=True))[0]['Image']
    os.umask(0o077);ROOT.mkdir(mode=0o700)
    password=secrets.token_urlsafe(48)
    env=ROOT/'database.env';env.write_text('MARIADB_ROOT_PASSWORD='+password+'\nMARIADB_ROOT_HOST=%\n');env.chmod(0o600)
    subprocess.run(['docker','volume','create',VOLUME],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['docker','run','-d','--name',NAME,'--restart','unless-stopped','--publish','127.0.0.1:3309:3306','--mount','type=volume,source='+VOLUME+',target=/var/lib/mysql','--env-file',str(env),image],check=True,stdout=subprocess.DEVNULL)
    probe='''import json,sys
import MySQLdb
try:
 c=MySQLdb.connect(host="127.0.0.1",port=3309,user="root",passwd=json.load(sys.stdin)["password"],connect_timeout=3)
 c.close();sys.exit(0)
except Exception:sys.exit(1)
'''
    for _ in range(45):
        r=subprocess.run(['/home/sisu/frappe-bench/env/bin/python','-c',probe],input=json.dumps({'password':password}),text=True,capture_output=True)
        if r.returncode==0:break
        time.sleep(2)
    else:raise RuntimeError('New database did not become ready; preserve container and inspect')
    print('READY: isolated public MariaDB on 127.0.0.1:3309; persistent dedicated volume.')
    print('Existing databases and passwords unchanged. Credentials saved privately, not displayed.')
    site=Path('/home/sisu/frappe-bench/sites/sisuacademylk.com')
    expected=Path('/home/sisu/frappe-bench/sites').resolve()
    if site.exists():
        if site.is_symlink() or site.resolve().parent!=expected:raise RuntimeError('Unexpected partial site path')
        config=site/'site_config.json'
        if not config.is_file():raise RuntimeError('Partial site configuration missing; inspect before moving')
        if (site/'private/backups').exists() and any((site/'private/backups').iterdir()):raise RuntimeError('Site has backups; review before moving')
        marker=Path('/root/sisu-public-provision/creation.log')
        if not marker.is_file() or 'Access denied' not in marker.read_text(errors='replace'):raise RuntimeError('Expected failed creation log missing')
        destination=ROOT/'preserved-partial-site'
        # Reversible archive; no database or volume is deleted.
        site.rename(destination)
        print('PRESERVED: failed public-site directory under private recovery directory.')
    print('Next run the revised public-site creation script. No DNS, routing or signup enabled.')
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('STOPPED: '+(str(e) if isinstance(e,RuntimeError) else type(e).__name__)+'. No credentials printed.')
        raise SystemExit(1)
