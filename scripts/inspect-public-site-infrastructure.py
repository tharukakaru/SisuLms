"""Read-only infrastructure inputs for a new, separate public campus site."""
import json,os,shutil,subprocess
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
def main():
    if os.name!='posix' or os.geteuid()!=0 or not (BENCH/'sites').is_dir():raise RuntimeError('Run as root on the deployment server')
    target=BENCH/'sites/sisuacademylk.com'
    print(json.dumps({'public_site_exists':target.exists(),'certbot_installed':bool(shutil.which('certbot'))}))
    common=json.loads((BENCH/'sites/common_site_config.json').read_text())
    for site in ('staging.sisuacademylk.com','teen.sisuacademylk.com'):
        config={**common,**json.loads((BENCH/'sites'/site/'site_config.json').read_text())}
        # Explicit allowlist only. Never print database names, users or passwords.
        print(json.dumps({'site':site,'db_host':config.get('db_host'),'db_port':config.get('db_port'),'db_type':config.get('db_type'),'redis_cache_configured':bool(config.get('redis_cache')),'redis_queue_configured':bool(config.get('redis_queue'))}))
    containers=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
    for name in containers:
        if name not in ('sisu-staging-db','sisu-teen-db'):continue
        data=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
        env=dict(x.split('=',1) for x in data.get('Config',{}).get('Env',[]) if '=' in x)
        print(json.dumps({'container':name,'image':data.get('Config',{}).get('Image'),'ports':data.get('NetworkSettings',{}).get('Ports'),
            'root_password_env_present':bool(env.get('MARIADB_ROOT_PASSWORD') or env.get('MYSQL_ROOT_PASSWORD'))}))
    result=subprocess.run(['sudo','-u','sisu','-H','/usr/local/bin/bench','new-site','--help'],cwd=BENCH,capture_output=True,text=True)
    options=('--db-host','--db-port','--db-root-username','--db-root-password','--mariadb-root-password','--admin-password','--no-mariadb-socket','--install-app')
    print(json.dumps({'new_site_help_available':result.returncode==0,'supported_options':[x for x in options if x in result.stdout]}))
    root=Path('/var/www/sisu-marketing-releases')
    releases=sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    print(json.dumps({'latest_marketing_release':releases[-1] if releases else None}))
    print('READ ONLY: no site creation, password changes, configuration writes, messages or restarts.')
if __name__=='__main__':main()
