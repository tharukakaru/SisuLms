"""Read-only launch inventory. No messages, credentials, migrations or restarts."""
import json,os,socket,hashlib,logging
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
def main():
    if os.name!='posix' or not (BENCH/'sites').is_dir():raise RuntimeError('Expected deployment server')
    logging.disable(logging.CRITICAL)
    for host in ('sisuacademylk.com','www.sisuacademylk.com'):
        try:print(json.dumps({'domain':host,'ipv4':sorted({x[4][0] for x in socket.getaddrinfo(host,443,socket.AF_INET)})}))
        except OSError:print(json.dumps({'domain':host,'dns':'unavailable'}))
    print(json.dumps({'marketing_releases_present':Path('/var/www/sisu-marketing-releases').is_dir()}))
    import frappe
    os.chdir(BENCH/'sites')
    sites=sorted(p.name for p in (BENCH/'sites').iterdir() if p.is_dir() and (p/'site_config.json').is_file() and not p.name.endswith('failed-empty-backup'))
    for site in sites:
        out={'site':site}
        try:
            frappe.init(site=site,sites_path=str(BENCH/'sites'));frappe.connect()
            frappe.db.rollback();frappe.db.sql('SET SESSION TRANSACTION READ ONLY')
            c=frappe.conf
            for key in ('il_control_plane','il_shared_campus_enabled','il_self_signup_enabled','il_public_signup_enabled','il_payments_paused','mute_emails','pause_scheduler','il_institute_teacher_coverage'):
                out[key]=bool(c.get(key))
            out['google_enabled']=bool(frappe.db.exists('Social Login Key',{'name':'google','enable_social_login':1}))
            out['outgoing_email_accounts']=frappe.db.count('Email Account',{'enable_outgoing':1})
            out['sms_adapter_configured']=bool(c.get('il_sms_adapter'))
            out['sms_test_restricted']=bool((c.get('il_notify_live') or {}).get('test_mode'))
            out['otp_encryption_key_present']=bool(c.get('encryption_key'))
            out['whatsapp_credentials_present']=bool(c.get('il_whatsapp_token') and c.get('il_whatsapp_phone_id'))
            out['livekit_configured']=all(bool(c.get(k)) for k in ('il_livekit_url','il_livekit_api_key','il_livekit_api_secret'))
            out['institute_count']=frappe.db.count('IL Institute')
            out['pending_email_count']=frappe.db.count('Email Queue',{'status':['in',['Not Sent','Partially Sent']]})
        except Exception as e:out['error_type']=type(e).__name__
        finally:
            if getattr(frappe.local,'db',None):frappe.db.rollback()
            frappe.destroy()
        print(json.dumps(out))
    app=BENCH/'apps/institute_lms/institute_lms'
    for name in ('self_signup.py','campus_context.py','campus_join.py','campus_teachers.py','notify_live.py'):
        path=app/name
        print(json.dumps({'source':name,'present':path.is_file(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None}))
    print('READ ONLY: no configuration changes, messages, account changes or deployment performed.')
if __name__=='__main__':main()
