"""Read-only database authentication diagnosis; no credentials or raw errors printed."""
import json,os,subprocess
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench');CONTAINER='sisu-staging-db'
def main():
    if os.name!='posix' or os.geteuid()!=0:raise RuntimeError('Run as root on deployment server')
    d=json.loads(subprocess.check_output(['docker','inspect',CONTAINER],text=True))[0]
    env=dict(x.split('=',1) for x in d.get('Config',{}).get('Env',[]) if '=' in x)
    password=env.get('MARIADB_ROOT_PASSWORD') or env.get('MYSQL_ROOT_PASSWORD')
    if not password or '\n' in password:raise RuntimeError('Expected container root credential missing')
    command=['docker','exec','-i',CONTAINER,'sh','-c',
        'IFS= read -r MYSQL_PWD; export MYSQL_PWD; exec mariadb --user=root --protocol=socket --batch --skip-column-names -e "SELECT 1"']
    result=subprocess.run(command,input=password+'\n',capture_output=True,text=True,timeout=20)
    socket_ok=result.returncode==0 and result.stdout.strip()=='1'
    print(json.dumps({'container_root_socket_login':socket_ok}))
    probe='''import sys,json
import MySQLdb
v=json.load(sys.stdin)
try:
 c=MySQLdb.connect(host="127.0.0.1",port=3306,user=v["user"],passwd=v["password"],connect_timeout=8)
 c.close();print("PASS")
except Exception as e:print("FAIL:"+str(e.args[0]) if e.args and isinstance(e.args[0],int) else "FAIL")
'''
    def tcp(user,secret):
        r=subprocess.run([str(BENCH/'env/bin/python'),'-c',probe],input=json.dumps({'user':user,'password':secret}),capture_output=True,text=True,timeout=20)
        output=r.stdout.strip()
        return output if output in ('PASS','FAIL','FAIL:1045','FAIL:1698','FAIL:1130','FAIL:2003') else 'UNAVAILABLE'
    print(json.dumps({'container_root_tcp_login':tcp('root',password)}))
    cfg=json.loads((BENCH/'sites/staging.sisuacademylk.com/site_config.json').read_text())
    print(json.dumps({'existing_staging_database_login':tcp(cfg.get('db_user') or cfg['db_name'],cfg['db_password'])}))
    if socket_ok:
        query='SELECT Host FROM mysql.user WHERE User=\'root\''
        command[-1]='IFS= read -r MYSQL_PWD; export MYSQL_PWD; exec mariadb --user=root --protocol=socket --batch --skip-column-names -e '+"\""+query+"\""
        r=subprocess.run(command,input=password+'\n',capture_output=True,text=True,timeout=20)
        if r.returncode==0:print(json.dumps({'root_allowed_hosts':r.stdout.splitlines()}))
    print('Read only: no passwords changed, grants added, databases deleted or site creation retried.')
if __name__=='__main__':
    try:main()
    except Exception as e:print('Diagnostic stopped ['+type(e).__name__+']; no credentials printed.');raise SystemExit(1)
