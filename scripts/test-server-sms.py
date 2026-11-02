"""One authorized Notify test. Does not enable customer SMS or change site configuration."""
import argparse,getpass,json,logging,os,re,stat,warnings
from pathlib import Path
SITE='staging.sisuacademylk.com'
BENCH=Path('/home/sisu/frappe-bench')
stage='startup'

class SetupBlocked(ValueError):
    pass

def number(value):
    value=re.sub(r'[ ()-]','',value.strip())
    if re.fullmatch(r'07[0-9]{8}',value):value='+94'+value[1:]
    elif re.fullmatch(r'947[0-9]{8}',value):value='+'+value
    if not re.fullmatch(r'\+947[0-9]{8}',value):raise SetupBlocked('Invalid Sri Lankan mobile format. Enter 07XXXXXXXX or +947XXXXXXXX; do not omit 94 after +.')
    return value

def reserve(path):
    with os.fdopen(os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as out:
        json.dump({'state':'Review'},out);out.flush();os.fsync(out.fileno())

def main():
    global stage
    p=argparse.ArgumentParser();p.add_argument('--inspect',action='store_true');p.add_argument('--test-approved-sender',action='store_true');args=p.parse_args()
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu on the deployment server')
    os.umask(0o077);logging.disable(logging.CRITICAL);warnings.simplefilter('error',getpass.GetPassWarning)
    folder=Path.home()/'.sisu-secrets/server-sms-tests'
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    for part in (folder,folder.parent):
        info=part.lstat()
        if part.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError('Private storage required')
    marker=folder/'first-notify-test.json'
    if marker.exists():
        if marker.is_symlink():raise ValueError('Invalid marker')
        state=json.loads(marker.read_text()).get('state')
        print('Existing test: '+('Accepted' if state=='Accepted' else 'Review required')+'. No SMS resent.');return
    phone=None
    if not args.inspect:
        stage='validate mobile format'
        phone=number(getpass.getpass('Your authorized test mobile: 07XXXXXXXX or +947XXXXXXXX (hidden): '))
        print('PASS: mobile format validated; number not displayed.')
    import frappe
    os.chdir(BENCH/'sites')
    try:
        stage='load staging Notify configuration'
        frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
        config=frappe.conf.get('il_notify') or {}
        if not isinstance(config,dict):raise SetupBlocked('Notify configuration is not a dictionary.')
        missing=[k for k in ('user_id','api_key','sender_id') if not config.get(k)]
        sender_ok=config.get('sender_id')=='SisuAcademy'
        print(('PASS: ' if not missing else 'BLOCKED: ')+'Notify required fields; missing: '+(', '.join(missing) if missing else 'none'))
        print(('PASS: ' if sender_ok else 'BLOCKED: ')+'configured sender matches SisuAcademy: '+str(sender_ok))
        if args.inspect:
            print('INSPECT ONLY: no provider requests, no SMS, no site configuration changes.');return
        if missing:raise SetupBlocked('Required Notify configuration fields are missing.')
        if not sender_ok and not args.test_approved_sender:raise SetupBlocked('Staging sender differs. Use --test-approved-sender for one SisuAcademy test without changing saved configuration.')
        test_config={k:config[k] for k in ('user_id','api_key','sender_id')}
        if args.test_approved_sender:
            test_config['sender_id']='SisuAcademy'
            print('TEST ONLY: using SisuAcademy sender; saved staging configuration remains unchanged.')
        from institute_lms.notify_adapter import send
        stage='reserve single test'
        reserve(marker)  # Persist before provider I/O; ambiguous sends must be reviewed, never retried.
        stage='request Notify acceptance'
        original_config=frappe.conf.get('il_notify')
        try:
            frappe.conf['il_notify']=test_config
            result=send(phone=phone,message='Server SMS delivery test. SISU has sent this single message to your authorized test number. No account was created.')
        finally:
            frappe.conf['il_notify']=original_config
        if not isinstance(result,dict) or result.get('accepted') is not True:raise ValueError('Provider acceptance unconfirmed')
        with marker.open('w') as out:
            json.dump({'state':'Accepted'},out);out.flush();os.fsync(out.fileno())
        print('PASS: Notify accepted the single SMS. Confirm receipt on your phone; acceptance alone is not delivery.')
        print('Teen Academy and platform SMS configuration unchanged. No customer sending enabled.')
    finally:
        try:frappe.db.rollback()
        except Exception:pass
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        if isinstance(exc,SetupBlocked):print('BLOCKED: '+str(exc))
        print('STOPPED at '+stage+' ['+type(exc).__name__+']. No phone, key or provider response printed. Use --inspect; do not remove the test marker or blindly retry.');raise SystemExit(1) from None
