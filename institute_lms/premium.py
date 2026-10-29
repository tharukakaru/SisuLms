"""Organization Premium offers and receipt views. No frontend activation endpoint."""
import json
import frappe
from frappe.utils import now_datetime, get_datetime
from .saas import managed, audit

def offer_for(tenant):
    rows=frappe.get_all('IL Price Assignment',filters={'tenant_id':tenant,'product':'Platform',
        'commercial_plan':'PREMIUM AI','active':1},fields=['name','base_minor','currency','period','version','effective_at'],limit_page_length=2)
    if len(rows)!=1:return {'available':False,'message':'Premium AI pricing has not yet been configured for your institute.'}
    row=rows[0]
    if row.period!='Monthly' or row.currency!='LKR' or row.base_minor<=0 or row.effective_at and get_datetime(row.effective_at)>now_datetime():
        return {'available':False,'message':'Premium offer is not currently available.'}
    return {'available':True,'assignment':row.name,'amount_minor':row.base_minor,'currency':row.currency,
            'period':'Monthly','version':row.version,'effective_at':row.effective_at}

@frappe.whitelist(methods=['POST'])
def configure_offer(tenant,amount_minor,reason,enabled=True):
    from .platform import owner,organization
    from .pricing_rules import integer
    from .owner_pricing import save
    owner();org=organization(tenant)
    amount=integer(amount_minor,'Monthly price')
    if type(enabled) is not bool or amount<=0 or not 3<=len(str(reason).strip())<=500:frappe.throw('Positive monthly price and audit reason required')
    frappe.db.sql('SELECT name FROM `tabIL Organization` WHERE name=%s FOR UPDATE',(tenant,))
    rows=frappe.get_all('IL Price Assignment',filters={'tenant_id':tenant,'product':'Platform','commercial_plan':'PREMIUM AI'},fields=['name','version','active'])
    for row in rows:
        if row.active:
            d=frappe.get_doc('IL Price Assignment',row.name);d.active=0;save(d)
    d=save(frappe.get_doc({'doctype':'IL Price Assignment','customer':org.admin_contact,'customer_kind':'Institute',
        'tenant_id':tenant,'product':'Platform','commercial_plan':'PREMIUM AI','currency':'LKR','period':'Monthly',
        'base_minor':amount,'included_units':0,'unit_minor':0,'discount_bps':0,'tax_bps':0,'active':int(enabled),
        'version':max([int(r.version or 0) for r in rows]+[0])+1,'effective_at':now_datetime(),
        'reason':reason,'assigned_by':frappe.session.user}))
    audit('Premium monthly offer',tenant,reason+'; version '+str(d.version))
    return offer_for(tenant)

@frappe.whitelist()
def summary(tenant):
    from .platform import organization
    org=organization(tenant,administrator=True)
    from .full_rules import final_policy
    sub=frappe.get_doc('IL Subscription',frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name'))
    value=sub.as_dict()
    from datetime import timedelta
    value['lease_until']=now_datetime()+timedelta(hours=24)
    value['enabled']=bool(org.enabled and sub.enabled)
    policy=final_policy(value)
    return {'organization':org.title,'tenant_id':tenant,'subscription':policy,'offer':offer_for(tenant),
        'payments':frappe.get_all('IL Payment Attempt',filters={'tenant_id':tenant},fields=['name','status','amount_minor','currency','creation'],order_by='creation desc',limit_page_length=50),
        'receipts':frappe.get_all('IL Premium Receipt',filters={'tenant_id':tenant},fields=['name','plan','amount_minor','currency','period_start','period_end','paid_at'],order_by='creation desc',limit_page_length=50),
        'policy_delivery':frappe.db.get_value('IL Policy Delivery',{'organization':tenant},['status','revision','acknowledged_at'],as_dict=True)}

@frappe.whitelist()
def receipt(name):
    from .platform import organization
    d=frappe.get_doc('IL Premium Receipt',name);organization(d.tenant_id,administrator=True)
    return {k:d.get(k) for k in ('name','tenant_id','plan','amount_minor','currency','period_start','period_end','paid_at','transaction_reference')}

@frappe.whitelist(methods=['POST'])
def request_pricing(tenant):
    from .platform import organization
    organization(tenant,administrator=True)
    from .registration import limit
    limit('premium-price-request:'+tenant)
    audit('Premium price requested',tenant,'Organization billing contact requested an offer')
    return {'requested':True,'message':'Pricing request recorded for the platform owner.'}

def settled_receipt(attempt, start, end, payment):
    if frappe.db.exists('IL Premium Receipt',{'attempt':attempt.name}):return
    managed(frappe.get_doc({'doctype':'IL Premium Receipt','attempt':attempt.name,'tenant_id':attempt.tenant_id,
        'plan':json.loads(attempt.snapshot)['plan'],'amount_minor':attempt.amount_minor,'currency':attempt.currency,
        'period_start':start,'period_end':end,'paid_at':now_datetime(),'transaction_reference':payment['id']}))
