"""Read-only password-setup diagnosis. Never prints tokens, passwords or email bodies."""
import os,json,inspect,re
EMAIL='tharukakarunarathne60@gmail.com'
def main():
 os.chdir('/home/sisu/frappe-bench/sites')
 import frappe
 frappe.init(site='platform.sisuacademylk.com');frappe.connect()
 try:
  from frappe.core.doctype.user import user as module
  exists=bool(frappe.db.exists('User',EMAIL));out={'site':frappe.local.site,'account_exists':exists}
  if exists:
   d=frappe.get_doc('User',EMAIL)
   out.update(enabled=bool(d.enabled),user_type=d.user_type,reset_token_present=bool(d.get('reset_password_key')),last_password_reset_date=str(d.get('last_password_reset_date') or ''),reset_requested_at=str(d.get('last_reset_password_key_generated_on') or ''),billing_contact=bool(frappe.db.exists('IL Organization',{'admin_contact':EMAIL})))
  out['settings']={k:frappe.db.get_single_value('System Settings',k) for k in ('enable_password_policy','minimum_password_score','disable_user_pass_login') if frappe.get_meta('System Settings').has_field(k)}
  print(json.dumps(out,default=str))
  # These are installed program sources, not request data or user credentials.
  for name,fn in [('update_password',getattr(module,'update_password',None)),('_reset_password',getattr(module.User,'_reset_password',None)),('reset_password',getattr(module.User,'reset_password',None))]:
   if callable(fn):
    print('\nINSTALLED IMPLEMENTATION '+name+' '+str(inspect.signature(fn)))
    print(inspect.getsource(fn))
  print('READ ONLY: no password, token, account, session or mail changed; no secret values displayed.')
 finally:frappe.db.rollback();frappe.destroy()
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print('DIAGNOSTIC ERROR: '+type(exc).__name__)
  raise SystemExit(1) from None
