"""Read-only launch flow checks; never start checkout or change user records."""
import os,json,hashlib,tarfile
from pathlib import Path
from types import SimpleNamespace
APP=Path('/home/sisu/frappe-bench/apps/institute_lms')
def digest(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
def main():
 with tarfile.open('/tmp/sisu-launch-followup.tgz') as archive:
  manifest=json.load(archive.extractfile('manifest.json'))
  for name,entry in manifest.items():assert digest((APP/name).read_bytes())==entry['after'],name
 print('PASS: deployed source matches launch-flow package.')
 os.chdir('/home/sisu/frappe-bench/sites')
 import frappe
 for site in ('sisuacademylk.com','teen.sisuacademylk.com'):
  frappe.init(site=site);frappe.connect()
  try:
   from institute_lms import account_billing,plan_catalog,portal_policy
   config=frappe.conf.get('il_cybersource') or {}
   print(json.dumps({'site':site,'payments_paused':bool(frappe.conf.get('il_payments_paused')),'sandbox_enabled':config.get('enabled') is True and config.get('mode')=='sandbox','platform_merchant_configured':'platform' in (config.get('merchants') or {})}))
   assert frappe.conf.get('il_four_plan_lkr_enabled')==1
   assert frappe.conf.get('il_student_password_login_enabled')==1
   for role in ('Teacher','Institute'):
    account=SimpleNamespace(role=role)
    for plan in ('Individual','Silver','Gold','Platinum'):
     assert account_billing.price(account,plan)==plan_catalog.plan(plan)['monthly_lkr']*100
    assert account_billing.currency_for(account)=='LKR'
   assert not portal_policy.student_password_account('Guest')
   print('PASS: '+site+' provider prices match published catalogue; guest password policy denied.')
   if site=='sisuacademylk.com':
    user='sisu.student.test@gmail.com'
    if frappe.db.exists('User',user):
     assert portal_policy.student_password_account(user),'Named student is disabled or unavailable'
     members=frappe.get_all('IL Member',filters={'user':user,'role':'Student','active':1},pluck='name')
     rows=frappe.get_all('IL Invoice',filters={'student':['in',members or ['__none__']]},fields=['name','classroom','status','amount'],order_by='creation desc',limit_page_length=12)
     print('TEST STUDENT INVOICES: '+json.dumps([dict(r) for r in rows],default=str))
     print('PASS: enabled named student is eligible for normal password login. Password itself was not inspected or reset.')
  finally:frappe.db.rollback();frappe.destroy()
 print('READ ONLY: no account, invoice, payment, email or SMS changed. Browser signup, slip upload and gateway acceptance still require live testing.')
if __name__=='__main__':main()
