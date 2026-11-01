"""Install existing Google OAuth credentials in sandbox Frappe encrypted storage."""
import getpass,logging,os,re,subprocess,warnings
from pathlib import Path
from datetime import datetime,timezone
SITE='hnb-checkout.localhost'
CALLBACK='http://localhost:8001/api/method/frappe.integrations.oauth2_logins.login_via_google'

def main():
    os.umask(0o077);logging.disable(logging.CRITICAL);warnings.simplefilter('error',getpass.GetPassWarning)
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise ValueError('Sandbox only')
    import frappe
    os.chdir(bench/'sites');frappe.init(site=SITE,sites_path=str(bench/'sites'));frappe.connect()
    try:
        if not frappe.conf.get('encryption_key'):raise ValueError('Encryption key missing')
        if frappe.conf.get('google_login'):raise ValueError('Existing config override needs review')
        meta=frappe.get_meta('Social Login Key')
        if not meta.has_field('sign_ups') or meta.get_field('client_secret').fieldtype!='Password':raise ValueError('Unsupported schema')
        print('Google Cloud OAuth Web client: add this Authorized redirect URI:')
        print(CALLBACK)
        print('Keep existing production redirect URIs. Use localhost:8001 for this test.')
        client=getpass.getpass('Existing Google OAuth Web Client ID (hidden): ').strip()
        secret=getpass.getpass('Existing Google OAuth Client Secret (hidden): ').strip()
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.apps\.googleusercontent\.com',client) or not secret or len(secret)>1024 or any(c.isspace() for c in secret):raise ValueError('Invalid credentials')
        backup=Path.home()/'.sisu-secrets/google-sandbox'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup.mkdir(parents=True,mode=0o700)
        subprocess.run(['bench','--site',SITE,'backup','--backup-path',str(backup)],cwd=bench,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        doc=frappe.get_doc('Social Login Key','google') if frappe.db.exists('Social Login Key','google') else frappe.new_doc('Social Login Key')
        if not doc.is_new() and doc.social_login_provider!='Google':raise ValueError('Existing provider conflict')
        doc.get_social_login_provider('Google',initialize=True)
        doc.social_login_provider='Google';doc.client_id=client;doc.client_secret=secret
        doc.redirect_url=CALLBACK;doc.sign_ups='Allow';doc.enable_social_login=1
        if meta.has_field('trust_email_without_verified_claim'):doc.trust_email_without_verified_claim=0
        doc.save(ignore_permissions=True)
        if doc.name!='google' or doc.get_password('client_secret')!=secret:raise ValueError('Credential persistence failed')
        from frappe.utils.oauth import get_redirect_uri
        if get_redirect_uri('google')!=CALLBACK:raise ValueError('Unexpected callback URL')
        frappe.db.commit();frappe.clear_cache()
        print('PASS: Google OAuth configured; secret stored in Frappe encrypted Password field.')
        print('PASS: callback URL matches '+CALLBACK)
        print('NOT TESTED: Google consent, credential validity and callback login. No Google request or email sent.')
        print('Hard-refresh http://localhost:8001/campus and try Google. New signup remains subject to SISU test-contact restrictions.')
    finally:frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Setup stopped ['+type(exc).__name__+']. No credentials or exception details printed.');raise SystemExit(1) from None
