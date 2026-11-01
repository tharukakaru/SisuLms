"""Sandbox role-test setup and one targeted native password-reset test."""
import argparse,getpass,hashlib,importlib.util,json,logging,os,shutil,subprocess,warnings
from pathlib import Path
from datetime import datetime,timezone
SITE='hnb-checkout.localhost'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reset',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    os.umask(0o077);logging.disable(logging.CRITICAL);warnings.simplefilter('error',getpass.GetPassWarning)
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise ValueError('Sandbox only')
    source=Path(__file__).resolve().parents[1];app=bench/'apps/institute_lms'
    import frappe
    os.chdir(bench/'sites');frappe.init(site=SITE,sites_path=str(bench/'sites'));frappe.connect()
    try:
        roles=frappe.conf.get('il_self_signup_role_emails') or {}
        if args.check:
            from institute_lms.account_billing import account,state
            institutes=frappe.get_all('IL Institute',pluck='name')
            if len(institutes)!=1:raise ValueError('Workspace missing')
            inst=frappe.get_doc('IL Institute',institutes[0])
            for role,email in roles.items():
                member=frappe.db.get_value('IL Member',{'user':email,'institute':inst.name},'name')
                if not member:print('PENDING: '+role+' account creation');continue
                m=frappe.get_doc('IL Member',member);expected='Teacher' if role=='Individual Teacher' else 'Admin'
                print(('PASS: ' if m.role==expected else 'FAIL: ')+role+' membership role')
                billing=account(inst,m);status=state(billing)
                print(('PASS: ' if not status['available'] else 'REVIEW: ')+role+' unpaid workspace lock')
            return
        if args.reset:
            email=getpass.getpass('Existing authorized test account email for ONE reset email (hidden): ').strip().lower()
            allowed=set(roles.values())|{frappe.conf.get('il_self_signup_test_email')}
            if email not in allowed or email in ('Administrator','Guest') or not frappe.db.get_value('User',email,'enabled'):raise ValueError('Not an authorized test account')
            if not frappe.db.get_default('suspend_email_queue'):raise ValueError('General queue must remain suspended')
            marker='il_signup_reset_test:'+hashlib.sha256(email.encode()).hexdigest()
            with frappe.cache.lock(marker,timeout=60):
                if frappe.cache.get_value(marker):
                    print('BLOCKED: reset already requested within one hour; inspect inbox/queue before retrying.');return
                frappe.cache.set_value(marker,1,expires_in_sec=3600)
                before=set(frappe.get_all('Email Queue',pluck='name'))
                from frappe.core.doctype.user.user import reset_password
                reset_password(email)
                frappe.db.commit()
                after=set(frappe.get_all('Email Queue',pluck='name'))-before
                if len(after)!=1:raise ValueError('Expected exactly one reset queue record')
                queue=frappe.get_doc('Email Queue',after.pop())
                if len(queue.recipients)!=1 or queue.recipients[0].recipient.lower()!=email:raise ValueError('Unexpected recipient')
                if queue.status=='Not Sent':queue.send(force_send=True)
                frappe.db.commit();queue.reload()
                print('Reset queue status: '+queue.status)
                print('Check inbox. Open the reset link, choose a new password and verify login. No general queue flush performed.')
            return
        baseline=json.loads((source/'scripts/signup-followup-baseline.json').read_text())
        for name,expected in baseline.items():
            target=app/name
            if not target.exists():raise ValueError('Missing deployed source')
            text=target.read_text().strip()
            if text!=(source/name).read_text().strip() and hashlib.sha256(text.encode()).hexdigest()!=expected:
                print('BLOCKED: source conflict in '+name);return
        if frappe.db.count('IL Institute')!=1 or frappe.db.exists('IL Member',{'role':'Admin'}):
            raise ValueError('Institute test needs a sandbox without an existing institute admin')
        teacher=getpass.getpass('NEW teacher test email you control (hidden): ').strip().lower()
        institute=getpass.getpass('NEW institute test email you control (hidden): ').strip().lower()
        from institute_lms.signup_rules import details
        for email in (teacher,institute):
            details(dict(kind='Student',first_name='Test',last_name='User',email=email,phone=frappe.conf.get('il_self_signup_test_phone'),username='testing',country='LK',timezone='UTC',grade='Test',privacy_accepted=True))
            if frappe.db.exists('User',email):raise ValueError('Use new emails')
        if teacher==institute or frappe.conf.get('il_self_signup_test_email') in (teacher,institute):raise ValueError('Distinct test emails needed')
        backup=Path.home()/'.sisu-secrets/signup-backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');backup.mkdir(parents=True,mode=0o700)
        subprocess.run(['bench','--site',SITE,'backup','--backup-path',str(backup)],cwd=bench,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for name in baseline:
            target=app/name;saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved);target.write_text((source/name).read_text())
        subprocess.run(['bench','build','--app','institute_lms'],cwd=bench,check=True)
        from frappe.installer import update_site_config
        for key,value in {'il_self_signup_role_emails':{'Individual Teacher':teacher,'Institute':institute},'il_self_signup_institute_email':institute}.items():
            update_site_config(key,value,site_config_path=str(bench/'sites'/SITE/'site_config.json'))
        frappe.clear_cache()
        google=frappe.db.exists('Social Login Key',{'name':'google','enable_social_login':1})
        print(('PASS: ' if google else 'BLOCKED: ')+'Google provider configuration presence (OAuth callback not yet tested).')
        print('PASS: Google buttons deployed; teacher/institute test emails assigned. Existing student and test phone preserved.')
        print('Restart only sandbox. Register both roles in separate signed-out sessions. Expect plan/payment screen, not unlocked teaching access.')
        print('Then run this script with --check, and --reset for one native password-reset email. No messages sent during setup.')
    finally:frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Stopped safely ['+type(exc).__name__+']. No credentials, passwords or reset links printed.');raise SystemExit(1) from None
