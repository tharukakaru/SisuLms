"""Stage validated Notify credentials in owner-only storage. Never enables sending."""
import json,logging,os,stat
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
TARGETS=('sisuacademylk.com',)

def private_directory(path):
    path.mkdir(exist_ok=True,mode=0o700)
    info=path.lstat()
    if path.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:
        raise ValueError('Owner-only directory required')

def save_new(path,data):
    if path.exists():
        info=path.lstat()
        if path.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError('Existing credential permissions differ')
        if json.loads(path.read_text())!=data:raise ValueError('Existing staged credentials differ; not overwritten')
        return False
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as output:
        json.dump(data,output);output.flush();os.fsync(output.fileno())
    return True

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    os.umask(0o077);logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH/'sites')
    try:
        frappe.init(site='staging.sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect()
        source=frappe.conf.get('il_notify') or {}
        if not isinstance(source,dict) or not all(source.get(k) for k in ('user_id','api_key')):raise ValueError('Source credentials missing')
        credentials={k:source[k] for k in ('user_id','api_key')}
        credentials['sender_id']='SisuAcademy'
    finally:frappe.destroy()
    # Both targets must still have no SMS dispatch adapter or OTP send hook.
    for site in TARGETS:
        try:
            frappe.init(site=site,sites_path=str(BENCH/'sites'));frappe.connect()
            if not frappe.conf.get('maintenance_mode') or not frappe.conf.get('il_payments_paused'):raise ValueError('Expected closed public site')
            if frappe.conf.get('il_sms_adapter') or frappe.get_hooks('il_send_verification_sms'):raise ValueError('Target already has SMS delivery configured')
        finally:frappe.destroy()
    root=Path.home()/'.sisu-secrets';private_directory(root)
    folder=root/'notify-live';private_directory(folder)
    for site in TARGETS:
        target=folder/site;private_directory(target)
        created=save_new(target/'credentials.json',credentials)
        print(('STAGED: ' if created else 'ALREADY STAGED: ')+site+' — owner-only credentials; sender SisuAcademy.')
    try:
        frappe.init(site='sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect()
        from institute_lms.notify_public import credentials as read_private_credentials
        read_private_credentials('sisuacademylk.com')
        policy=frappe.get_single('IL Portal Settings')
        print(json.dumps({'private_sms_credentials_valid':True,'privacy_policy_url':policy.privacy_policy_url or '',
            'privacy_policy_version':policy.privacy_policy_version or '', 'email_muted':bool(frappe.conf.get('mute_emails')),
            'public_signup_enabled':bool(frappe.conf.get('il_public_signup_enabled'))}))
    finally:frappe.destroy()
    print('No site configuration, adapter or SMS delivery enabled. No provider requests or messages sent.')
    print('Credential files are outside the bench and repository. Keep ~/.sisu-secrets excluded from shared backups.')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('PREPARATION STOPPED ['+type(exc).__name__+']. No credentials printed. Existing files were not intentionally overwritten.');raise SystemExit(1) from None
