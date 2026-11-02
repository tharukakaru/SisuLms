"""Provision the explicitly authorized Google test student in the local sandbox."""
import os
from pathlib import Path
EMAIL='sisu.student.test@gmail.com'
SITE='hnb-checkout.localhost'
def main():
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise RuntimeError('Run in local sandbox bench')
    import frappe
    from frappe.model.naming import make_autoname
    os.chdir(bench/'sites');frappe.init(site=SITE,sites_path=str(bench/'sites'));frappe.connect()
    try:
        if frappe.conf.get('il_control_plane') or frappe.conf.get('il_shared_campus_enabled'):raise RuntimeError('Unexpected sandbox mode')
        if not frappe.db.get_value('User',EMAIL,'enabled'):raise RuntimeError('Sign in with the test Google account first')
        profiles=frappe.get_all('IL Public Profile',filters={'user':EMAIL},pluck='kind')
        members=frappe.get_all('IL Member',filters={'user':EMAIL},fields=['name','role','active','institute'])
        if any(k!='Student' for k in profiles) or any(m.role!='Student' or not m.active for m in members):raise RuntimeError('Existing identity needs review; no roles changed')
        institutes=frappe.get_all('IL Institute',fields=['name','code'],limit_page_length=2)
        if len(institutes)!=1:raise RuntimeError('Expected one sandbox institute')
        inst=institutes[0]
        if any(m.institute==inst.name for m in members):
            print('READY: existing active test student membership; unchanged.');return
        frappe.set_user('Administrator')
        doc=frappe.get_doc({'doctype':'IL Member','institute':inst.name,'user':EMAIL,
            'role':'Student','full_name':'SISU Test Student','language':'en','active':1,
            'whatsapp_opt_in':0,'email_opt_in':0})
        doc.insert(ignore_permissions=True,set_name=make_autoname('ST-'+inst.code+'-.#####'))
        frappe.db.commit()
        print('CREATED: local test student membership. Sign out and sign in with Google again.')
        print('No password, phone verification, provider role or production account changed.')
    finally:
        frappe.db.rollback();frappe.destroy()
if __name__=='__main__':main()
