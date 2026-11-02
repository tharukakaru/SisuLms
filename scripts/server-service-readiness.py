"""Configuration-presence report only. No messages, provider requests or writes."""
import json,logging,os
from pathlib import Path
logging.disable(logging.CRITICAL)
BENCH=Path('/home/sisu/frappe-bench')

def complete(value,keys):
    return isinstance(value,dict) and all(bool(value.get(k)) for k in keys)

def main():
    import frappe
    os.chdir(BENCH/'sites')
    for site in ('teen.sisuacademylk.com','platform.sisuacademylk.com','staging.sisuacademylk.com'):
        result={'site':site,'delivery_tested':False}
        try:
            frappe.init(site=site,sites_path=str(BENCH/'sites'));frappe.connect()
            c=frappe.conf
            result['email_account_present']=bool(frappe.db.exists('Email Account',{'enable_outgoing':1}))
            result['google_login_enabled']=bool(frappe.db.exists('Social Login Key',{'name':'google','enable_social_login':1}))
            result['notify_fields_present']=complete(c.get('il_notify'),('user_id','api_key','sender_id'))
            result['sms_adapter_present']=bool(c.get('il_sms_adapter'))
            result['livekit_fields_present']=all(bool(c.get(k)) for k in ('il_livekit_url','il_livekit_api_key','il_livekit_api_secret'))
            result['private_storage_fields_present']=complete(c.get('il_private_media_s3'),('bucket','region','access_key','secret'))
            result['push_adapter_present']=bool(c.get('il_push_adapter'))
            result['firebase_sandbox_config_present']=bool(c.get('il_firebase_sandbox'))
            result['payments_pause_flag']=bool(c.get('il_payments_paused'))
            result['whatsapp_token_present']=bool(c.get('il_whatsapp_token'))
            result['scheduler_pause_flag']=bool(c.get('pause_scheduler'))
            result['email_mute_flag']=bool(c.get('mute_emails'))
            result['database']='connected'
        except Exception as exc:result['error_type']=type(exc).__name__
        finally:
            try:frappe.db.rollback()
            except Exception:pass
            frappe.destroy()
        print(json.dumps(result))

if __name__=='__main__':main()
