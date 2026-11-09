"""Assign the verified, explicitly requested test teacher to demo institute rooms only."""
import os
from pathlib import Path
from datetime import timedelta
BENCH=Path('/home/sisu/frappe-bench')
USER='sisu.student.test+teacher@gmail.com'
def main():
 if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
 import frappe
 from frappe.utils import now_datetime
 os.chdir(BENCH/'sites');frappe.init(site='sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect();frappe.set_user('Administrator')
 try:
  if not frappe.conf.get('il_payments_paused'):raise RuntimeError('Payment pause required')
  profile=frappe.db.get_value('IL Public Profile',{'user':USER,'kind':'Teacher','status':'Verified'},'name')
  if not profile or not frappe.db.get_value('User',USER,'enabled'):
   print('PENDING: test teacher must complete signup and verification first: '+USER);return
  inst=frappe.db.get_value('IL Institute',{'code':'SISUDEMO','title':'[DEMO] SISU Practice Institute'},'name')
  if not inst:raise RuntimeError('Demo institute missing')
  from institute_lms.membership_write import authorized_insert
  name=frappe.db.get_value('IL Member',{'user':USER,'institute':inst},'name')
  if name:
   member=frappe.get_doc('IL Member',name)
   if member.role!='Teacher' or not member.active:raise RuntimeError('Existing test membership requires review')
  else:
   member=frappe.get_doc({'doctype':'IL Member','user':USER,'institute':inst,'role':'Teacher','full_name':'SISU Test Teacher','active':1,'language':'en','email_opt_in':0,'whatsapp_opt_in':0})
   with authorized_insert(member):member.insert(ignore_permissions=True)
  from institute_lms.account_billing import account,sync_provider
  sub=account(frappe.get_doc('IL Institute',inst),member,create=True)
  if sub.plan=='Individual':
   frappe.db.set_value('IL Account Subscription',sub.name,{'plan':'Gold','trial_until':now_datetime()+timedelta(days=30)})
   sub.reload();sync_provider(sub)
  providers=frappe.get_all('IL Public Profile',filters={'user':['in',['sisu-public-demo-admin@example.invalid','sisu-public-demo-teacher@example.invalid']]},pluck='name')
  rooms=frappe.get_all('IL Classroom',filters={'institute':inst,'public_provider':['in',providers],'title':['like','[DEMO] %']},pluck='name')
  for name in rooms:frappe.db.set_value('IL Classroom',name,'teacher',member.name)
  frappe.db.commit()
  print('READY: verified test teacher assigned to '+str(len(rooms))+' demo institute classrooms. Sign in, choose the demo institute and start a live session.')
  print('No passwords, contact verification, real classrooms or payment settings changed. Test package is time bounded; reruns do not extend it.')
 finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
 try:main()
 except Exception as exc:print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__));raise SystemExit(1) from None
