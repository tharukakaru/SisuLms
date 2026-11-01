"""Sandbox-only signup deployment. No messages, account creation or payment changes."""
import argparse, getpass, hashlib, json, logging, os, shutil, subprocess, warnings
from datetime import datetime, timezone
from pathlib import Path
SITE='hnb-checkout.localhost'
FILES=('institute_lms/self_signup.py','institute_lms/signup_rules.py','institute_lms/registration.py','institute_lms/portal_policy.py','frontend/src/native/VerifiedSignup.vue','frontend/src/native/RegistrationFlow.vue','frontend/src/native/PortalRoot.vue')

def check(frappe):
    checks={
        'Exactly one isolated sandbox institute':frappe.db.count('IL Institute')==1,
        'Brevo outgoing account':bool(frappe.db.exists('Email Account',{'name':'SISU Academy','enable_outgoing':1})),
        'Server encryption key':bool(frappe.conf.get('encryption_key')),
        'SMS adapter configured':bool(frappe.conf.get('il_sms_adapter') or frappe.get_hooks('il_send_verification_sms')),
    }
    settings=frappe.get_single('IL Portal Settings')
    checks['Privacy policy URL and version']=bool(settings.privacy_policy_url and settings.privacy_policy_version)
    for label,ok in checks.items():print(('PASS: ' if ok else 'BLOCKED: ')+label)
    print('Provider presence is not a delivery test. No OTP or email sent.')
    return all(checks.values())

def prepare_workspace(frappe,bench):
    count=frappe.db.count('IL Institute')
    if count>1:
        print('BLOCKED: multiple institutes need review; none changed.');return
    if count==1:
        print('PASS: existing institute preserved; no account or role changed.');return
    if frappe.db.count('IL Member'):
        print('BLOCKED: memberships exist without an institute; review required.');return
    backup=Path.home()/'.sisu-secrets/signup-backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True,mode=0o700)
    subprocess.run(['bench','--site',SITE,'backup','--backup-path',str(backup)],cwd=bench,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    with frappe.cache.lock('il_signup_prepare_workspace',timeout=60):
        if frappe.db.count('IL Institute') or frappe.db.count('IL Member'):
            print('Workspace changed during preparation; nothing created.');return
        frappe.get_doc({'doctype':'IL Institute','code':'SISUTEST','title':'SISU Signup Sandbox — Test Only','language':'en','billing_day':1}).insert(ignore_permissions=True)
        frappe.db.commit()
    print('PASS: isolated sandbox test institute created. No users, admin roles or billing records created.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--deploy',action='store_true');parser.add_argument('--prepare-workspace',action='store_true');args=parser.parse_args()
    os.umask(0o077);warnings.simplefilter('error',getpass.GetPassWarning);logging.disable(logging.CRITICAL)
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if Path.cwd().resolve()!=bench.resolve():raise ValueError('Run from the sandbox bench.')
    source=Path(__file__).resolve().parents[1];app=bench/'apps/institute_lms'
    import frappe
    os.chdir(bench/'sites');frappe.init(site=SITE,sites_path=str(bench/'sites'));frappe.connect()
    try:
        if args.prepare_workspace:prepare_workspace(frappe,bench)
        ready=check(frappe)
        if not args.deploy:
            print('Check complete.' if args.prepare_workspace else 'Read-only check complete; no configuration changed.');return
        if not ready:
            print('Deployment stopped before writes. Resolve the BLOCKED checks first.');return
        baseline=json.loads((source/'scripts/signup-baseline.json').read_text())
        conflicts=[]
        for name in FILES:
            target=app/name
            if target.exists() and target.read_text().strip()!=(source/name).read_text().strip():
                allowed=baseline.get(name,[])
                if isinstance(allowed,str):allowed=[allowed]
                digest=hashlib.sha256(target.read_text().strip().encode()).hexdigest()
                if digest not in allowed:
                    conflicts.append(name)
                    print('BLOCKED: source conflict in '+name+' [SHA256 '+digest+']')
        if conflicts:
            print('No files or configuration changed. Share these filenames and hashes for review.');return
        import importlib.util
        spec=importlib.util.spec_from_file_location('signup_setup_rules',source/'institute_lms/signup_rules.py')
        rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
        details=rules.details
        email=getpass.getpass('One authorized NEW signup test email (hidden): ').strip().lower()
        phone=getpass.getpass('One authorized test mobile, including country code (hidden): ').strip()
        details(dict(kind='Student',first_name='Sandbox',last_name='Test',email=email,phone=phone,username='signup_test',country='LK',timezone='UTC',grade='Test',privacy_accepted=True))
        if frappe.db.exists('User',email):raise ValueError('Use an email without an existing account.')
        backup=Path.home()/'.sisu-secrets/signup-backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup.mkdir(parents=True,mode=0o700)
        # Explicit private backup; never copy secrets to the repository.
        subprocess.run(['bench','--site',SITE,'backup','--backup-path',str(backup)],cwd=bench,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for name in FILES:
            target=app/name
            if target.exists():
                saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text((source/name).read_text())
        subprocess.run(['bench','build','--app','institute_lms'],cwd=bench,check=True)
        from frappe.installer import update_site_config
        for key,value in {'il_self_signup_test_email':email,'il_self_signup_test_phone':phone,'il_self_signup_phone_channel':'SMS','il_self_signup_enabled':1}.items():
            update_site_config(key,value,site_config_path=str(bench/'sites'/SITE/'site_config.json'))
        frappe.clear_cache()
        print('PASS: sandbox signup source built and test contacts configured. Restart only this sandbox bench.')
        print('No messages sent. Institute signup still requires an explicitly assigned empty workspace.')
        print('Next: /campus -> Create account; verify both codes, save, and sign in. Runtime signup is not yet verified.')
    finally:frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Setup stopped safely ['+type(exc).__name__+']. No exception details or credentials printed.')
        raise SystemExit(1) from None
