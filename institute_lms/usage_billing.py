"""Provider usage automation. Opt-in after migration and tenant acceptance."""
import hashlib
import html
import json
from datetime import timedelta
import frappe
from frappe.utils import get_datetime, now_datetime
from .provider_usage_rules import usage_quote
DT='IL Usage Invoice'

def enabled(): return bool(frappe.conf.get('il_usage_billing_enabled'))
def save(doc):
    doc.flags.usage_service=True
    return doc.save(ignore_permissions=True)
def quote(account,bill):
    start=max(get_datetime(bill.period_start),get_datetime(bill.paid_at),get_datetime(account.trial_until))
    end=get_datetime(bill.period_end)
    if start>=end:return None
    filters={'institute':account.institute,'owner_type':account.role}
    if account.role=='Teacher':filters['owner_user']=account.user
    rooms=frappe.get_all('IL Classroom',filters=filters,pluck='name')
    rows=[]
    if rooms:
        rows=frappe.db.sql("""SELECT m.user AS student,s.starts_at AS present_at
            FROM `tabIL Attendance` a JOIN `tabIL Session` s ON s.name=a.session
            JOIN `tabIL Member` m ON m.name=a.student
            WHERE a.institute=%s AND s.institute=%s AND m.institute=%s
            AND a.classroom IN %s AND s.classroom=a.classroom AND a.status='Present'
            AND s.starts_at >= %s AND s.starts_at < %s""",
            (account.institute,account.institute,account.institute,tuple(rooms),start,min(end,now_datetime())),as_dict=True)
    attendance=[dict(student=x.student,present_at=get_datetime(x.present_at),present=True,provider=account.name) for x in rows]
    return usage_quote(account.name,bill.plan,start,end,get_datetime(account.trial_until),get_datetime(bill.paid_at),attendance)

def document_html(doc):
    e=lambda x:html.escape(str(x))
    return '<h1>SISU active-student '+('estimate' if doc.status=='Estimate' else 'invoice')+'</h1><p>'+e(doc.name)+'</p><p>Period: '+e(doc.period_start)+' to '+e(doc.period_end)+'</p><table><tr><th>Quantity</th><th>Unit rate LKR</th><th>Total LKR</th></tr><tr><td>'+e(doc.quantity)+'</td><td>'+e(doc.unit_rate)+'</td><td>'+e(doc.amount_lkr)+'</td></tr></table><p>Due: '+e(doc.due_at)+'</p><p>Payable by the provider. This document does not charge students. An estimate is not a final invoice.</p>'

def daily():
    if not enabled() or frappe.conf.get('il_control_plane'):return
    now=now_datetime()
    for key in frappe.get_all('IL Account Invoice',filters={'status':'Paid','currency':'LKR'},pluck='name'):
        bill=frappe.get_doc('IL Account Invoice',key)
        if get_datetime(bill.period_end)-timedelta(days=5)>now:continue
        a=frappe.get_doc('IL Account Subscription',bill.subscription,for_update=True)
        if a.role not in ('Teacher','Institute'):continue
        period_key=hashlib.sha256((a.name+':'+bill.name).encode()).hexdigest()
        name=frappe.db.get_value(DT,{'period_key':period_key},'name')
        doc=frappe.get_doc(DT,name,for_update=True) if name else None
        if doc and doc.issued_at:
            if doc.status!='Paid' and now>=get_datetime(doc.due_at) and not doc.suspended:
                doc.suspended=1;save(doc)
            continue
        q=quote(a,bill)
        if q is None:continue
        final=now>=q['period_end']
        if doc and not final:continue
        doc=doc or frappe.get_doc(dict(doctype=DT,subscription=a.name,source_invoice=bill.name,period_key=period_key))
        doc.update(dict(period_start=q['period_start'],period_end=q['period_end'],due_at=q['due_at'],plan=q['plan'],unit_rate=q['unit_rate'],quantity=q['quantity'],amount_lkr=q['amount'],student_snapshot=json.dumps(q['student_ids']),status=('Paid' if not q['amount'] else 'Unpaid') if final else 'Estimate'))
        if final:doc.issued_at=now;doc.suspended=int(bool(q['amount']) and now>=q['due_at'])
        else:doc.estimated_at=now
        save(doc)
        if a.billing_email:frappe.sendmail(recipients=[a.billing_email],subject='SISU usage '+doc.status+' '+doc.name,message=document_html(doc),delayed=True)

def blocked(subscription):
    if not enabled():return False
    now=now_datetime()
    return any(d.suspended or (d.status=='Unpaid' and now>=get_datetime(d.due_at)) for d in frappe.get_all(DT,filters={'subscription':subscription},fields=['suspended','status','due_at']))

def own_invoice(invoice):
    from .account_billing import account
    doc=frappe.get_doc(DT,invoice,for_update=True)
    if doc.subscription!=account().name:frappe.throw('Invoice unavailable',frappe.PermissionError)
    return doc

@frappe.whitelist(methods=['POST'])
def status():
    if not enabled():return dict(enabled=False,gateway_ready=False,invoices=[])
    from .account_billing import account
    a=account()
    return dict(enabled=enabled(),gateway_ready=False,blocked=blocked(a.name),invoices=frappe.get_all(DT,filters={'subscription':a.name},fields=['name','period_start','period_end','quantity','unit_rate','amount_lkr','status','due_at','suspended','activation_requested'],order_by='creation desc',limit_page_length=100))

@frappe.whitelist(methods=['POST'])
def document(invoice):return {'html':document_html(own_invoice(invoice))}

@frappe.whitelist(methods=['POST'])
def request_activation(invoice):
    doc=own_invoice(invoice)
    if not doc.issued_at:frappe.throw('An estimate is not payable')
    doc.activation_requested=1;save(doc)
    return {'requested':True,'payment_verified':doc.status=='Paid'}

@frappe.whitelist(methods=['POST'])
def admin_invoices():
    from .account_billing import require_owner
    require_owner()
    if not enabled():return []
    return frappe.get_all(DT,fields=['name','subscription','quantity','amount_lkr','status','due_at','suspended','activation_requested'],order_by='creation desc',limit_page_length=200)

@frappe.whitelist(methods=['POST'])
def verify_and_reactivate(invoice,reference,amount_lkr,reason):
    from .account_billing import require_owner
    require_owner()
    return settle_verified(invoice,reference,amount_lkr,reason)

def settle_verified(invoice,reference,amount_lkr,reason,remote_reviewer=None):
    # Internal only. Caller must authorize owner or verify a scoped signed command.
    if not enabled():frappe.throw('Usage billing is not enabled')
    doc=frappe.get_doc(DT,invoice,for_update=True)
    if not doc.issued_at:frappe.throw('Cannot settle an estimate')
    reference='bank:'+str(reference).strip()
    if len(reference)<=5 or len(reference)>140 or len(str(reason).strip())<10:frappe.throw('Bank reference and evidence review note required')
    if str(amount_lkr)!=str(doc.amount_lkr):frappe.throw('Exact invoice amount required')
    if frappe.db.exists('IL Account Invoice',{'payment_reference':reference}):frappe.throw('Reference already allocated to a subscription invoice')
    if doc.status=='Paid':
        if doc.payment_reference!=reference:frappe.throw('Already settled')
        return {'verified':True,'invoice_reactivated':not bool(doc.suspended),'already_applied':True}
    other=frappe.db.get_value(DT,{'payment_reference':reference},'name')
    if other and other!=doc.name:frappe.throw('Payment reference already allocated to another usage invoice')
    doc.status='Paid';doc.payment_reference=reference;doc.paid_at=doc.paid_at or now_datetime()
    doc.reviewed_by=None if remote_reviewer else frappe.session.user
    doc.remote_reviewed_by=remote_reviewer
    doc.review_note=str(reason)[:1000]
    doc.suspended=0;doc.activation_requested=0;doc.reactivated_at=now_datetime();save(doc)
    return {'verified':True,'invoice_reactivated':True}

def blocked_institute(institute):
    if not enabled():return False
    name=frappe.db.get_value('IL Account Subscription',{'institute':institute,'role':'Institute'},'name')
    return bool(name and blocked(name))
