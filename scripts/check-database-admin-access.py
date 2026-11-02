"""Check standard local MariaDB administrator access without altering databases."""
import json,os,subprocess
from pathlib import Path
CONTAINER='sisu-staging-db'
def main():
    if os.name!='posix' or os.geteuid()!=0:raise RuntimeError('Run as root on server')
    # Local socket authentication/default client configuration, no password guess.
    command=['docker','exec',CONTAINER,'mariadb','--user=root','--protocol=socket','--batch','--skip-column-names','-e','SELECT 1']
    result=subprocess.run(command,capture_output=True,text=True,timeout=20)
    print(json.dumps({'container_default_socket_admin':result.returncode==0 and result.stdout.strip()=='1'}))
    for name in ('/root/.my.cnf','/home/sisu/.my.cnf'):
        p=Path(name)
        print(json.dumps({'client_config':name,'present':p.is_file(),'symlink':p.is_symlink()}))
    # Identify mounted secret mechanisms, without dumping mounts or file contents.
    data=json.loads(subprocess.check_output(['docker','inspect',CONTAINER],text=True))[0]
    names={item.split('=',1)[0] for item in data.get('Config',{}).get('Env',[]) if '=' in item}
    print(json.dumps({'root_password_file_setting':bool(names & {'MARIADB_ROOT_PASSWORD_FILE','MYSQL_ROOT_PASSWORD_FILE'})}))
    print('No configuration or database writes; no secrets printed.')
if __name__=='__main__':
    try:main()
    except Exception as e:print('Stopped ['+type(e).__name__+']. No credentials printed.');raise SystemExit(1)
