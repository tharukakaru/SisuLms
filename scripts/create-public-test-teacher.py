"""Create the requested live test teacher through real email and SMS verification."""
import os,logging,json,traceback
from pathlib import Path
from getpass import getpass
BENCH=Path('/home/sisu/frappe-bench')
EMAIL='sisu.student.test+teacher@gmail.com'
stage='preflight'
PROGRESS=Path('/home/sisu/.sisu-secrets/public-test-teacher-progress.json')

def save_progress(token):
 PROGRESS.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 if PROGRESS.is_symlink():raise RuntimeError('Unexpected progress file')
 with os.fdopen(os.open(PROGRESS,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),'w') as stream:
  os.chmod(PROGRESS,0o600)
  json.dump({'email':EMAIL,'token':token},stream)

def finish(signup,token,password,confirm,state=None):
 global stage
 state=state or {}
 if not state.get('email_verified'):
  stage='verifying email';verify_code(signup,token,'email')
 if not state.get('phone_verified'):
  stage='sending SMS verification';signup.send_phone(token)
  stage='verifying SMS';verify_code(signup,token,'phone')
 stage='saving verified teacher identity'
 signup.complete(token,password,confirm)
 if PROGRESS.exists():PROGRESS.unlink()
 print('CREATED: verified email/phone and password login for '+EMAIL+'. Provider profile is Pending; no institute membership or payment granted.')
 print('Sign in at https://www.sisuacademylk.com/campus using Teacher and email/password.')
def ask_password(rules):
 global stage
 stage='validating password'
 for _ in range(3):
  password=getpass('New teacher password, 12–128 characters (hidden): ')
  confirm=getpass('Confirm password (hidden): ')
  if not 12 <= len(password) <= 128:
   print('Password must contain 12–128 characters. Please try again.');continue
  if password != confirm:
   print('Passwords do not match. Please type the same password twice.');continue
  rules.password(password,confirm)
  return password,confirm
 raise RuntimeError('Password entry attempts exhausted')

def verify_code(signup,token,channel):
 label='Email' if channel=='email' else 'SMS'
 print('Use the newest '+label+' code for this request. Codes are entered privately.')
 for _ in range(5):
  code=getpass(label+' code (hidden): ').strip()
  if len(code)!=6 or not code.isascii() or not code.isdigit():
   print('Enter exactly six digits, without spaces.');continue
  try:
   signup.verify(token,channel,code)
   print(label+' verified.')
   return
  except Exception as exc:
   # Only allowlisted constant messages, never arbitrary backend exception text.
   if str(exc)=='Code did not match.':
    print('Code did not match. Check the newest message for this request and try again.')
    continue
   if str(exc)=='Code expired. Start again.':
    print('Code expired or verification attempts exhausted. Restart with a fresh request.')
   else:
    print('Verification request could not continue. No automatic resend.')
   raise
 raise RuntimeError('Verification entry attempts exhausted')

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
  if frappe.db.exists('User',EMAIL):
   print('Existing test account: '+EMAIL)
   password,confirm=ask_password(signup_rules)
   stage='resetting existing test password'
   if not frappe.db.get_value('User',EMAIL,'enabled'):raise RuntimeError('Test account is disabled; not re-enabled automatically')
   from frappe.utils.password import update_password
   from frappe.sessions import clear_sessions
   frappe.set_user('Administrator')
   update_password(EMAIL,password,logout_all_sessions=True)
   clear_sessions(user=EMAIL,keep_current=False,force=True)
   frappe.db.commit()
   print('RESET: password for '+EMAIL+'. Existing sessions cleared. Roles, verification and memberships unchanged.')
   return
  if PROGRESS.is_file() and not PROGRESS.is_symlink():
   saved=json.loads(PROGRESS.read_text())
   if saved.get('email')!=EMAIL:raise RuntimeError('Unexpected progress identity')
   try:state=public_signup.read(saved['token'])
   except frappe.ValidationError:
    print('Previous verification request expired; starting a fresh request.');state=None
   if state:
    if state.get('details',{}).get('email')!=EMAIL:raise RuntimeError('Verification identity mismatch')
    print('RESUMING: existing verification request; previously verified contacts remain verified until expiry.')
    password,confirm=ask_password(signup_rules)
    finish(public_signup,saved['token'],password,confirm,state)
    return
  policy=portal_policy.public()
  print('Creates only '+EMAIL+' as a pending test teacher. No institute access or paid entitlement granted.')
  print('Privacy policy: '+policy['privacy_policy_url'])
  if input('Accept the policy and send one email code and one SMS code to your phone? Type YES: ').strip().upper()!='YES':
   print('Cancelled; no messages sent.');return
  phone=getpass('Your authorized mobile in +94 format (hidden): ').strip()
  password,confirm=ask_password(signup_rules)
  fields={'kind':'Individual Teacher','first_name':'SISU Test','last_name':'Teacher','email':EMAIL,
   'phone':phone,'username':'sisu_test_teacher','country':'Sri Lanka','timezone':'Asia/Colombo',
   'subject':'Demonstration lessons','bio':'SISU test teacher account','qualifications':'','website':'',
   'privacy_accepted':True,'privacy_policy_version':policy['privacy_policy_version']}
  stage='validating signup details'
  try:
   signup_rules.details(fields)
  except ValueError as exc:
   safe={'Phone number must include the country code.':'Use +94 followed by the mobile number without its initial 0; no spaces or dashes.',
         'Required: phone.':'Enter your mobile number in +94 format.',
         'Choose a valid time zone.':'Server timezone data is unavailable; configuration needs repair.'}
   print(safe.get(str(exc),'Signup field validation failed. No verification message has been requested.'))
   raise
  stage='sending email verification'
  token=public_signup.start(fields)['challenge']
  save_progress(token)
  finish(public_signup,token,password,confirm)
  print('Now sign in with email/password at https://www.sisuacademylk.com/campus and verify the teacher setup screen.')
  print('Existing students/admins unchanged. Payments and WhatsApp unchanged. Normal account-confirmation jobs may be queued by signup hooks.')
 finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
 try:main()
 except Exception as exc:
  frames=traceback.extract_tb(exc.__traceback__)
  print(json.dumps({'failed_stage':stage,'exception':type(exc).__name__,
   'password_strength_rejection':any('password' in f.name.lower() and ('strength' in f.name.lower() or 'test' in f.name.lower()) for f in frames),
   'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in frames[-8:]]}))
  print('STOPPED at '+stage+': '+type(exc).__name__+'. No passwords or codes displayed. No automatic resend. Previously sent messages cannot be rolled back.')
  raise SystemExit(1) from None
