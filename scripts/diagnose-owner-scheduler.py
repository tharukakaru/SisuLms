"""Read-only scheduler/mail diagnosis. Never sends mail or changes scheduler settings."""
import os,json,time

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    for site in ('platform.sisuacademylk.com','sisuacademylk.com','teen.sisuacademylk.com'):
        frappe.init(site=site);frappe.connect()
        try:
            value={'site':site,'flags':{k:bool(frappe.conf.get(k)) for k in ('maintenance_mode','pause_scheduler','disable_scheduler','mute_emails')}}
            stamp=frappe.cache.get_value('il_release_worker_heartbeat')
            value['email_queue_suspended']=bool(frappe.db.get_default('suspend_email_queue'))
            value['payments_paused']=bool(frappe.conf.get('il_payments_paused'))
            value['heartbeat_age_seconds']=round(time.time()-float(stamp)) if stamp else None
            meta=frappe.get_meta('System Settings')
            if meta.has_field('enable_scheduler'):value['system_scheduler_enabled']=bool(frappe.db.get_single_value('System Settings','enable_scheduler'))
            if frappe.db.exists('DocType','Scheduled Job Type'):
                meta=frappe.get_meta('Scheduled Job Type')
                fields=[k for k in ('method','frequency','stopped','last_execution') if meta.has_field(k)]
                value['jobs']=frappe.get_all('Scheduled Job Type',fields=fields,order_by='method asc',limit_page_length=500)
            value['email_queue']={s:frappe.db.count('Email Queue',{'status':s}) for s in ('Not Sent','Sending','Sent','Error','Partially Sent')}
            value['outgoing_account_configured']=bool(frappe.db.exists('Email Account',{'enable_outgoing':1}))
            print(json.dumps(value,default=str))
        except Exception as exc:print(json.dumps({'site':site,'diagnostic_error':type(exc).__name__}))
        finally:frappe.db.rollback();frappe.destroy()
    print('READ ONLY: no credentials, email bodies or tokens displayed; no messages sent or scheduler settings changed.')
if __name__=='__main__':main()
