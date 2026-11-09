"""Read-only verification for the scoped owner invitation service."""
import os,json,time

def main():
 os.chdir('/home/sisu/frappe-bench/sites')
 import frappe
 frappe.init(site='platform.sisuacademylk.com');frappe.connect()
 try:
  methods={'institute_lms.health.heartbeat','institute_lms.owner_invitation_delivery.dispatch'}
  active=frappe.get_all('Scheduled Job Type',filters={'stopped':0},fields=['method','last_execution'])
  assert {r.method for r in active}==methods,'Unexpected active scheduled jobs'
  assert frappe.conf.get('il_owner_invitation_delivery_enabled'),'Invitation service is not enabled'
  assert frappe.db.get_single_value('System Settings','enable_scheduler'),'Owner scheduler is not enabled'
  assert frappe.db.get_default('suspend_email_queue'),'General mail hold was removed'
  assert frappe.conf.get('il_payments_paused'),'Payment hold was removed'
  stamp=frappe.cache.get_value('il_release_worker_heartbeat')
  print(json.dumps({'site':frappe.local.site,'active_jobs':active,'heartbeat_age_seconds':round(time.time()-float(stamp)) if stamp else None,'email_queue':{s:frappe.db.count('Email Queue',{'status':s}) for s in ('Not Sent','Sent','Error')},'general_mail_held':True,'payments_held':True},default=str))
  print('PASS: only heartbeat and scoped invitation delivery enabled. A null heartbeat immediately after activation means the first scheduled run is still pending.')
 finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('CHECK FAILED: '+(str(exc) if isinstance(exc,AssertionError) else type(exc).__name__))
  raise SystemExit(1) from None
