"""SISU merchant card billing. Hosted card capture; verified settlement only.

Disabled until this site's SISU merchant completes sandbox acceptance. Never use
student tuition merchant keys. Unresolved attempts older than 23h require manual
reconciliation; they must not be reissued after the gateway idempotency window.
"""
import json
import re
import uuid
from datetime import timedelta
import frappe
from frappe.utils import get_url,now_datetime,get_datetime
from .payments_lk import provider_request
from .payments_lk_contract import hosted_url,verify_signature
from .provider_card_rules import valid_charge
from .commercial import locked,save,account_access

def ready():
    return False  # Legacy mandates cannot charge the replacement subscription system.


def config():
    if not ready():frappe.throw('SISU card billing awaits merchant setup and sandbox acceptance. Bank transfer remains available.')
    return (frappe.conf.il_provider_payments_lk_secret_key,frappe.conf.il_provider_payments_lk_webhook_secret,frappe.conf.get('il_provider_payments_lk_mode','test'))

def owned(account):
    a=locked('IL Provider Account',account);account_access(a);return a

def safe_account(a):
    result={k:a.get(k) for k in ('name','provider_key','owner_type','plan','next_plan','billing_email','cycle_start','cycle_end','bank_instructions','payment_method','auto_pay')}
    profile=frappe.db.get_value('IL Public Profile',{'user':a.owner_user,'kind':'Teacher'},['display_name','lms_id'],as_dict=True) if a.owner_type=='Teacher' else frappe.db.get_value('IL Public Profile',{'workspace':a.institute,'kind':'Institute'},['display_name','lms_id'],as_dict=True)
    result.update(display_name=profile.display_name if profile else a.provider_key,lms_id=profile.lms_id if profile else '')
    result['card']={'brand':a.card_brand,'last4':a.card_last4,'expiry':a.card_expiry} if a.gateway_card_id else None
    return result

def preferences(account,payment_method,billing_email,auto_pay=False,consent=False):
    a=owned(account)
    if payment_method not in ('Card','Bank transfer'):frappe.throw('Choose card or bank transfer')
    frappe.utils.validate_email_address(billing_email,throw=True)
    enabled=auto_pay in (True,1,'1') and payment_method=='Card'
    if enabled:
        _,_,mode=config()
        if not a.gateway_card_id or a.gateway_card_mode!=mode:frappe.throw('Add a card for the current payment environment first')
        if consent not in (True,1,'1'):frappe.throw('Accept the monthly billing authorisation')
        a.autopay_consent_at=now_datetime();a.autopay_consent_user=frappe.session.user
    else:a.autopay_consent_at=None;a.autopay_consent_user=None
    a.payment_method=payment_method;a.auto_pay=int(enabled);a.billing_email=billing_email;save(a)
    return {'saved':True}

def remove(account):
    a=owned(account);a.auto_pay=0;a.payment_method='Bank transfer';a.card_revoked_at=now_datetime();save(a);frappe.db.commit()
    if a.gateway_card_id:
        key,_,mode=config()
        if a.gateway_card_mode!=mode:frappe.throw('Switch to the card’s original merchant environment before removing it')
        provider_request('DELETE','/cards/'+a.gateway_card_id,key)
        a=locked('IL Provider Account',account)
        for field in ('gateway_card_id','gateway_card_mode','card_brand','card_last4','card_expiry','card_consent','autopay_consent_at','autopay_consent_user'):a.set(field,None)
        save(a)
    return {'saved':True}

def setup(account):
    a=owned(account)
    names=frappe.get_all('IL Provider Invoice',filters={'provider_account':a.name,'status':'Unpaid'},pluck='name',order_by='issued_at desc',limit_page_length=1)
    if not names:frappe.throw('You can securely add or replace your card when paying your next open invoice. No extra setup charge is made.')
    return checkout(names[0])

def checkout(name):
    account=frappe.db.get_value('IL Provider Invoice',name,'provider_account')
    a=owned(account);bill=locked('IL Provider Invoice',name);key,_,mode=config()
    if bill.status!='Unpaid':frappe.throw('Only an unpaid invoice can start card checkout')
    if bill.collection_status=='Failed':frappe.throw('The previous attempt needs reconciliation; use bank transfer or contact SISU before retrying')
    if bill.gateway_card_id:frappe.throw('An automatic payment exists. Reconcile it before starting a new checkout.')
    if not bill.gateway_request:
        payload={'amountCents':bill.total_minor,'description':'SISU '+bill.plan+' monthly invoice','reference':bill.name,
            'customer':{'name':safe_account(a)['display_name'],'email':a.billing_email},'saveCard':True,
            'successUrl':get_url('/campus#subscription'),'cancelUrl':get_url('/campus#subscription'),'locale':'en'}
        bill.update(dict(gateway_request=json.dumps(payload,separators=(',',':')),gateway_request_key='sisu-provider-'+uuid.uuid4().hex,gateway_requested_at=now_datetime(),gateway_mode=mode,collection_status='Pending'));save(bill)
    if bill.gateway_mode!=mode:frappe.throw('Reconcile the payment before changing merchant mode')
    frappe.db.commit()
    if bill.gateway_checkout_id:result=provider_request('GET','/checkouts/'+bill.gateway_checkout_id,key)
    else:
        if get_datetime(bill.gateway_requested_at)<now_datetime()-timedelta(hours=23):frappe.throw('Payment needs reconciliation before retrying')
        result=provider_request('POST','/checkouts',key,bill.gateway_request,bill.gateway_request_key)
    payment=result.get('payment') or {}
    if not (result.get('mode')==mode and re.fullmatch(r'chk_[A-Za-z0-9]{24}',str(result.get('id',''))) and hosted_url(result.get('url')) and payment.get('reference')==bill.name and payment.get('amountCents')==bill.total_minor and payment.get('currency')=='LKR'):frappe.throw('Checkout could not be verified. Reconcile the saved attempt.')
    a=locked('IL Provider Account',account);bill=locked('IL Provider Invoice',name)
    if bill.gateway_checkout_id and bill.gateway_checkout_id!=result['id']:frappe.throw('Checkout identity changed')
    bill.gateway_checkout_id=result['id'];save(bill)
    if result.get('status')!='open':frappe.db.commit();frappe.throw('Checkout is no longer open; refresh payment status before retrying')
    return {'redirect_url':result['url']}

def collect(name):
    """Scheduler only. One immutable attempt per invoice, even on timeout."""
    key,_,mode=config();account=frappe.db.get_value('IL Provider Invoice',name,'provider_account')
    a=locked('IL Provider Account',account);bill=locked('IL Provider Invoice',name)
    if not a.enabled or bill.status!='Unpaid' or not a.auto_pay or a.payment_method!='Card' or not a.gateway_card_id or not a.autopay_consent_at:return
    if a.gateway_card_mode!=mode:return
    if not bill.gateway_request and get_datetime(bill.issued_at)<get_datetime(a.autopay_consent_at):return
    if bill.collection_status in ('Succeeded','Failed') or bill.gateway_checkout_id:return
    if bill.gateway_request and not bill.gateway_card_id:return
    if not bill.gateway_request:
        bill.update(dict(gateway_request=json.dumps({'amountCents':bill.total_minor,'description':'SISU '+bill.plan+' monthly invoice','reference':bill.name},separators=(',',':')),gateway_request_key='sisu-auto-'+uuid.uuid4().hex,gateway_requested_at=now_datetime(),gateway_mode=mode,gateway_card_id=a.gateway_card_id,collection_status='Pending'));save(bill)
    if bill.gateway_mode!=mode:return
    frappe.db.commit()
    if bill.gateway_payment_id:p=provider_request('GET','/payments/'+bill.gateway_payment_id,key)
    else:
        if get_datetime(bill.gateway_requested_at)<now_datetime()-timedelta(hours=23):return
        p=provider_request('POST','/cards/'+bill.gateway_card_id+'/charge',key,bill.gateway_request,bill.gateway_request_key)
    a=locked('IL Provider Account',account);bill=locked('IL Provider Invoice',name)
    if not valid_charge(p,bill.as_dict(),mode):frappe.throw('Payment response did not match the invoice')
    if bill.gateway_payment_id and bill.gateway_payment_id!=p['id']:frappe.throw('Payment identity changed')
    bill.gateway_payment_id=p['id'];save(bill)
    apply_payment(bill,p)

def apply_payment(bill,p):
    if bill.status=='Paid':
        if bill.gateway_payment_id!=p['id']:frappe.throw('Invoice already settled with a different payment')
        return
    if bill.status!='Unpaid':frappe.throw('Payment requires reconciliation with existing invoice state')
    bill.gateway_payment_id=p['id']
    if p.get('status')=='succeeded':
        bill.update(dict(status='Paid',paid_at=now_datetime(),payment_reference=p['id'],settlement_key='card:'+p['id'],payment_channel='Card',receipt_number='RC-'+bill.name,collection_status='Succeeded',collection_error=''));save(bill)
        from .provider_documents import queue_document
        queue_document(bill,'receipt')
    elif p.get('status') in ('failed','cancelled'):
        bill.collection_status='Failed';bill.collection_error='Card payment was not completed. Use bank transfer or contact SISU to reconcile the card attempt.';save(bill)
    else:bill.collection_status='Pending';save(bill)

@frappe.whitelist(allow_guest=True,methods=['POST'])
def notify(**kwargs):
    key,secret,mode=config();raw=frappe.request.get_data(cache=True)
    if len(raw)>65536 or not verify_signature(raw,frappe.request.headers.get('Payments-Signature'),secret):frappe.throw('Invalid payment signature',frappe.PermissionError)
    event=json.loads(raw);p=event.get('data')
    if event.get('mode')!=mode or not isinstance(p,dict):frappe.throw('Invalid payment event')
    if event.get('type')=='card.saved':
        if not re.fullmatch(r'pay_[A-Za-z0-9]{24}',str(p.get('paymentId',''))):frappe.throw('Card has no payment binding')
        payment=provider_request('GET','/payments/'+p['paymentId'],key)
        name=payment.get('reference');account=frappe.db.get_value('IL Provider Invoice',name,'provider_account')
        if not account:return {'accepted':True,'matched':False}
        a=locked('IL Provider Account',account);bill=locked('IL Provider Invoice',name)
        if not valid_charge(payment,bill.as_dict(),mode) or payment.get('status')!='succeeded' or not json.loads(bill.gateway_request or '{}').get('saveCard'):frappe.throw('Card payment binding mismatch')
        request=json.loads(bill.gateway_request)
        if not (p.get('mode')==mode and p.get('active') is True and p.get('customerEmail')==request.get('customer',{}).get('email') and p.get('consent',{}).get('agreedAt') and re.fullmatch(r'card_[A-Za-z0-9]{24}',str(p.get('id',''))) and re.fullmatch(r'\d{4}',str(p.get('last4','')))):frappe.throw('Card details failed verification')
        expiry=p.get('expiry') or {}
        if a.card_revoked_at and get_datetime(p['consent']['agreedAt']).replace(tzinfo=None)<=get_datetime(a.card_revoked_at):return {'accepted':True}
        if (not a.card_consent or str(json.loads(a.card_consent).get('agreedAt',''))<str(p['consent']['agreedAt'])) and (not a.gateway_card_id or a.gateway_card_id!=p['id']):
            a.update(dict(gateway_card_id=p['id'],gateway_card_mode=mode,card_brand=str(p.get('scheme') or 'Card')[:25],card_last4=p['last4'],card_expiry=str(expiry.get('month',''))+'/'+str(expiry.get('year','')),card_consent=json.dumps(p['consent']),auto_pay=0,payment_method='Card'));save(a)
        apply_payment(bill,payment);return {'accepted':True}
    if event.get('type') not in ('payment.succeeded','payment.failed','payment.cancelled'):return {'accepted':True}
    name=p.get('reference');account=frappe.db.get_value('IL Provider Invoice',name,'provider_account')
    if not account:return {'accepted':True,'matched':False}
    a=locked('IL Provider Account',account);bill=locked('IL Provider Invoice',name)
    if not valid_charge(p,bill.as_dict(),mode) or event['type']!='payment.'+p.get('status','') or bill.gateway_mode!=mode:frappe.throw('Payment binding mismatch')
    if bill.gateway_payment_id and bill.gateway_payment_id!=p['id']:frappe.throw('Payment identity changed')
    apply_payment(bill,p);return {'accepted':True,'settled':bill.status=='Paid'}

def daily():
    if not ready():return
    for name in frappe.get_all('IL Provider Invoice',filters={'status':'Unpaid'},pluck='name'):
        try:collect(name);frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            # No secret, full gateway response, or customer payment data in logs.
            frappe.log_error(title='Provider card collection needs review',message='Invoice '+name+' requires reconciliation; no replacement attempt was created.')
