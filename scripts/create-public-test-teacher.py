"""Create the requested live test teacher through real email and SMS verification."""
import os,logging
from pathlib import Path
from getpass import getpass
BENCH=Path('/home/sisu/frappe-bench')
EMAIL='sisu.student.test+teacher@gmail.com'
stage='preflight'
def main():
 global stage
 if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
 logging.disable(logging.CRITICAL)
 import frappe
 os.chdir(BENCH/'sites');frappe.init(site='sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect()
 try:
  frappe.set_user('Guest')
  frappe.local.request_ip='127.0.0.1'
  from institute_lms import public_signup,portal_policy,signup_rules
  public_signup.ready()
  if not frappe.conf.get('il_payments_paused'):raise RuntimeError('Payment pause required')
  if frappe.db.exists('User',EMAIL):raise RuntimeError('Teacher login already exists; not overwritten. Use browser sign-in or password recovery.')
  policy=portal_policy.public()
  print('Creates only '+EMAIL+' as a pending test teacher. No institute access or paid entitlement granted.')
  print('Privacy policy: '+policy['privacy_policy_url'])
  if input('Accept the policy and send one email code and one SMS code to your phone? Type YES: ').strip().upper()!='YES':
   print('Cancelled; no messages sent.');return
  phone=getpass('Your authorized mobile in +94 format (hidden): ').strip()
  password=getpass('New teacher password, 12–128 characters (hidden): ')
  confirm=getpass('Confirm password (hidden): ')
  signup_rules.password(password,confirm)
  fields={'kind':'Individual Teacher','first_name':'SISU Test','last_name':'Teacher','email':EMAIL,
   'phone':phone,'username':'sisu_test_teacher','country':'Sri Lanka','timezone':'Asia/Colombo',
   'subject':'Demonstration lessons','bio':'SISU test teacher account','qualifications':'','website':'',
   'privacy_accepted':True,'privacy_policy_version':policy['privacy_policy_version']}
  signup_rules.details(fields)
  stage='sending email verification'
  token=public_signup.start(fields)['challenge']
  stage='verifying email'
  public_signup.verify(token,'email',getpass('Email code (hidden): ').strip())
  stage='sending SMS verification'
  public_signup.send_phone(token)
  stage='verifying SMS'
  public_signup.verify(token,'phone',getpass('SMS code (hidden): ').strip())
  stage='saving verified teacher identity'
  public_signup.complete(token,password,confirm)
  print('CREATED: verified email/phone and password login for '+EMAIL+'. Provider profile is Pending; no institute membership or payment granted.')
  print('Now sign in with email/password at https://www.sisuacademylk.com/campus and verify the teacher setup screen.')
  print('Existing students/admins unchanged. Payments and WhatsApp unchanged. Normal account-confirmation jobs may be queued by signup hooks.')
 finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('STOPPED at '+stage+': '+type(exc).__name__+'. No passwords or codes displayed. No automatic resend. Previously sent messages cannot be rolled back.')
  raise SystemExit(1) from None
