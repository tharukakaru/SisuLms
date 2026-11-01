"""Conflict-checked signup sandbox update; no production or gateway changes."""
import ast,argparse,hashlib,json,logging,os,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
SITE='hnb-checkout.localhost'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--notices',action='store_true');args=parser.parse_args()
    os.umask(0o077);logging.disable(logging.CRITICAL)
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise ValueError('Sandbox only')
    source=Path(__file__).resolve().parents[1];app=bench/'apps/institute_lms'
    import frappe
    os.chdir(bench/'sites');frappe.init(site=SITE,sites_path=str(bench/'sites'));frappe.connect()
    try:
        if args.notices:
            from institute_lms.sandbox_notices import welcome,expiry,deliver,allowed
            for row in frappe.get_all('IL Member',filters={'active':1},fields=['user','role']):
                if allowed(row.user):welcome(row.user,'Institute' if row.role=='Admin' else row.role)
            expiry();frappe.db.commit();deliver()
            print('Only configured sandbox test contacts processed. Review uncertain channels before retrying.');return
        baseline=json.loads((source/'scripts/signup-completion-baseline.json').read_text())
        new=['frontend/src/native/ProviderAccessGate.vue','frontend/src/native/InstituteJoinPicker.vue','institute_lms/sandbox_notices.py','institute_lms/institute_coverage.py']
        schema='institute_lms/institute_lms/doctype/il_sandbox_notice/'
        new += [schema+n for n in ('__init__.py','il_sandbox_notice.py','il_sandbox_notice.json')]
        files=list(baseline)+new
        merged_hooks=None
        for name in files:
            target=app/name
            if not target.exists():
                if name in baseline:raise ValueError('Expected deployed source missing')
                continue
            text=target.read_text().strip()
            if name=='institute_lms/hooks.py':
                # Preserve deployed hooks, including independently installed integrations.
                ast.parse(text)
                addon=(source/name).read_text().split('# Sandbox-only transactional test notices; no production dispatch.',1)[1]
                if 'institute_lms.sandbox_notices.observe' in text:
                    if not text.endswith(addon.strip()):
                        print('BLOCKED: existing notice hooks need review');return
                    merged_hooks=text+'\n'
                else:
                    merged_hooks=text+'\n\n# Sandbox-only transactional test notices; no production dispatch.'+addon
                ast.parse(merged_hooks)
                continue
            if text!=(source/name).read_text().strip() and hashlib.sha256(text.encode()).hexdigest() not in baseline.get(name,[]):
                print('BLOCKED: source conflict in '+name);return
        for role in ('Individual Teacher','Institute'):
            ok=bool((frappe.conf.get('il_self_signup_role_emails') or {}).get(role))
            print(('PASS: ' if ok else 'BLOCKED: ')+role+' test email configured')
            if not ok:return
        from institute_lms.notify_sandbox import credentials
        if credentials().get('test_phone')!=frappe.conf.get('il_self_signup_test_phone'):raise ValueError('Test phone mismatch')
        backup=Path.home()/'.sisu-secrets/signup-backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');backup.mkdir(parents=True,mode=0o700)
        subprocess.run(['bench','--site',SITE,'backup','--backup-path',str(backup)],cwd=bench,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for name in files:
            target=app/name
            if target.exists():
                saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(merged_hooks if name=='institute_lms/hooks.py' else (source/name).read_text())
        for dt in ('il_sandbox_notice','il_profile_relationship'):
            frappe.reload_doc('institute_lms','doctype',dt,force=True)
        frappe.db.commit()
        subprocess.run(['bench','build','--app','institute_lms'],cwd=bench,check=True)
        from frappe.installer import update_site_config
        update_site_config('il_signup_notices_enabled',1,site_config_path=str(bench/'sites'/SITE/'site_config.json'))
        update_site_config('il_institute_teacher_coverage',1,site_config_path=str(bench/'sites'/SITE/'site_config.json'))
        update_site_config('il_payments_paused',1,site_config_path=str(bench/'sites'/SITE/'site_config.json'))
        frappe.clear_cache()
        print('PASS: signup UI, role gate, institute request purpose and restricted notice outbox installed.')
        print('Restart only sandbox bench and workers. Hard-refresh /campus. Use +94 format and your configured role email.')
        print('No messages sent by deployment. Future authorized test events queue background welcome/receipt notices.')
        print('Daily scheduler remains paused. Use --notices for targeted test notices. Google OAuth and payment completion remain separate checks.')
    finally:frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Stopped safely ['+type(exc).__name__+']. No private values printed.');raise SystemExit(1) from None
