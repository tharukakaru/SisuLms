"""Full refunds: provider confirmation precedes ledger reversal and access revocation.

The deployment adapter must implement request/refetch with a stable idempotency key.
No client or operator can declare a provider payment refunded.
"""
import hashlib
import frappe
from frappe.utils import now_datetime
from .saas import managed, audit

def confirmed(value, refund):
    return (isinstance(value,dict) and value.get('verified') is True
            and value.get('status')=='succeeded' and value.get('payment_id')==refund.payment_id
            and type(value.get('amount_minor')) is int and value['amount_minor']==refund.amount_minor
            and value.get('currency')==refund.currency and value.get('request_key')==refund.request_key
            and isinstance(value.get('reference'),str) and 1<=len(value['reference'])<=140)

def authorized(order):
    from .api import identity,require_role
    inst,member=identity();require_role(member,'Admin')
    d=frappe.get_doc('IL Lecture Order',order)
    if d.institute!=inst.name:frappe.throw('Order unavailable',frappe.PermissionError)
    return d

@frappe.whitelist(methods=['POST'])
def request(order,reason):
    d=authorized(order)
    if not isinstance(reason,str) or not 10<=len(reason.strip())<=500:frappe.throw('Provide a refund audit reason')
    with frappe.cache.lock('il_lesson_refund:'+d.name,timeout=90,blocking_timeout=1):
        d=frappe.get_doc('IL Lecture Order',order,for_update=True)
        prior=frappe.db.get_value('IL Lecture Refund',{'order_id':order},'name')
        if prior:r=frappe.get_doc('IL Lecture Refund',prior)
        else:
            if d.status!='succeeded':frappe.throw('Only verified paid orders may be refunded')
            r=managed(frappe.get_doc({'doctype':'IL Lecture Refund','order_id':order,
                'request_key':hashlib.sha256(('refund:'+order).encode()).hexdigest(),
                'payment_id':d.payment_id,'amount_minor':d.amount_minor,'currency':d.currency,
                'status':'Pending','reason':reason,'requested_by':frappe.session.user}))
            audit('Lecture refund requested',order,reason)
        if r.status=='Succeeded':return {'name':r.name,'status':r.status}
        adapter=frappe.conf.get('il_lecture_refund_adapter')
        if not adapter:frappe.throw('Refund provider is not configured; no refund has been issued')
        frappe.db.commit() # durable key before any provider call
        try:
            value=frappe.get_attr(adapter)(payment_id=r.payment_id,amount_minor=r.amount_minor,
                currency=r.currency,request_key=r.request_key)
        except Exception:
            r.status='Review';managed(r);frappe.db.commit()
            frappe.throw('Refund outcome unknown. Retry the same order to reconcile; do not issue a separate refund.')
        if not confirmed(value,r):
            r.status='Review';managed(r)
            return {'name':r.name,'status':'Review','message':'Await verified provider refund confirmation'}
        settle(r.name,value)
        return {'name':r.name,'status':'Succeeded'}

def settle(name,value):
    r=frappe.get_doc('IL Lecture Refund',name,for_update=True)
    if not confirmed(value,r):frappe.throw('Refund confirmation mismatch',frappe.PermissionError)
    if r.status=='Succeeded':return
    order=frappe.get_doc('IL Lecture Order',r.order_id,for_update=True)
    if order.status!='succeeded' or order.payment_id!=r.payment_id:frappe.throw('Refund order requires reconciliation')
    from .wallet import locked_wallet,post
    w=locked_wallet(order.wallet)
    # Negative available balance is intentional when earnings have already been paid out.
    post(w,'lecture-refund:'+order.name,'Reversal',-int(r.amount_minor),0,reference=order.name,reason=r.reason)
    for name in frappe.get_all('IL Lecture Access',filters={'order':order.name,'revoked':0},pluck='name'):
        a=frappe.get_doc('IL Lecture Access',name,for_update=True);a.revoked=1;managed(a)
    order.status='refunded';managed(order)
    r.status='Succeeded';r.provider_reference=value['reference'];r.verified_at=now_datetime();managed(r)
    audit('Verified lecture refund',order.name,r.name)
    from .product_events import user_event
    user_event(order.institute,order.user,'lesson.refunded',r.name,'Your lesson refund is confirmed. Purchase access has been revoked.')

@frappe.whitelist()
def listing():
    from .api import identity,require_role
    inst,m=identity();require_role(m,'Admin')
    return frappe.get_all('IL Lecture Order',filters={'institute':inst.name,'status':['in',['succeeded','refunded']]},
        fields=['name','product','amount_minor','currency','status','receipt_number','paid_at'],limit_page_length=100,order_by='modified desc')
