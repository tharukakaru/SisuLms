"""Inspect only the named staging checkout fixture; rollback all database work."""
import os,json,secrets,traceback
from pathlib import Path

def main():
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='staging.sisuacademylk.com');frappe.connect()
    try:
        frappe.set_user('sisu.student.test+hnb@gmail.com')
        frappe.session.data.csrf_token=secrets.token_hex(32)
        from institute_lms.api import identity,bootstrap
        inst,member=identity()
        data=bootstrap()
        print(json.dumps({'site':frappe.local.site,'shared_campus':bool(frappe.conf.get('il_shared_campus_enabled')),'role':member.role,'institute_teacher':data['member'].get('institute_teacher'),'workspace_has_institute_profile':bool(frappe.db.exists('IL Public Profile',{'workspace':inst.name,'kind':'Institute'})),'personal_profile_kind':frappe.db.get_value('IL Public Profile',{'user':frappe.session.user},'kind'),'personal_profile_workspace_matches':frappe.db.get_value('IL Public Profile',{'user':frappe.session.user},'workspace')==inst.name,'owned_classrooms':frappe.db.count('IL Classroom',{'owner_user':frappe.session.user,'institute':inst.name})}))
        print('READ ONLY: rolled back; no settings, credentials, invoices, messages or payments changed.')
    finally:
        frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'error':type(exc).__name__,'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-6:]]}))
        raise SystemExit(1) from None
