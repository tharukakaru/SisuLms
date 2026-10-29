"""Control-plane notices travel with signed policy; tenant dispatch honors preferences."""
import frappe
from .saas import managed
from .saas_rules import notification_key

def changed(doc,method=None):
    if not frappe.conf.get('il_control_plane'):return
    if doc.doctype=='IL Price Assignment':
        if doc.get('commercial_plan')!='PREMIUM AI' or not doc.active:return
        event='premium.offer';body='Your institute Premium AI monthly offer is available. Review Subscription for the current price.'
    elif doc.doctype=='IL Premium Receipt':event='premium.receipt';body='Verified Premium payment receipt is available in Subscription billing history.'
    elif doc.doctype=='IL Payment Attempt':
        if doc.status not in ('succeeded','failed','cancelled') or not doc.has_value_changed('status'):return
        event='payment.successful' if doc.status=='succeeded' else 'payment.failed'
        body='Organization payment '+doc.status+'. A failed renewal does not end the currently paid period.'
    else:return
    tenant=doc.get('tenant_id')
    if not tenant:return
    key=notification_key(doc.doctype+':'+doc.name+':'+str(doc.get('status')),event)
    if not frappe.db.exists('IL Subscription Notice',{'event_key':key}):
        managed(frappe.get_doc({'doctype':'IL Subscription Notice','event_key':key,'tenant_id':tenant,'event_type':event,'body':body,'acknowledged':0}))
    # Serialize against issuance. Do not clear newer pending updates after delivery.
    frappe.db.sql('SELECT name FROM `tabIL Organization` WHERE name=%s FOR UPDATE',(tenant,))
    name=frappe.db.get_value('IL Policy Delivery',{'organization':tenant},'name')
    if name:
        from frappe.utils import now_datetime
        d=frappe.get_doc('IL Policy Delivery',name,for_update=True);d.status='Pending';d.next_attempt=now_datetime();managed(d)

def apply(institute,notices):
    from .notification_service import emit,EVENTS
    if not isinstance(notices,list) or len(notices)>50:frappe.throw('Invalid signed notice batch')
    recipients=frappe.get_all('IL Member',filters={'institute':institute,'active':1,'role':'Admin'},pluck='name')
    for n in notices:
        if set(n)!={'name','event_key','event_type','body'} or n['event_type'] not in EVENTS:frappe.throw('Invalid signed notice')
        for member in recipients:emit(institute,member,n['event_type'],n['event_key'],n['body'])

def low_credit(doc,method=None):
    if doc.state!='Succeeded' or not doc.has_value_changed('state'):return
    from .ai_credits import allocation,user_used
    from .saas import state,resolved
    from .usage import used
    from .product_events import user_event
    sub=state(lock=True);cap=resolved(sub)['limits']['ai_credits']
    total=used('ai_credits',doc.period)
    if cap>0 and total>=cap*0.9:
        for row in frappe.get_all('IL Member',filters={'institute':doc.institute,'active':1,'role':'Admin'},fields=['user']):
            user_event(doc.institute,row.user,'ai.low','org:'+doc.period,'Your institute AI pool has 10% or less remaining.')
    if sub.ai_mode=='Individual':
        cap=allocation(doc.user,doc.period)
        if cap>0 and user_used(doc.user,doc.period)>=cap*0.9:user_event(doc.institute,doc.user,'ai.low','personal:'+doc.period,'Your allocated AI credits have 10% or less remaining.')

def expiry_reminders():
    if frappe.conf.get('il_control_plane') or not frappe.conf.get('il_tenant_id'):return
    from frappe.utils import now_datetime,get_datetime
    from .saas import state
    from .api import institute
    from .product_events import user_event
    d=state();inst=institute()
    if not d.ends_at:return
    days=(get_datetime(d.ends_at)-now_datetime()).total_seconds()/86400
    if days>7:return
    stage='expired' if days<=0 else 'renewal'
    text='Premium expired; Starter remains available.' if days<=0 else 'Premium renewal is due within seven days. Review Subscription.'
    for row in frappe.get_all('IL Member',filters={'institute':inst.name,'role':'Admin','active':1},fields=['user']):
        user_event(inst.name,row.user,'subscription.expiry',stage+':'+str(d.ends_at),text)
