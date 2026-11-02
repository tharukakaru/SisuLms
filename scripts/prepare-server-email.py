"""Prepare existing staging Brevo credentials on two explicit targets. No email sends."""
import argparse,json,logging,os,smtplib,ssl,subprocess,stat
from datetime import datetime,timezone
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
SOURCE='staging.sisuacademylk.com'
TARGETS=('teen.sisuacademylk.com','platform.sisuacademylk.com')
FIELDS=('email_account_name','email_id','enable_incoming','enable_outgoing','default_outgoing','auth_method','login_id_is_different','login_id','smtp_server','smtp_port','use_tls','use_ssl_for_outgoing','no_smtp_authentication','always_use_account_email_id_as_sender','always_use_account_name_as_sender_name','awaiting_password')

def connect(frappe,site):
    frappe.init(site=site,sites_path=str(BENCH/'sites'));frappe.connect();frappe.set_user('Administrator')

def encrypted_secret_count(frappe):
    # Login password hashes have encrypted=0; never replace a lost encryption key.
    return int(frappe.db.sql('SELECT COUNT(*) FROM `__Auth` WHERE encrypted=1')[0][0])

def initialize_site_key(frappe,site):
    if frappe.conf.get('encryption_key'):return False
    if encrypted_secret_count(frappe):raise ValueError('Existing encrypted secrets require original key recovery')
    config=BENCH/'sites'/site/'site_config.json'
    if config.is_symlink() or config.stat().st_uid!=os.getuid():raise ValueError('Unsafe site configuration ownership')
    # Check the file again to avoid replacing a key created after preflight.
    if json.loads(config.read_text()).get('encryption_key'):raise ValueError('Site key changed; reconnect before retrying')
    from frappe.utils.password import get_encryption_key
    get_encryption_key()  # Frappe generates and persists a new site-specific Fernet key.
    stored=json.loads(config.read_text()).get('encryption_key')
    if not stored:raise ValueError('Frappe did not persist the site key')
    frappe.conf['encryption_key']=stored
    os.chmod(config,0o600)
    print('PASS: '+site+' — site encryption key initialized; value not displayed.')
    return True


def target_preflight(frappe,site,initialize_missing=False):
    """Print only fixed labels, field names and counts; never exception contents."""
    key_present=bool(frappe.conf.get('encryption_key'))
    encrypted=encrypted_secret_count(frappe) if not key_present else 0
    can_initialize=initialize_missing and not key_present and encrypted==0
    meta=frappe.get_meta('Email Account')
    missing=[name for name in FIELDS if not meta.has_field(name)]
    accounts=int(frappe.db.count('Email Account'))
    print(('PASS: ' if key_present else ('PENDING: ' if can_initialize else 'BLOCKED: '))+site+' — site encryption key '+('present' if key_present else 'missing'))
    print(('PASS: ' if not missing else 'BLOCKED: ')+site+' — Email Account schema; missing fields: '+(', '.join(missing) if missing else 'none'))
    print(('PASS: ' if accounts==0 else 'BLOCKED: ')+site+' — existing Email Account count: '+str(accounts))
    if not key_present:
        print(('READY TO INITIALIZE: ' if can_initialize else 'BLOCKED: ')+site+' — encrypted secret count: '+str(encrypted))
    return (key_present or can_initialize) and not missing and accounts==0


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--inspect-targets',action='store_true');parser.add_argument('--initialize-missing-keys',action='store_true');args=parser.parse_args()
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu on the deployment server')
    os.umask(0o077);logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH/'sites')
    if args.inspect_targets:
        for site in TARGETS:
            try:
                connect(frappe,site);target_preflight(frappe,site)
            finally:frappe.destroy()
        print('INSPECTION ONLY: no SMTP requests, configuration writes or messages.');return
    try:
        connect(frappe,SOURCE)
        names=frappe.get_all('Email Account',filters={'enable_outgoing':1,'smtp_server':'smtp-relay.brevo.com','email_id':'noreply@sisuacademylk.com'},pluck='name')
        if len(names)!=1:raise ValueError('Expected staging Brevo account is absent or ambiguous')
        source=frappe.get_doc('Email Account',names[0])
        if not source.use_tls or source.use_ssl_for_outgoing or int(source.smtp_port)!=587 or source.no_smtp_authentication:raise ValueError('Unexpected SMTP security configuration')
        values={field:source.get(field) for field in FIELDS}
        values.update(email_account_name='SISU Academy',enable_incoming=0,enable_outgoing=1,default_outgoing=1,awaiting_password=0)
        password=source.get_password('password')
        username=source.login_id if source.login_id_is_different else source.email_id
        compat=bool(frappe.conf.get('smtp_no_ehlo_after_auth'))
    finally:frappe.destroy()
    with smtplib.SMTP('smtp-relay.brevo.com',587,timeout=20) as smtp:
        smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo();smtp.login(username,password)
    print('PASS: staging SMTP STARTTLS authentication. No recipients or messages submitted.')
    targets_ok=True
    for site in TARGETS:
        try:
            connect(frappe,site)
            targets_ok=target_preflight(frappe,site,args.initialize_missing_keys) and targets_ok
        finally:frappe.destroy()
    if not targets_ok:
        print('BLOCKED: resolve the checks above. No target changes or messages.');return
    if not args.apply:
        print('CHECK ONLY: no configuration writes. Use --apply to prepare accounts with email queue suspended.');return
    # Backup both sites before changing either one; never print backup credentials.
    backup=Path.home()/'.sisu-secrets/email-rollout'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True,mode=0o700)
    for site in TARGETS:
        folder=backup/site;folder.mkdir(mode=0o700)
        subprocess.run(['/usr/local/bin/bench','--site',site,'backup','--backup-path',str(folder)],cwd=BENCH,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for site in TARGETS:
        try:
            connect(frappe,site)
            if not frappe.conf.get('encryption_key'):
                if not args.initialize_missing_keys:raise ValueError('Site encryption key missing')
                initialize_site_key(frappe,site)
            frappe.db.set_default('suspend_email_queue',1);frappe.db.commit()
            if frappe.db.count('Email Account'):raise ValueError('Target changed after preflight')
            doc=frappe.new_doc('Email Account');doc.update(values);doc.password=password
            doc.save(ignore_permissions=True)
            if doc.get_password('password')!=password:raise ValueError('Target SMTP encryption verification failed')
            frappe.db.commit()
            if compat:
                from frappe.installer import update_site_config
                update_site_config('smtp_no_ehlo_after_auth',1,site_config_path=str(BENCH/'sites'/site/'site_config.json'))
            frappe.clear_cache()
            print('PREPARED: '+site+'; password encrypted for target; general email queue suspended.')
        finally:frappe.destroy()
    print('No email sent. Reply-To not configured. Recipient delivery testing and queue activation remain pending.')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED ['+type(exc).__name__+']. No credentials printed. Do not assume all targets were updated.');raise SystemExit(1) from None
