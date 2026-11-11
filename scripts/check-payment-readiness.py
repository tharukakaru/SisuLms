"""Read-only sandbox readiness; never print secrets or create payments."""
import json,os
from pathlib import Path
os.chdir('/home/sisu/frappe-bench/sites')
import frappe
for site in ('sisuacademylk.com','teen.sisuacademylk.com','staging.sisuacademylk.com'):
 frappe.init(site=site);frappe.connect()
 try:
  root=frappe.conf.get('il_cybersource') or {}
  if not isinstance(root,dict):root={}
  merchant=(root.get('merchants') or {}).get('platform') or {}
  fields=('merchant_id','key_id','p12_path','p12_password')
  print(json.dumps({'site':site,'paused':bool(frappe.conf.get('il_payments_paused')),'enabled':root.get('enabled') is True,'mode':root.get('mode'),'origin':root.get('origin'),'credential_fields_present':{k:bool(merchant.get(k)) for k in fields},'certificate_readable':bool(merchant.get('p12_path') and os.path.isfile(merchant['p12_path']) and os.access(merchant['p12_path'],os.R_OK)),'methods':merchant.get('methods',[])}))
 finally:frappe.destroy()
print('READ ONLY: no secrets printed, requests sent, payments started or settings changed.')
