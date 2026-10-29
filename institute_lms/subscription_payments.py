"""Organization -> SISU billing on the control plane; distinct merchant credentials.

Uses the existing Payments.lk transport and raw-body signature contract. Tenant
activation is propagated using platform.manifest, never a frontend return URL.
"""
import hashlib
import json
import re
import uuid
from datetime import timedelta, datetime
import frappe
from frappe.utils import now_datetime, get_datetime, get_url
from .saas import managed, audit
from .saas_rules import resolve, transition_payment
from .payments_lk_contract import valid_payment, hosted_url, verify_signature, amount_cents

def config():
    from .platform import control
    control()
    mode=frappe.conf.get('il_subscription_payments_lk_mode','test')
    key=frappe.conf.get('il_subscription_payments_lk_secret_key','')
    secret=frappe.conf.get('il_subscription_payments_lk_webhook_secret','')
    if mode not in ('test','live') or not key.startswith('sk_'+mode+'_') or not secret.startswith('whsec_'):
        frappe.throw('SISU subscription merchant is not configured')
    if not get_url().startswith('https://'):frappe.throw('HTTPS required')
    return key,secret,mode

@frappe.whitelist(methods=['POST'])
def quote(tenant, plan):
    from .platform import organization
    from .registration import limit
    d=organization(tenant,administrator=True);limit('subscription-quote:'+frappe.session.user)
    if not d.enabled or plan != 'PREMIUM AI':frappe.throw('Only the monthly Premium offer requires checkout')
    from .premium import offer_for
    offer=offer_for(tenant)
    if not offer['available']:frappe.throw(offer['message'])
    p=frappe.get_doc('IL SaaS Plan',plan)
    total=offer['amount_minor'];assignment=offer['assignment'];days=30
    amount_cents(total/100)
    s=frappe.get_doc('IL Subscription',frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name'))
    r=resolve(p.features,p.limits,s.overrides or '{}')
    snapshot={'plan':plan,'features':r['features'],'limits':r['limits'],'support_tier':r['support_tier'],'period_days':days,'plan_version':p.version,'billing_cycle':'calendar_month','price_version':offer['version']}
    snapshot['overrides']=json.loads(s.overrides or '{}')
    q=frappe.get_doc({'doctype':'IL Checkout Quote','customer':d.admin_contact,'assignment':assignment,
        'product':'Platform','currency':'LKR','period':'Yearly' if days>31 else 'Monthly','total_minor':total,
        'breakdown':json.dumps({'total_minor':total}),'expires_at':now_datetime()+timedelta(minutes=15),
        'status':'Open','tenant_id':tenant,'plan_snapshot':json.dumps(snapshot)})
    q.flags.pricing_service=True;q.insert(ignore_permissions=True)
    return {'quote':q.name,'total_minor':total,'currency':'LKR','expires_at':q.expires_at,'plan':plan}

@frappe.whitelist(methods=['POST'])
def checkout(quote,mobile=False):
    from .platform import organization
    from .payments_lk import provider_request
    key,_,mode=config()
    frappe.db.sql('SELECT name FROM `tabIL Checkout Quote` WHERE name=%s FOR UPDATE',(quote,))
    q=frappe.get_doc('IL Checkout Quote',quote,for_update=True);organization(q.tenant_id,administrator=True)
    if q.product!='Platform' or not q.plan_snapshot or q.status!='Open':frappe.throw('Subscription quote unavailable')
    name=frappe.db.get_value('IL Payment Attempt',{'quote':quote},'name')
    if name:a=frappe.get_doc('IL Payment Attempt',name,for_update=True)
    else:
        if get_datetime(q.expires_at)<=now_datetime():frappe.throw('Quote expired')
        a=frappe.get_doc({'doctype':'IL Payment Attempt','attempt_id':'sub-'+uuid.uuid4().hex,'quote':q.name,
            'tenant_id':q.tenant_id,'amount_minor':q.total_minor,'currency':'LKR','mode':mode,'status':'created',
            'request_key':'sisu-sub-'+uuid.uuid4().hex,'snapshot':q.plan_snapshot})
        a.request=json.dumps({'amountCents':q.total_minor,'reference':a.attempt_id,'description':'SISU organization subscription',
            'successUrl':get_url('/mobile_payment_return' if mobile is True else '/campus?subscription=returned'),'cancelUrl':get_url('/mobile_payment_return' if mobile is True else '/campus?subscription=cancelled'),'locale':'en'},separators=(',',':'))
        managed(a)
    if a.mode!=mode or a.status in ('succeeded','failed','cancelled'):frappe.throw('Reconcile terminal payment before creating another quote')
    if get_datetime(a.creation)<now_datetime()-timedelta(hours=23):frappe.throw('Payment attempt needs reconciliation')
    a.status='pending';managed(a);frappe.db.commit()
    # Stable idempotency key also protects concurrent checkout retries.
    result=provider_request('GET','/checkouts/'+a.checkout_id,key) if a.checkout_id else provider_request('POST','/checkouts',key,a.request,a.request_key)
    payment=result.get('payment') or {}
    if (result.get('mode')!=mode or not hosted_url(result.get('url')) or payment.get('reference')!=a.name
        or payment.get('amountCents')!=a.amount_minor or payment.get('currency')!='LKR'
        or not re.fullmatch(r'chk_[A-Za-z0-9]{24}',str(result.get('id','')))):
        frappe.throw('Checkout response failed validation; reconcile the saved attempt')
    frappe.db.sql('SELECT name FROM `tabIL Payment Attempt` WHERE name=%s FOR UPDATE',(a.name,));a=frappe.get_doc('IL Payment Attempt',a.name,for_update=True)
    if a.checkout_id and a.checkout_id!=result['id']:frappe.throw('Checkout identity changed')
    a.checkout_id=result['id'];managed(a)
    if result.get('status')!='open':
        frappe.db.commit();frappe.throw('Checkout not open; await signed settlement or reconcile')
    return {'attempt':a.name,'redirect_url':result['url']}

def settle(a, payment):
    """Private transaction step, called only after signed payment validation."""
    organization=frappe.get_doc('IL Organization',a.tenant_id,for_update=True)
    name=frappe.db.get_value('IL Subscription',{'tenant_id':a.tenant_id},'name')
    frappe.db.sql('SELECT name FROM `tabIL Subscription` WHERE name=%s FOR UPDATE',(name,))
    s=frappe.get_doc('IL Subscription',name,for_update=True)
    if frappe.db.exists('IL Payment Transaction',{'attempt':a.name}):return
    snapshot=json.loads(a.snapshot);now=datetime.utcnow()
    base=max(now,get_datetime(s.ends_at)) if s.ends_at and s.plan==snapshot['plan'] else now
    from .full_rules import month_end
    end=month_end(base) if snapshot.get('billing_cycle')=='calendar_month' else base+timedelta(days=int(snapshot['period_days']))
    managed(frappe.get_doc({'doctype':'IL Payment Transaction','attempt':a.name,'payment_id':payment['id'],
        'tenant_id':a.tenant_id,'amount_minor':a.amount_minor,'currency':a.currency,'settled_at':now}))
    s.plan=snapshot['plan'];s.features=json.dumps(snapshot['features']);s.limits=json.dumps(snapshot['limits']);s.overrides=json.dumps(snapshot.get('overrides') or {})
    s.support_tier=snapshot.get('support_tier','standard')
    s.state='suspended' if s.state=='suspended' else 'active';s.starts_at=s.starts_at or now;s.ends_at=end;s.grace_until=None;s.last_payment=a.name
    # Payment cannot undo an administrative organization suspension.
    managed(s)
    organization.plan=s.plan;managed(organization)
    q=frappe.get_doc('IL Checkout Quote',a.quote);q.status='Settled';q.flags.pricing_service=True;q.save(ignore_permissions=True)
    from .premium import settled_receipt
    settled_receipt(a,base,end,payment)
    audit('Verified subscription settlement',a.tenant_id,a.name)

@frappe.whitelist(allow_guest=True,methods=['POST'])
def notify(**kwargs):
    _,secret,mode=config();raw=frappe.request.get_data(cache=True)
    if len(raw)>65536 or not verify_signature(raw,frappe.request.headers.get('Payments-Signature'),secret):
        frappe.throw('Invalid payment signature',frappe.PermissionError)
    try:event=json.loads(raw)
    except (ValueError,UnicodeError):frappe.throw('Invalid payment event')
    if not isinstance(event,dict) or event.get('mode')!=mode:frappe.throw('Wrong payment mode')
    mapping={'payment.succeeded':'succeeded','payment.failed':'failed','payment.cancelled':'cancelled'}
    incoming=mapping.get(event.get('type'))
    if not incoming:return {'accepted':True,'settled':False}
    p=event.get('data')
    if not isinstance(p,dict) or not isinstance(p.get('reference'),str):frappe.throw('Invalid payment identity')
    rows=frappe.db.sql('SELECT name FROM `tabIL Payment Attempt` WHERE name=%s FOR UPDATE',(p['reference'],))
    if not rows:frappe.throw('Unknown subscription attempt')
    a=frappe.get_doc('IL Payment Attempt',p['reference'])
    binding={'name':a.name,'amount':a.amount_minor/100,'gateway_checkout_id':a.checkout_id}
    if incoming=='succeeded':valid=valid_payment(p,binding,mode)
    else:
        valid=(p.get('mode')==mode and p.get('currency')==a.currency and type(p.get('amountCents')) is int
               and p['amountCents']==a.amount_minor and bool(a.checkout_id) and p.get('checkoutId')==a.checkout_id
               and p.get('object')=='payment' and p.get('status')==incoming
               and re.fullmatch(r'pay_[A-Za-z0-9]{24}',str(p.get('id',''))))
    if not valid or a.mode!=mode:frappe.throw('Payment binding mismatch',frappe.PermissionError)
    digest=hashlib.sha256(raw).hexdigest()
    if frappe.db.exists('IL Webhook Event',{'event_key':digest}):return {'accepted':True,'duplicate':True}
    if a.status=='succeeded' and incoming=='succeeded' and a.payment_id!=p['id']:frappe.throw('Already settled with another payment')
    if incoming=='succeeded' and a.status!='succeeded':
        settle(a,p);a.payment_id=p['id']
    a.status=transition_payment(a.status,incoming);managed(a)
    managed(frappe.get_doc({'doctype':'IL Webhook Event','event_key':digest,'attempt':a.name,
        'event_type':event['type'],'provider_id':p['id'],'received_at':now_datetime()}))
    return {'accepted':True,'settled':a.status=='succeeded'}

@frappe.whitelist()
def status(attempt):
    from .platform import organization
    a=frappe.get_doc('IL Payment Attempt',attempt,for_update=True);organization(a.tenant_id,administrator=True)
    return {k:a.get(k) for k in ('name','status','amount_minor','currency','tenant_id')}
