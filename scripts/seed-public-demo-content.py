"""Idempotent public demo institute; no existing real accounts changed."""
import os,logging
from pathlib import Path
from datetime import timedelta
from contextlib import ExitStack
from unittest.mock import patch
BENCH=Path('/home/sisu/frappe-bench');CODE='SISUDEMO'
ADMIN='sisu-public-demo-admin@example.invalid';TEACHER='sisu-public-demo-teacher@example.invalid'
def deny(*a,**kw):raise RuntimeError('Unexpected delivery; demo transaction rolled back')
def deferred(*a,**kw):
 if kw.get('enqueue_after_commit') is True and not kw.get('now'):return None
 deny()
def refresh(event=None,*a,**kw):
 if event in ('doc_update','list_update') and kw.get('after_commit') is True:return None
 deny()
def main():
 if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
 logging.disable(logging.CRITICAL)
 import frappe,requests,smtplib
 from frappe.utils import now_datetime
 from institute_lms.campus_provisioning import institute_insert
 from institute_lms.membership_write import authorized_insert
 from institute_lms.profiles import write
 os.chdir(BENCH/'sites');frappe.init(site='sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect();frappe.set_user('Administrator')
 try:
  if not frappe.conf.get('il_shared_campus_enabled') or not frappe.conf.get('il_payments_paused'):raise RuntimeError('Shared public site and payment pause required')
  if frappe.conf.get('il_whatsapp_token') or frappe.conf.get('il_whatsapp_phone_id'):raise RuntimeError('Expected WhatsApp to remain unconfigured')
  with ExitStack() as stack:
   for obj,key,fn in [(frappe,'sendmail',deny),(frappe,'enqueue',deferred),(frappe,'publish_realtime',refresh),(requests.sessions.Session,'request',deny),(smtplib.SMTP,'sendmail',deny)]:stack.enter_context(patch.object(obj,key,fn))
   for email,title in [(ADMIN,'Demo Institute'),(TEACHER,'Demo Teacher')]:
    if frappe.db.exists('User',email):
     if frappe.db.get_value('User',email,'enabled'):raise RuntimeError('Demo fixture unexpectedly enabled; not changed')
    else:frappe.get_doc(dict(doctype='User',email=email,first_name=title,enabled=0,user_type='Website User',send_welcome_email=0)).insert(ignore_permissions=True)
   name=frappe.db.get_value('IL Institute',{'code':CODE},'name')
   if name:
    inst=frappe.get_doc('IL Institute',name)
    if inst.title!='[DEMO] SISU Practice Institute':raise RuntimeError('Demo code belongs to another institute')
   else:
    inst=frappe.get_doc(dict(doctype='IL Institute',code=CODE,title='[DEMO] SISU Practice Institute',language='en',billing_day=1))
    with institute_insert(inst):inst.insert(ignore_permissions=True)
   members={}
   for email,role in [(ADMIN,'Admin'),(TEACHER,'Teacher')]:
    name=frappe.db.get_value('IL Member',{'institute':inst.name,'user':email},'name')
    doc=frappe.get_doc('IL Member',name) if name else frappe.get_doc(dict(doctype='IL Member',institute=inst.name,user=email,role=role,full_name='[DEMO] '+role,active=1,language='en',email_opt_in=0,whatsapp_opt_in=0))
    if name:
     if doc.role!=role or not doc.active:raise RuntimeError('Demo membership changed; review required')
    else:
     with authorized_insert(doc):doc.insert(ignore_permissions=True)
    members[role]=doc
   profiles={}
   for email,kind,username,title in [(ADMIN,'Institute','sisu_public_demo_institute','[DEMO] SISU Practice Institute'),(TEACHER,'Teacher','sisu_public_demo_teacher','[DEMO] Mathematics Teacher')]:
    name=frappe.db.get_value('IL Public Profile',{'user':email},'name')
    if name:
     profile=frappe.get_doc('IL Public Profile',name)
     if profile.kind!=kind or profile.username!=username:raise RuntimeError('Demo profile conflict')
    else:
     profile=write(frappe.get_doc(dict(doctype='IL Public Profile',user=email,kind=kind,username=username,display_name=title,country='Sri Lanka',status='Verified',workspace=inst.name if kind=='Institute' else None,bio='Fictional SISU demonstration. No real teaching service or payment. Register to explore free practice and a locked paid example.')))
    profiles[kind]=profile
   import hashlib
   relationship_key=hashlib.sha256((TEACHER+':'+profiles['Institute'].name+':Teacher membership').encode()).hexdigest()
   if not frappe.db.exists('IL Profile Relationship',{'relationship_key':relationship_key}):
    write(frappe.get_doc(dict(doctype='IL Profile Relationship',relationship_key=relationship_key,profile=profiles['Institute'].name,user=TEACHER,kind='Teacher membership',status='Active')))
   from institute_lms.account_billing import account
   sub=account(inst,members['Admin'],create=True)
   # Demo-only, time-bounded entitlement; never renew it on reruns.
   if sub.plan=='Individual':frappe.db.set_value('IL Account Subscription',sub.name,{'plan':'Gold','trial_until':now_datetime()+timedelta(days=30)})
   from institute_lms.commercial import account_for,save
   from institute_lms.commercial_rules import beneficiary
   provider=account_for(frappe._dict(institute=inst.name,owner_type='Institute'),False)
   if not provider:save(frappe.get_doc(dict(doctype='IL Provider Account',provider_key=beneficiary({'institute':inst.name,'owner_type':'Institute'}),institute=inst.name,owner_type='Institute',plan='Gold',enabled=1,billing_email=ADMIN,cycle_start=now_datetime(),cycle_end=now_datetime()+timedelta(days=30))))
   elif provider.plan!='Gold':raise RuntimeError('Demo provider package changed; review required')
   for mode,fee,title in [('Free',0,'[DEMO] Free mathematics practice'),('Paid',1000,'[DEMO] Locked class - do not pay')]:
    name=frappe.db.get_value('IL Classroom',{'institute':inst.name,'title':title},'name')
    if name:
     room=frappe.get_doc('IL Classroom',name)
     if room.fee_mode!=mode or float(room.fee)!=fee:raise RuntimeError('Demo class fee changed; review required')
    else:frappe.get_doc(dict(doctype='IL Classroom',institute=inst.name,title=title,subject='Mathematics',teacher=members['Teacher'].name,font='sans',active=1,owner_type='Institute',public_provider=profiles['Institute'].name,fee_mode=mode,fee=fee,published=1,description='Fictional demo. Free practice: solve 2x + 3 = 11. Subtract 3, then divide by 2: x = 4. Try 3x + 6 = 21 (answer: 5). The paid example is intentionally locked; do not make payment.')).insert(ignore_permissions=True)
   frappe.db.commit()
  print('SAVED: labelled public demo institute, disabled display-only teacher/admin and published free/locked classes.')
  print('Students: verify account, find [DEMO] SISU Practice Institute, follow/register, select it and join the free class.')
  print('No students auto-enrolled, no paid grants, no messages or jobs dispatched. Demo entitlement lasts 30 days and reruns do not extend it.')
  print('Payments paused; WhatsApp unchanged. Browser registration, free access and locked-class denial still require acceptance testing.')
 finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('STOPPED: '+type(exc).__name__+'. No credentials displayed. Transaction rolled back if not committed.')
  raise SystemExit(1) from None
