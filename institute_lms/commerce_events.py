"""Minimized signed tenant reports. Never queries a tenant database from control plane."""
import hashlib,json,hmac,time
from datetime import timedelta
import frappe,requests
from frappe.utils import now_datetime
from .saas import managed
from .saas_rules import sign

FIELDS=('event_key','tenant_id','purpose','amount_minor','currency','status','occurred_at','reference_hash')

def observe(doc,method=None):
    if frappe.conf.get('il_control_plane') or not frappe.conf.get('il_tenant_id'):return
    purpose={'IL Lecture Order':'lesson','IL Invoice':'class'}.get(doc.doctype)
    if not purpose or not doc.has_value_changed('status'):return
    status=str(doc.status).lower()
    if status not in ('paid','succeeded','failed','cancelled','refunded'):return
    reference=hashlib.sha256((frappe.local.site+':'+doc.doctype+':'+doc.name).encode()).hexdigest()
    key=hashlib.sha256((reference+':'+status).encode()).hexdigest()
    if frappe.db.exists('IL Commerce Event',{'event_key':key}):return
    amount=int(doc.amount_minor) if purpose=='lesson' else round(float(doc.amount)*100)
    managed(frappe.get_doc({'doctype':'IL Commerce Event','event_key':key,'tenant_id':frappe.conf.il_tenant_id,
        'purpose':purpose,'amount_minor':amount,'currency':doc.currency or 'LKR','status':status,
        'occurred_at':now_datetime(),'reference_hash':reference,'delivery_status':'Pending','attempts':0,'next_attempt':now_datetime()}))

def deliver():
    if frappe.conf.get('il_control_plane'):return
    from .release import https_origin
    origin=https_origin(frappe.conf.get('il_control_plane_url'));key=frappe.conf.get('il_control_plane_key')
    if not origin or not key:return
    for name in frappe.get_all('IL Commerce Event',filters={'delivery_status':'Pending','next_attempt':['<=',now_datetime()]},pluck='name',limit_page_length=50):
        d=frappe.get_doc('IL Commerce Event',name,for_update=True)
        if d.delivery_status!='Pending':continue
        value={k:d.get(k) for k in FIELDS};value['occurred_at']=str(value['occurred_at'])
        payload={'site_hostname':frappe.local.site,'issued_at':int(time.time()),'event':value}
        try:
            r=requests.post(origin+'/api/method/institute_lms.commerce_events.receive',json={'payload':json.dumps(payload),'signature':sign(payload,key)},timeout=(5,15),allow_redirects=False)
            r.raise_for_status()
            if r.json().get('message',{}).get('ack')!=d.event_key:raise ValueError('ack')
            d.delivery_status='Acknowledged';d.ack_at=now_datetime()
        except Exception:
            d.attempts=int(d.attempts or 0)+1
            d.next_attempt=now_datetime()+timedelta(minutes=min(1440,2**min(d.attempts,10)))
        managed(d);frappe.db.commit()

@frappe.whitelist(allow_guest=True,methods=['POST'])
def receive(payload,signature):
    from .platform import control
    control()
    if not isinstance(payload,str) or len(payload)>4000:frappe.throw('Invalid commerce report')
    value=json.loads(payload);e=value.get('event',{})
    if set(e)!=set(FIELDS):frappe.throw('Unexpected commerce report fields')
    key=(frappe.conf.get('il_tenant_signing_keys') or {}).get(e.get('tenant_id'))
    if not key or not hmac.compare_digest(sign(value,key),str(signature)):frappe.throw('Invalid report signature',frappe.PermissionError)
    org=frappe.get_doc('IL Organization',e['tenant_id'],for_update=True)
    if value.get('site_hostname')!=org.site_hostname or abs(time.time()-int(value.get('issued_at',0)))>120:frappe.throw('Invalid report scope',frappe.PermissionError)
    import re
    if (e['purpose'] not in ('lesson','class') or e['status'] not in ('paid','succeeded','failed','cancelled','refunded')
        or type(e['amount_minor']) is not int or not 0<=e['amount_minor']<=2000000000
        or e['currency'] not in ('LKR','USD') or any(not re.fullmatch('[a-f0-9]{64}',str(e[k])) for k in ('event_key','reference_hash'))):frappe.throw('Invalid report data')
    old=frappe.db.get_value('IL Commerce Event',{'event_key':e['event_key']},'name')
    if old:
        d=frappe.get_doc('IL Commerce Event',old)
        if any(str(d.get(k))!=str(e[k]) for k in FIELDS if k!='occurred_at'):frappe.throw('Report identity conflict')
    else:managed(frappe.get_doc({'doctype':'IL Commerce Event',**e,'delivery_status':'Acknowledged','ack_at':now_datetime()}))
    return {'ack':e['event_key']}

@frappe.whitelist()
def listing(tenant=None,page=0):
    from .platform import owner
    owner()
    filters={'tenant_id':tenant} if tenant else {}
    return frappe.get_all('IL Commerce Event',filters=filters,fields=list(FIELDS)+['delivery_status','ack_at'],
        order_by='occurred_at desc',start=max(0,min(int(page),10000))*50,limit_page_length=50)
