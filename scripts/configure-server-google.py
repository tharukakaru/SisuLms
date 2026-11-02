"""Configure Google sign-in for existing accounts; never enables Google auto-signup."""
import logging,os,re,stat,subprocess
from datetime import datetime,timezone
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
SITES=('teen.sisuacademylk.com','platform.sisuacademylk.com')
PATH='/api/method/frappe.integrations.oauth2_logins.login_via_google'
stage='startup'

def connect(frappe,site):
    frappe.init(site=site,sites_path=str(BENCH/'sites'));frappe.connect();frappe.set_user('Administrator')

def main():
    global stage
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    os.umask(0o077);logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH/'sites')
    try:
        stage='read existing staging OAuth client'
        connect(frappe,'staging.sisuacademylk.com')
        if frappe.conf.get('google_login'):raise ValueError('Staging override requires review')
        source=frappe.get_doc('Social Login Key','google')
        if source.social_login_provider!='Google' or not source.enable_social_login:raise ValueError('Staging Google provider unavailable')
        client=source.client_id;secret=source.get_password('client_secret')
        if not client or not re.fullmatch(r'[A-Za-z0-9_.-]+\.apps\.googleusercontent\.com',client) or not secret:raise ValueError('Google credential fields incomplete')
    finally:frappe.destroy()
    for site in SITES:
        try:
            stage=site+' preflight';connect(frappe,site)
            if not frappe.conf.get('encryption_key') or frappe.conf.get('google_login'):raise ValueError('Encryption or override needs review')
            meta=frappe.get_meta('Social Login Key')
            if not meta.has_field('sign_ups') or meta.get_field('client_secret').fieldtype!='Password':raise ValueError('Unsupported OAuth schema')
            if frappe.db.exists('Social Login Key','google'):raise ValueError('Target already has a Google provider; not overwritten')
            print('PASS: '+site+' OAuth preflight.')
        finally:frappe.destroy()
    stage='private backups'
    root=Path.home()/'.sisu-secrets';folder=root/'google-rollout'
    for p in (root,folder):
        p.mkdir(exist_ok=True,mode=0o700);info=p.lstat()
        if p.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError('Private backups required')
    backup=folder/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');backup.mkdir(mode=0o700)
    for site in SITES:
        target=backup/site;target.mkdir(mode=0o700)
        subprocess.run(['/usr/local/bin/bench','--site',site,'backup','--backup-path',str(target)],cwd=BENCH,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for site in SITES:
        try:
            stage=site+' configure Google';connect(frappe,site)
            if frappe.db.exists('Social Login Key','google'):raise ValueError('Target changed during preflight')
            doc=frappe.new_doc('Social Login Key');doc.get_social_login_provider('Google',initialize=True)
            doc.social_login_provider='Google';doc.client_id=client;doc.client_secret=secret
            doc.redirect_url='https://'+site+PATH;doc.sign_ups='Deny';doc.enable_social_login=1
            if doc.meta.has_field('trust_email_without_verified_claim'):doc.trust_email_without_verified_claim=0
            doc.save(ignore_permissions=True)
            if doc.name!='google' or doc.get_password('client_secret')!=secret:raise ValueError('Encrypted credential persistence failed')
            from frappe.utils.oauth import get_redirect_uri
            if get_redirect_uri('google')!=doc.redirect_url:raise ValueError('Callback mismatch')
            frappe.db.commit();frappe.clear_cache()
            print('CONFIGURED: '+site+' — existing-account Google sign-in; automatic new-user creation denied.')
            print('Callback: '+doc.redirect_url)
        finally:
            try:frappe.db.rollback()
            except Exception:pass
            frappe.destroy()
    print('No messages or Google authentication requests sent. Register BOTH callbacks on the same Google Cloud client, then test browser login.')
    print('Client secret encrypted separately for each site. Existing staging configuration unchanged.')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED at '+stage+' ['+type(exc).__name__+']. No credentials printed; do not assume both targets were configured.');raise SystemExit(1) from None
