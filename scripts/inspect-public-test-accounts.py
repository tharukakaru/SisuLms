"""Inspect the explicitly named live accounts and signup configuration without secrets."""
import os,json,logging
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
ACCOUNTS={
 'platform.sisuacademylk.com':['tharukakarunarathne60@gmail.com','gro4celk@gmail.com'],
 'sisuacademylk.com':['sisu.student.test@gmail.com','sisu.student.test+teacher@gmail.com'],
}
def main():
 if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
 logging.disable(logging.CRITICAL)
 import frappe
 os.chdir(BENCH/'sites')
 for site,emails in ACCOUNTS.items():
  frappe.init(site=site,sites_path=str(BENCH/'sites'))
  try:
   frappe.connect()
   from institute_lms.owner_access import is_owner,primary_email
   for email in emails:
    exists=bool(frappe.db.exists('User',email))
    result={'site':site,'email':email,'exists':exists,'enabled':bool(exists and frappe.db.get_value('User',email,'enabled')),
     'primary_owner':email==primary_email(),'owner_access':is_owner(email)}
    if exists:
     result['password_set']=bool(frappe.db.sql('SELECT 1 FROM `__Auth` WHERE doctype=%s AND name=%s AND fieldname=%s AND encrypted=0 LIMIT 1',('User',email,'password')))
     result['profiles']=frappe.get_all('IL Public Profile',filters={'user':email},fields=['kind','status'],limit_page_length=10)
     result['memberships']=frappe.get_all('IL Member',filters={'user':email},fields=['role','active'],limit_page_length=10)
     phone=frappe.db.get_value('IL Verified Phone',{'user':email},['phone','verified_at'],as_dict=True)
     result['phone_verified']=bool(phone and phone.phone and phone.verified_at)
     result['email_signup_verified']=bool(frappe.db.exists('IL Registration Request',{'email':email,'email_verified':1,'status':'Approved'}))
    print(json.dumps(result,default=str))
   from institute_lms.portal_policy import public
   policy=public()
   print(json.dumps({'site':site,'signup_enabled':policy['self_signup_enabled'],'google_configured':policy['google_available'],
    'privacy_configured':bool(policy['privacy_policy_url'] and policy['privacy_policy_version']),
    'shared_mode':bool(frappe.conf.get('il_shared_campus_enabled')),'payments_paused':bool(frappe.conf.get('il_payments_paused')),
    'sms_adapter_configured':bool(frappe.conf.get('il_sms_adapter')),'outgoing_email_configured':bool(frappe.db.exists('Email Account',{'enable_outgoing':1})),
    'institute_count':frappe.db.count('IL Institute'),'classroom_count':frappe.db.count('IL Classroom')}))
  finally:frappe.db.rollback();frappe.destroy()
 print('READ ONLY: no accounts created, verification bypassed, passwords read/changed, or messages sent. Provider delivery and browser login remain untested.')
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('STOPPED: '+type(exc).__name__+'. No credentials displayed.')
  raise SystemExit(1) from None
