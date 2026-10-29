"""Retryable TLS policy transport. Never opens another site's database."""
from datetime import timedelta
import frappe
import requests
from frappe.utils import now_datetime
from .saas import managed

def changed(doc, method=None):
    if not frappe.conf.get('il_control_plane'):return
    before=doc.get_doc_before_save()
    keys=('enabled','plan','state','ends_at','grace_until','features','limits','overrides','base_features','base_limits','site_hostname')
    if before and all(before.get(k)==doc.get(k) for k in keys):return
    tenant=doc.name if doc.doctype=='IL Organization' else doc.tenant_id
    # Registration inserts organization before its subscription; scheduler resolves later.
    name=frappe.db.get_value('IL Policy Delivery',{'organization':tenant},'name')
    d=frappe.get_doc('IL Policy Delivery',name) if name else frappe.get_doc({'doctype':'IL Policy Delivery','organization':tenant})
    d.status='Pending';d.next_attempt=now_datetime();managed(d)

def dispatch():
    if not frappe.conf.get('il_control_plane'):return
    rows=frappe.get_all('IL Policy Delivery',filters={'next_attempt':['<=',now_datetime()]},pluck='name',limit_page_length=50)
    for name in rows:
        with frappe.cache.lock('il_policy_delivery:'+name,timeout=120,blocking_timeout=1):
            d=frappe.get_doc('IL Policy Delivery',name,for_update=True)
            sent_modified=str(d.modified)
            try:
                org=frappe.get_doc('IL Organization',d.organization)
                allowed=frappe.conf.get('il_policy_delivery_hosts') or []
                if org.site_hostname not in allowed:raise ValueError('policy_host_not_allowlisted')
                from .platform import signed_policy
                payload=signed_policy(org.name)
                # Save issued revision before delivery; a crash retries a newer revision safely.
                frappe.db.commit()
                response=requests.post('https://'+org.site_hostname+'/api/method/institute_lms.saas.apply_manifest',
                    json=payload,timeout=(5,20),allow_redirects=False)
                response.raise_for_status()
                body=response.json().get('message',{})
                import json
                revision=json.loads(payload['payload'])['revision']
                if body.get('applied') is not True or body.get('revision')!=revision:raise ValueError('policy_acknowledgement_invalid')
                for notice in json.loads(payload['payload']).get('notices',[]):
                    n=frappe.get_doc('IL Subscription Notice',notice['name'],for_update=True);n.acknowledged=1;managed(n)
                d=frappe.get_doc('IL Policy Delivery',name,for_update=True)
                changed_while_sending=str(d.modified)!=sent_modified or bool(frappe.db.exists('IL Subscription Notice',{'tenant_id':org.name,'acknowledged':0}))
                d.status='Pending' if changed_while_sending else 'Delivered'
                d.revision=revision;d.acknowledged_at=now_datetime();d.error_code=None;d.attempts=0
                d.next_attempt=now_datetime() if changed_while_sending else now_datetime()+timedelta(hours=12)
            except Exception:
                # Never persist provider response/configuration/keys in an error record.
                frappe.db.rollback()
                d=frappe.get_doc('IL Policy Delivery',name,for_update=True)
                d.status='Failed';d.attempts=int(d.attempts or 0)+1;d.error_code='delivery_failed_check_configuration_or_connectivity'
                d.next_attempt=now_datetime()+timedelta(minutes=min(60,2**min(d.attempts,6)))
            managed(d);frappe.db.commit()
