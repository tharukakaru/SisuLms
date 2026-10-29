"""Owner-authorized, signed HTTPS billing RPC. No cross-site DB access.

Off by default. Requires an explicitly allowlisted tenant hostname on control
plane and matching per-tenant keys. Replies are authenticated and request-bound.
"""
import json,time,uuid
import frappe,requests
from .billing_transport_rules import sign_message,verify_message,fingerprint
from .saas_rules import hostname
PUBLIC_FIELDS=['name','subscription','period_start','period_end','due_at','plan','unit_rate','quantity','amount_lkr','status','issued_at','suspended','activation_requested']

def enabled():
    if not frappe.conf.get('il_billing_transport_enabled'):
        frappe.throw('Cross-tenant billing is not enabled',frappe.PermissionError)

def call_tenant(tenant,action,data):
    from .platform import owner
    owner();enabled()
    org=frappe.get_doc('IL Organization',tenant)
    host=hostname(org.site_hostname)
    if not org.enabled or host not in (frappe.conf.get('il_billing_transport_hosts') or []):
        frappe.throw('Tenant billing host not enabled',frappe.PermissionError)
    key=(frappe.conf.get('il_tenant_signing_keys') or {}).get(org.tenant_id)
    payload=dict(tenant_id=org.tenant_id,site_hostname=host,issued_at=int(time.time()),request_id=uuid.uuid4().hex,action=action,data=data,reviewer=frappe.session.user)
    signature=sign_message(payload,key)
    session=requests.Session();session.trust_env=False
    try:
        response=session.post('https://'+host+'/api/method/institute_lms.billing_transport.receive',json={'payload':json.dumps(payload),'signature':signature},timeout=(5,20),allow_redirects=False)
        response.raise_for_status()
        body=response.json()['message'];reply=body['payload']
        verify_message(reply,body['signature'],key,org.tenant_id,host,int(time.time()))
        if reply['action']!='reply' or reply['request_id']!=payload['request_id']:raise ValueError('Reply binding mismatch')
        return reply['data']
    except (requests.RequestException,ValueError,KeyError,TypeError):
        frappe.throw('Tenant billing request could not be confirmed. Refresh invoice status before retrying.')
    finally:session.close()

@frappe.whitelist(methods=['POST'])
def invoices(tenant,page=0):
    page=int(page)
    if not 0<=page<=10000:frappe.throw('Invalid page')
    return call_tenant(tenant,'list',{'page':page})

@frappe.whitelist(methods=['POST'])
def verify_payment(tenant,invoice,snapshot,reference,amount_lkr,reason):
    return call_tenant(tenant,'settle',dict(invoice=invoice,snapshot=snapshot,reference=reference,amount_lkr=amount_lkr,reason=reason))

@frappe.whitelist(allow_guest=True,methods=['POST'])
def receive(payload,signature):
    enabled()
    if frappe.conf.get('il_control_plane'):frappe.throw('Tenant endpoint only',frappe.PermissionError)
    if not isinstance(payload,str) or len(payload)>32000:frappe.throw('Invalid payload')
    key=frappe.conf.get('il_control_plane_key')
    tenant=frappe.conf.get('il_tenant_id')
    if not tenant:frappe.throw('Tenant identity required',frappe.PermissionError)
    try:
        message=verify_message(json.loads(payload),signature,key,tenant,frappe.local.site,int(time.time()))
    except (ValueError,TypeError):frappe.throw('Invalid signed billing request',frappe.PermissionError)
    data=message.get('data')
    if not isinstance(data,dict):frappe.throw('Invalid request data')
    from . import usage_billing as usage
    if not usage.enabled():frappe.throw('Usage billing disabled')
    if message['action']=='list':
        page=data.get('page',0)
        if type(page)is not int or not 0<=page<=10000:frappe.throw('Invalid page')
        rows=frappe.get_all(usage.DT,fields=PUBLIC_FIELDS,order_by='creation desc, name desc',start=page*50,limit_page_length=50)
        result={'invoices':[]}
        for row in rows:
            item={k:str(row[k]) if k.endswith('_at') or k in ('period_start','period_end') else row[k] for k in PUBLIC_FIELDS}
            item['snapshot']=fingerprint(row);result['invoices'].append(item)
    elif message['action']=='settle':
        reviewer=message.get('reviewer')
        if not isinstance(reviewer,str) or not 1<=len(reviewer)<=140:frappe.throw('Reviewer required')
        invoice=data.get('invoice')
        if not isinstance(invoice,str):frappe.throw('Invoice required')
        doc=frappe.get_doc(usage.DT,invoice,for_update=True)
        if not doc.issued_at or data.get('snapshot')!=fingerprint(doc):frappe.throw('Invoice snapshot changed; refresh review')
        # Persisted settlement reference makes identical retries idempotent.
        expected='bank:'+str(data.get('reference','')).strip()
        if doc.status=='Paid':
            if doc.payment_reference!=expected or str(data.get('amount_lkr'))!=str(doc.amount_lkr):frappe.throw('Settlement conflicts with recorded payment')
            result={'verified':True,'invoice_reactivated':not bool(doc.suspended),'already_applied':True}
        else:
            result=usage.settle_verified(invoice,data.get('reference',''),data.get('amount_lkr'),data.get('reason',''),remote_reviewer=reviewer)
    else:frappe.throw('Invalid request action')
    reply=dict(tenant_id=tenant,site_hostname=frappe.local.site,issued_at=int(time.time()),request_id=message['request_id'],action='reply',data=result)
    return {'payload':reply,'signature':sign_message(reply,key)}
