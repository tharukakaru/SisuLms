"""Open public signup after confirmed delivery tests; keep commercial payments paused."""
import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BENCH=Path('/home/sisu/frappe-bench')
SITE='sisuacademylk.com'
HOST='www.sisuacademylk.com'


def write_config(path, data):
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.activation-')
    with os.fdopen(fd,'wb') as out:out.write(data)
    os.chmod(tmp,0o600);os.replace(tmp,path)


def get(path):
    result=subprocess.run(['curl','--noproxy','*','--resolve',HOST+':443:127.0.0.1',
        '--max-time','20','-sS','-w','\nSISU_STATUS:%{http_code}','https://'+HOST+path],capture_output=True)
    if result.returncode:raise RuntimeError('HTTPS transport check failed: '+path.split('?')[0])
    body, separator, status = result.stdout.rpartition(b'\nSISU_STATUS:')
    if not separator or status != b'200':
        report={'path':path.split('?')[0], 'http_status':status.decode(errors='replace')[:3]}
        try:
            value=json.loads(body)
            kind=value.get('exc_type')
            if isinstance(kind,str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*',kind):report['exception_type']=kind
            trace=value.get('exc') or ''
            if isinstance(trace,str):
                # Only source filename, line and function; never exception messages or locals.
                frames=re.findall(r'File [\\\"]+([^"\\]+)[\\\"]+, line (\d+), in ([A-Za-z0-9_<>]+)',trace)
                report['frames']=[{'file':Path(file).name,'line':int(line),'function':function} for file,line,function in frames[-6:]]
        except (ValueError,TypeError,AttributeError):pass
        print('HTTP DIAGNOSTIC: '+json.dumps(report),flush=True)
        raise RuntimeError('HTTPS check failed: '+path.split('?')[0])
    return body


def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    logging.disable(logging.CRITICAL);os.umask(0o077);os.chdir(BENCH/'sites')
    import frappe
    path=BENCH/'sites'/SITE/'site_config.json'
    if path.is_symlink() or path.stat().st_uid!=os.getuid():raise RuntimeError('Unexpected site config ownership')
    original=path.read_bytes();settings=json.loads(original)
    if not settings.get('maintenance_mode') or settings.get('il_public_signup_enabled'):raise RuntimeError('Expected closed public site; do not repeat activation')
    if settings.get('il_shared_campus_enabled')!=1 or settings.get('il_public_sms_enabled')!=1 or not settings.get('il_payments_paused'):
        raise RuntimeError('Service preparation incomplete')
    if settings.get('il_whatsapp_token') or settings.get('il_whatsapp_phone_id'):raise RuntimeError('Unexpected WhatsApp credentials')
    root=Path.home()/'.sisu-secrets'
    if root.is_symlink() or root.stat().st_uid!=os.getuid() or root.stat().st_mode&0o077:raise RuntimeError('Private recovery directory required')
    if json.loads((root/'public-sms-delivery-test.json').read_text()).get('state')!='accepted':raise RuntimeError('SMS test acceptance missing')
    changed=False
    google=None
    old_signups=None
    try:
        frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect();frappe.set_user('Administrator')
        marker=json.loads((root/'server-email-tests'/ (SITE+'.json')).read_text())
        if frappe.db.get_value('Email Queue',marker.get('queue'),'status')!='Sent':raise RuntimeError('Email test acceptance missing')
        from institute_lms.notify_public import credentials
        credentials(SITE)
        from institute_lms.public_signup import ready
        frappe.conf.il_public_signup_enabled=1;ready();frappe.conf.il_public_signup_enabled=0
        policy=frappe.get_single('IL Portal Settings')
        if policy.privacy_policy_url!='https://'+HOST+'/privacy/' or not policy.privacy_policy_version:raise RuntimeError('Privacy policy missing')
        get('/privacy/')
        google=frappe.get_doc('Social Login Key','google');old_signups=google.sign_ups
        if 'Allow' not in (google.meta.get_field('sign_ups').options or '').splitlines():raise RuntimeError('Unexpected Google signup schema')
        if not google.enable_social_login or not google.get_password('client_secret'):raise RuntimeError('Google provider not ready')
        backup=root/('public-activation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.mkdir(mode=0o700)
        (backup/'site_config.json').write_bytes(original)
        (backup/'google-signups.json').write_text(json.dumps({'sign_ups':old_signups}))
        # Google creates only an identity; SISU verification and membership gates remain in force.
        google.sign_ups='Allow';google.save(ignore_permissions=True);frappe.db.commit();changed=True
        settings.update(il_public_signup_enabled=1,maintenance_mode=0,il_payments_paused=1,pause_scheduler=1)
        write_config(path,json.dumps(settings,indent=2).encode());frappe.clear_cache()
        body=get('/campus').decode()
        assets=re.findall(r'(?:src|href)="(/assets/institute_lms/portal/assets/[^" ]+\.(?:js|css))"',body)
        if not assets:raise RuntimeError('Campus entry assets missing')
        for asset in assets:get(asset)
        public=json.loads(get('/api/method/institute_lms.portal_policy.public'))['message']
        if not public.get('self_signup_enabled') or not public.get('google_available'):raise RuntimeError('Public signup HTTP checks failed')
        session=json.loads(get('/api/method/institute_lms.portal_session.current'))['message']
        if session.get('authenticated') is not False:raise RuntimeError('Guest session check failed')
        print('OPEN: https://www.sisuacademylk.com/campus')
        print('PASS: campus entry/assets, public signup policy and guest-session HTTP checks.')
        print('Google new identities allowed; email/phone verification and role gates remain required.')
        print('Payments paused; WhatsApp unconfigured; general email queue suspended; scheduler paused.')
        print('NEXT: browser signup and Google callback tests. Role flows and background jobs are not yet fully verified.')
    except Exception:
        if changed:
            write_config(path,original)
            google.sign_ups=old_signups;google.save(ignore_permissions=True);frappe.db.commit();frappe.clear_cache()
            print('RESTORED: original configuration and Google signup setting; public site closed again.')
        raise
    finally:frappe.destroy()


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__)+'. No credentials displayed.')
        raise SystemExit(1)
