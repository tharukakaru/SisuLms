"""Persistent, repeatable demo content for the named local sandbox only."""
import os
from pathlib import Path
from datetime import timedelta
EMAIL='sisu.student.test@gmail.com'
TEACHER='sisu-demo-teacher@example.invalid'
def main():
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():raise RuntimeError('Local sandbox only')
    import frappe
    from frappe.utils import now_datetime
    from unittest.mock import patch
    os.chdir(bench/'sites');frappe.init(site='hnb-checkout.localhost',sites_path=str(bench/'sites'));frappe.connect();frappe.set_user('Administrator')
    def no_delivery(*a,**kw):raise RuntimeError('Unexpected external delivery; rolled back')
    try:
        if frappe.conf.get('il_control_plane') or frappe.conf.get('il_shared_campus_enabled'):raise RuntimeError('Unexpected sandbox mode')
        institutes=frappe.get_all('IL Institute',fields=['name'],limit_page_length=2)
        if len(institutes)!=1:raise RuntimeError('Expected one local sandbox institute')
        inst=institutes[0].name
        student=frappe.db.get_value('IL Member',{'institute':inst,'user':EMAIL,'role':'Student','active':1},'name')
        if not student:raise RuntimeError('Local test student membership missing')
        with patch.object(frappe,'sendmail',no_delivery):
            if not frappe.db.exists('User',TEACHER):
                frappe.get_doc({'doctype':'User','email':TEACHER,'first_name':'Demo','last_name':'Teacher','enabled':0,'user_type':'Website User','send_welcome_email':0}).insert(ignore_permissions=True)
            teacher=frappe.db.get_value('IL Member',{'institute':inst,'user':TEACHER,'role':'Teacher'},'name')
            if not teacher:
                teacher=frappe.get_doc({'doctype':'IL Member','institute':inst,'user':TEACHER,'role':'Teacher','full_name':'[DEMO] Mathematics Teacher','language':'en','active':1}).insert(ignore_permissions=True).name
            for user,kind,title,username in [(TEACHER,'Teacher','[DEMO] Mathematics Teacher','sisu_demo_teacher'),('Administrator','Institute','[DEMO] SISU Test Institute','sisu_demo_institute')]:
                existing=frappe.db.get_value('IL Public Profile',{'user':user},'name')
                if not existing:
                    p=frappe.get_doc({'doctype':'IL Public Profile','user':user,'kind':kind,'username':username,'display_name':title,'country':'Sri Lanka','status':'Verified','workspace':inst if kind=='Institute' else None,'bio':'Local demo data only. Not a real provider endorsement.'})
                    p.flags.community_service=True;p.insert(ignore_permissions=True)
            # Explicit local demo entitlement, never a payment or production grant.
            from institute_lms.commercial import account_for,save
            sub=frappe.db.get_value('IL Account Subscription',{'account_key':'Institute:'+inst},'name')
            if not sub:
                if not frappe.db.exists('IL Member',{'institute':inst,'user':'Administrator','role':'Admin'}):
                    frappe.get_doc({'doctype':'IL Member','institute':inst,'user':'Administrator','role':'Admin','full_name':'[DEMO] Sandbox administrator','language':'en','active':1}).insert(ignore_permissions=True)
                sub=frappe.db.get_value('IL Account Subscription',{'account_key':'Institute:'+inst},'name')
            if not sub:raise RuntimeError('Sandbox institute subscription missing')
            until=now_datetime()+timedelta(days=30)
            frappe.db.set_value('IL Account Subscription',sub,{'enabled':1,'trial_until':until})
            provider=account_for(frappe._dict(institute=inst,owner_type='Institute'),False)
            if provider:frappe.db.set_value('IL Provider Account',provider.name,{'enabled':1,'plan':'Gold'})
            else:
                from institute_lms.commercial_rules import beneficiary
                save(frappe.get_doc({'doctype':'IL Provider Account','provider_key':beneficiary({'institute':inst,'owner_type':'Institute'}),'institute':inst,'owner_type':'Institute','plan':'Gold','enabled':1,'billing_email':'demo@example.invalid','cycle_start':now_datetime(),'cycle_end':until}))
            from institute_lms.api import access
            member=frappe.get_doc('IL Member',student)
            for mode,fee in [('Free',0),('Paid',1000)]:
                title='[DEMO] '+('Free mathematics practice' if mode=='Free' else 'Locked paid mathematics class')
                name=frappe.db.get_value('IL Classroom',{'institute':inst,'title':title},'name')
                room=frappe.get_doc('IL Classroom',name) if name else frappe.get_doc({'doctype':'IL Classroom','institute':inst,'title':title,'subject':'Mathematics','teacher':teacher,'font':'sans','active':1,'owner_type':'Institute','fee_mode':mode,'fee':fee,'published':1,'description':'Persistent local demonstration class.'}).insert(ignore_permissions=True)
                if not frappe.db.exists('IL Enrollment',{'classroom':room.name,'student':student}):
                    frappe.get_doc({'doctype':'IL Enrollment','institute':inst,'classroom':room.name,'student':student,'active':1,'fee':fee,'access_override':'Automatic'}).insert(ignore_permissions=True)
                decision=access(room,member)
                if decision['allowed']!=(mode=='Free'):raise RuntimeError('Demo access assertion failed: '+mode)
            frappe.db.commit()
        print('SAVED: demo institute profile, demo teacher, enrolled free and locked paid classrooms.')
        print('Verified: free class allowed; paid class denied. Refresh My classrooms and Teachers & institutes.')
        print('Teacher is a disabled display fixture, not a login. No lesson media or second institute created yet.')
    finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':main()
