"""Read-only inventory for the existing SISU bench; never prints credentials."""
import json, os, logging
from pathlib import Path
logging.disable(logging.CRITICAL)
BENCH=Path('/home/sisu/frappe-bench')
SITES=('teen.sisuacademylk.com','platform.sisuacademylk.com','staging.sisuacademylk.com')

def main():
    import frappe
    os.chdir(BENCH/'sites')
    for site in SITES:
        result={'site':site}
        try:
            frappe.init(site=site,sites_path=str(BENCH/'sites'))
            frappe.connect()
            # No provider values, user addresses, tokens or database connection details.
            for key in ('il_control_plane','il_owner_provisioned','il_self_signup_enabled','il_payments_paused','pause_scheduler','mute_emails','il_usage_billing_enabled'):
                result[key]=bool(frappe.conf.get(key))
            result['institutes']=frappe.get_all('IL Institute',fields=['name','title','code'])
            result['active_members']={role:frappe.db.count('IL Member',{'role':role,'active':1}) for role in ('Admin','Teacher','Student')}
            result['outgoing_email_accounts']=frappe.db.count('Email Account',{'enable_outgoing':1})
            result['schema']={dt:bool(frappe.db.exists('DocType',dt)) for dt in ('IL Owner Access','IL Account Subscription','IL Public Profile','IL Classroom Quiz','IL Sandbox Notice')}
            if result['schema']['IL Account Subscription']:
                result['subscriptions']=frappe.get_all('IL Account Subscription',fields=['role','plan','enabled','trial_until','paid_until'],limit_page_length=20)
            if result['schema']['IL Public Profile']:
                result['institute_profiles']=frappe.get_all('IL Public Profile',filters={'kind':'Institute'},fields=['display_name','status','workspace'],limit_page_length=20)
            result['database']='connected'
        except Exception as exc:
            result['check_error']=type(exc).__name__
        finally:
            try:frappe.db.rollback()
            except Exception:pass
            frappe.destroy()
        print(json.dumps(result,default=str))

if __name__=='__main__':main()
