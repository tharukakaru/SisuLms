"""Deploy reviewed signup UI fixes and report safe prerequisite diagnostics."""
import hashlib,json,logging,os,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone

def main():
    os.umask(0o077);logging.disable(logging.CRITICAL)
    bench=Path.home()/'sisu-hnb-sandbox-bench';site='hnb-checkout.localhost'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise ValueError('Sandbox only')
    source=Path(__file__).resolve().parents[1];app=bench/'apps/institute_lms'
    baseline=json.loads((source/'scripts/signup-ui-baseline.json').read_text())
    for name,expected in baseline.items():
        current=(app/name).read_text().strip()
        if current!=(source/name).read_text().strip() and hashlib.sha256(current.encode()).hexdigest()!=expected:
            print('BLOCKED: source conflict in '+name);return
    import frappe
    os.chdir(bench/'sites');frappe.init(site=site,sites_path=str(bench/'sites'));frappe.connect()
    try:
        config=frappe.conf.get('il_self_signup_role_emails') or {}
        for role in ('Individual Teacher','Institute'):
            email=config.get(role)
            print(('PASS: ' if email else 'BLOCKED: ')+role+' test email configured')
            if email:print(('EXISTS: ' if frappe.db.exists('User',email) else 'READY: ')+role+' account '+('already created; use login' if frappe.db.exists('User',email) else 'not created yet'))
        from institute_lms.notify_sandbox import credentials
        print(('PASS: ' if credentials().get('test_phone')==frappe.conf.get('il_self_signup_test_phone') else 'BLOCKED: ')+'signup and Notify test phone match')
        print(('PASS: ' if frappe.db.exists('Social Login Key',{'name':'google','enable_social_login':1}) else 'BLOCKED: ')+'Google OAuth configuration presence')
        backup=Path.home()/'.sisu-secrets/signup-backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');backup.mkdir(parents=True,mode=0o700)
        for name in baseline:
            target=app/name;saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved);target.write_text((source/name).read_text())
        subprocess.run(['bench','build','--app','institute_lms'],cwd=bench,check=True)
        frappe.clear_cache()
        print('PASS: button spacing, signup button styling and visible validation/status feedback built. Hard-refresh /campus.')
        print('No emails, SMS, roles, credentials or payment settings changed.')
    finally:frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Stopped safely ['+type(exc).__name__+']. No private values printed.');raise SystemExit(1) from None
