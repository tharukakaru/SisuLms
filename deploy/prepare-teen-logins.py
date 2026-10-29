"""Run with the server bench Python as root. Secrets stay in root-only files."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import requests

ROOT = Path('/root/sisu-teen-db')
SECRETS = ROOT / 'pilot-logins.json'
REPORT = ROOT / 'pilot-login-checks.json'
ACCOUNTS = [
    ('teen.sisuacademylk.com', 'hello@teenacademy.lk', 'Admin'),
    ('platform.sisuacademylk.com', 'danusgalagoda@gmail.com', 'Super Admin'),
]
CHILD = r'''
import json, sys, frappe
from frappe.utils.password import update_password
data=json.load(sys.stdin)
try:
    frappe.init(site=data['site'], sites_path='.')
    frappe.connect()
    frappe.set_user('Administrator')
    if not frappe.db.get_value('User', data['email'], 'enabled'):
        raise RuntimeError('Expected enabled account missing')
    if data['role']=='Admin':
        if frappe.conf.get('il_control_plane') or frappe.conf.get('il_tenant_id')!='org-b88f135d14e04c99a493c851841ff22a':
            raise RuntimeError('Unexpected tenant')
        if not frappe.db.exists('IL Member', {'user':data['email'],'role':'Admin','active':1}):
            raise RuntimeError('Institute Admin membership missing')
    elif not frappe.conf.get('il_control_plane') or frappe.conf.get('il_owner_email')!=data['email']:
        raise RuntimeError('Unexpected platform ownership')
    update_password(data['email'], data['password'], logout_all_sessions=True)
    frappe.db.commit()
    print('Password configured for verified account.')
except Exception as error:
    print('Account setup failed: '+type(error).__name__)
    sys.exit(1)
finally:
    frappe.destroy()
'''

def write_private(path, value):
    fd=os.open(str(path), os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(value)

def run():
    if os.geteuid()!=0:
        raise RuntimeError('Run as root')
    ROOT.mkdir(mode=0o700, exist_ok=True)
    if SECRETS.exists():
        records=json.loads(SECRETS.read_text())
        if [(r['site'],r['email'],r['role']) for r in records]!=ACCOUNTS:
            raise RuntimeError('Unexpected saved account bindings')
    else:
        records=[dict(site=s,email=e,role=r,password=secrets.token_urlsafe(32),applied=False)
                 for s,e,r in ACCOUNTS]
        write_private(SECRETS,json.dumps(records,indent=2))
    for record in records:
        if not record.get('applied'):
            result=subprocess.run(
                ['sudo','-u','sisu','/home/sisu/frappe-bench/env/bin/python','-c',CHILD],
                input=json.dumps(record), text=True, capture_output=True,
                cwd='/home/sisu/frappe-bench/sites', timeout=120)
            if result.returncode:
                # Never print captured output that might contain unexpected secrets.
                raise RuntimeError('Account setup failed on '+record['site'])
            record['applied']=True
            write_private(SECRETS,json.dumps(records,indent=2))
        print('Account prepared:',record['site'],record['role'])
    text='PRIVATE SISU PILOT LOGINS — do not include in developer/public ZIPs\n\n'
    for record in records:
        text+=('Site: https://'+record['site']+'\nRole: '+record['role']+
               '\nEmail: '+record['email']+'\nPassword: '+record['password']+'\n\n')
    write_private(ROOT/'PILOT-LOGINS.txt',text)

    checks=[]
    def check(site,name,passed,status=None):
        checks.append(dict(site=site,check=name,passed=bool(passed),http_status=status))
    for record in records:
        host=record['site'];base='https://'+host
        with requests.Session() as session:
            session.trust_env=False
            try:
                response=session.post(base+'/api/method/login',data={
                    'usr':record['email'],'pwd':record['password']},timeout=30)
                check(host,'password login',response.status_code==200,response.status_code)
                if response.status_code!=200: continue
                current=session.get(base+'/api/method/institute_lms.portal_session.current',timeout=30)
                resolved=current.json().get('message',{})
                check(host,'server-resolved role',resolved.get('role')==record['role'] and resolved.get('user')==record['email'],current.status_code)
                csrf=resolved.get('csrf_token')
                if csrf:session.headers['X-Frappe-CSRF-Token']=csrf
                methods=(['api.classrooms','api.schedule','api.members'] if record['role']=='Admin'
                         else ['owner_access.access_list','platform.organizations'])
                for method in methods:
                    r=session.get(base+'/api/method/institute_lms.'+method,timeout=30)
                    check(host,method,r.status_code==200,r.status_code)
                if record['role']=='Admin':
                    r=session.get(base+'/api/method/institute_lms.owner_access.access_list',timeout=30)
                    check(host,'Institute Admin denied owner access',r.status_code==403,r.status_code)
                    r=session.post(base+'/api/method/institute_lms.account_billing.status',json={},timeout=30)
                    body=r.json().get('message',{})
                    check(host,'trial available; gateway disabled',r.status_code==200 and body.get('gateway_ready') is False and body.get('account',{}).get('available') is True,r.status_code)
                sid=next((c.value for c in session.cookies if c.name=='sid'),None)
                if sid:
                    for other in ['teen.sisuacademylk.com','platform.sisuacademylk.com','staging.sisuacademylk.com']:
                        if other==host:continue
                        with requests.Session() as foreign:
                            foreign.trust_env=False
                            r=foreign.get('https://'+other+'/api/method/institute_lms.portal_session.current',
                                          headers={'Cookie':'sid='+sid},timeout=30)
                            check(host,'session rejected by '+other,r.status_code==200 and r.json().get('message',{}).get('authenticated') is False,r.status_code)
            except Exception as error:
                check(host,'request failed: '+type(error).__name__,False)
            finally:
                try:
                    session.post(base+'/api/method/logout',timeout=30)
                    r=session.get(base+'/api/method/institute_lms.portal_session.current',timeout=30)
                    check(host,'logout',r.status_code==200 and r.json().get('message',{}).get('authenticated') is False,r.status_code)
                except Exception:
                    check(host,'logout',False)
    write_private(REPORT,json.dumps(checks,indent=2))
    for item in checks:
        print(('PASS' if item['passed'] else 'FAIL'),item['site'],item['check'],item['http_status'])
    print('Private credentials:',ROOT/'PILOT-LOGINS.txt')
    print('Check report:',REPORT)
    return 0 if all(c['passed'] for c in checks) else 1

if __name__=='__main__':
    try:
        sys.exit(run())
    except Exception as error:
        print('STOP: setup could not finish ('+type(error).__name__+'). No secrets printed.')
        sys.exit(1)
