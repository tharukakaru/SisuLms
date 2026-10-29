"""Account billing authority. Provider tuition and historical invoices are separate.

All mutations use authenticated POST endpoints, row locks and service-managed
DocTypes. Browser data cannot verify a country, settle an invoice or start a trial.
"""
import json
import html
from datetime import timedelta
import frappe
from frappe.utils import get_datetime, now_datetime
from .account_billing_rules import VERSION, PLANS, amount, next_anniversary, trial_end, access_state, payment_matches

ACCOUNT = 'IL Account Subscription'
INVOICE = 'IL Account Invoice'

def provider_lkr(a):
    return bool(frappe.conf.get('il_usage_billing_enabled')) and a.role in ('Teacher','Institute')
def price(a, plan):
    if provider_lkr(a):
        from .plan_catalog import plan as catalog_plan
        return catalog_plan(plan)['monthly_lkr'] * 100
    return amount(a.role, plan, a.billing_country) if a.billing_country else None
def currency_for(a): return 'LKR' if provider_lkr(a) else 'USD'

def save(doc):
    doc.flags.account_billing_service = True
    result=doc.save(ignore_permissions=True)
    if doc.doctype==ACCOUNT and doc.role!='Student': sync_provider(doc)
    return result

def sync_provider(a):
    """Maintain provider tuition/feature settings without issuing usage invoices."""
    from .commercial_rules import beneficiary
    from .commercial import save as provider_save
    key=beneficiary({'owner_type':a.role,'owner_user':a.user,'institute':a.institute})
    name=frappe.db.get_value('IL Provider Account',{'provider_key':key},'name')
    p=frappe.get_doc('IL Provider Account',name,for_update=True) if name else frappe.get_doc(dict(
        doctype='IL Provider Account',provider_key=key,institute=a.institute,owner_type=a.role,owner_user=a.user,
        cycle_start=a.trial_started,cycle_end=a.trial_until,enabled=1))
    p.plan=a.plan; p.next_plan=None; p.billing_email=a.billing_email or a.user
    # Old card mandates cannot collect any new subscription automatically.
    p.auto_pay=0
    provider_save(p)

def privileged():
    if frappe.session.user == 'Administrator': return True
    from .wallet import admin_actor
    return admin_actor()

def actor():
    from .api import identity
    inst, member = identity()
    if member.role not in ('Student', 'Teacher', 'Admin'):
        frappe.throw('This account does not have a subscription role', frappe.PermissionError)
    return inst, member

def seed(inst, member):
    role = 'Institute' if member.role == 'Admin' else member.role
    key = 'Institute:' + inst.name if role == 'Institute' else role + ':' + member.user
    # Never reset the trial at first login, role switch, deployment or reactivation.
    created = get_datetime(inst.creation if role == 'Institute' else frappe.db.get_value('User', member.user, 'creation'))
    user_created = get_datetime(frappe.db.get_value('User', member.user, 'creation'))
    created = min(created, user_created)
    plan='Student' if role=='Student' else 'Individual'
    if role!='Student':
        from .commercial_rules import beneficiary
        provider_key=beneficiary({'owner_type':role,'owner_user':member.user,'institute':inst.name})
        previous_plan=frappe.db.get_value('IL Provider Account',{'provider_key':provider_key},'plan')
        if previous_plan in PLANS:plan=previous_plan
    return dict(doctype=ACCOUNT, account_key=key, institute=inst.name, user=member.user if role != 'Institute' else None,
                role=role, display_name=inst.title if role == 'Institute' else member.full_name,
                billing_email=member.user, plan=plan, trial_started=created,
                trial_until=trial_end(created), country_status='Not submitted', enabled=1, version=VERSION)

def account(inst=None, member=None, create=False, lock=False):
    if inst is None: inst, member = actor()
    initial = seed(inst, member)
    if create or lock:
        # Serialize creation as well as updates. Institute billing is shared by its admins.
        dt, key = ('IL Institute', inst.name) if member.role == 'Admin' else ('User', member.user)
        frappe.db.sql('SELECT name FROM `tab' + dt + '` WHERE name=%s FOR UPDATE', (key,))
    name = frappe.db.get_value(ACCOUNT, {'account_key': initial['account_key']}, 'name')
    if name: return frappe.get_doc(ACCOUNT, name, for_update=lock)
    doc = frappe.get_doc(initial)
    return save(doc) if create else doc

def member_created(doc, method=None):
    if frappe.conf.get('il_control_plane') or doc.role not in ('Student', 'Teacher', 'Admin') or not doc.active: return
    inst = frappe.get_doc('IL Institute', doc.institute)
    account(inst, doc, create=True)

def state(a):
    if frappe.conf.get("il_usage_billing_enabled"):
        from .usage_billing import blocked, blocked_institute
        if (a.name and blocked(a.name)) or (a.institute and blocked_institute(a.institute)): return dict(state="Usage payment required", available=False)
    label, allowed = access_state(now_datetime(), get_datetime(a.trial_until),
        get_datetime(a.paid_until) if a.paid_until else None, not a.enabled)
    return dict(state=label, available=allowed)

def policy():
    a = account()
    from .plan_catalog import plan_features
    from .commercial_rules import plan_features as student_features
    f = plan_features(a.plan) if a.role != 'Student' else student_features('Gold')
    # Core learning and Study Room are included for every paying account.
    f.update(lms=True, study=True)
    f.update({'integrations.' + k: f['integrations'] for k in ('whatsapp','youtube', 'calendar')})
    f.update({'integrations.' + k: True for k in ('email','sms','push')})
    s = state(a)
    return dict(**s, plan=a.plan, features=f, limits={}, revision=1,
                ends_at=a.paid_until or a.trial_until, locked_reason='' if s['available'] else 'Your SISU subscription needs payment. Open Subscription to continue.')

def public_account(a):
    fields = ('name','role','display_name','plan','next_plan',
              'trial_started','trial_until','paid_until','anchor_day','payment_method','billing_email','cancel_at_end')
    result = {k:a.get(k) for k in fields}
    result.update(state(a))
    result['monthly_minor'] = price(a, a.plan)
    result['next_monthly_minor'] = price(a, a.next_plan) if a.next_plan else None
    result['billing_ready'] = bool(provider_lkr(a) or (a.billing_country and a.country_status in ('Verified','Change requested')))
    result['currency'] = currency_for(a)
    return result

def countries():
    # Frappe's country master is used to reject made-up country codes.
    return [{'code':str(c.code).upper(), 'name':c.name} for c in frappe.get_all('Country',fields=['name','code'],order_by='name',limit_page_length=0) if c.code]

def country_code(code):
    code = str(code).strip().upper()
    if code not in {c['code'] for c in countries()}: frappe.throw('Choose a country from the list')
    return code

@frappe.whitelist(methods=['POST'])
def status():
    a = account(create=True)
    # Customer responses contain only the applicable account prices.
    from .plan_catalog import plan as catalog_plan
    plans=[dict(plan=p,monthly_minor=price(a,p),**(catalog_plan(p) if provider_lkr(a) else {}))
           for p in (('Student',) if a.role=='Student' else PLANS)]
    return dict(account=public_account(a), plans=plans,gateway_ready=False,
                bank_instructions=str(frappe.conf.get('il_subscription_bank_instructions') or ''),
                gateway_message='Online payments and automatic card collection are not connected yet. No card will be charged.',
                invoices=frappe.get_all(INVOICE,filters={'subscription':a.name},fields=['name','plan','currency','amount_minor','period_start','period_end','status','paid_at','receipt_number','creation'],order_by='creation desc',limit_page_length=60))

@frappe.whitelist(methods=['POST'])
def preferences(plan, billing_email, payment_method='Card'):
    a=account(create=True,lock=True)
    if plan not in (('Student',) if a.role=='Student' else PLANS): frappe.throw('Invalid plan')
    if payment_method not in ('Card','Bank transfer'): frappe.throw('Choose a payment method')
    frappe.utils.validate_email_address(billing_email,throw=True)
    if a.paid_until and get_datetime(a.paid_until)>now_datetime():
        a.next_plan = plan if plan != a.plan else None
    else: a.plan=plan; a.next_plan=None
    a.billing_email=billing_email; a.payment_method=payment_method
    save(a)
    # Only unpaid offers are replaced. Settled financial history is immutable.
    void_open(a)
    return public_account(a)

@frappe.whitelist(methods=['POST'])
def request_country(country):
    a=account(create=True,lock=True)
    a.requested_country=country_code(country)
    # Keep an existing verified country until staff approves a change.
    a.country_status='Change requested' if a.billing_country else 'Pending review'
    save(a)
    return {'message':'Country submitted for verification. Changing this selection does not apply a discount.'}

def require_owner():
    from .registration import require_owner as check
    check()

@frappe.whitelist(methods=['POST'])
def admin_accounts():
    require_owner()
    return dict(accounts=frappe.get_all(ACCOUNT,fields=['name','display_name','role','plan','requested_country','billing_country','country_status','trial_until','paid_until'],order_by='modified desc',limit_page_length=200),
                invoices=frappe.get_all(INVOICE,filters={'status':'Unpaid'},fields=['name','subscription','amount_minor','currency','country','plan','period_start','period_end'],limit_page_length=200))

@frappe.whitelist(methods=['POST'])
def verify_country(subscription, country, reason):
    require_owner()
    if len(str(reason).strip())<10: frappe.throw('Record the evidence reviewed to verify billing country')
    a=frappe.get_doc(ACCOUNT,subscription,for_update=True)
    a.billing_country=country_code(country); a.country_status='Verified'; a.requested_country=None
    a.verified_by=frappe.session.user; a.verified_at=now_datetime(); a.verification_note=str(reason)[:1000]
    save(a); void_open(a)
    return public_account(a)

def void_open(a):
    for name in frappe.get_all(INVOICE,filters={'subscription':a.name,'status':'Unpaid'},pluck='name'):
        bill=frappe.get_doc(INVOICE,name,for_update=True)
        if bill.status!='Unpaid':continue
        bill.status='Void'; bill.open_key=None; save(bill)

def make_invoice(a):
    if frappe.conf.get('il_usage_billing_enabled') and a.role == 'Student':
        frappe.throw('SISU usage charges are paid by the provider; no student subscription invoice is created')
    if not provider_lkr(a) and (a.country_status not in ('Verified','Change requested') or not a.billing_country):
        frappe.throw('Your billing setup is being confirmed. Please contact SISU support before requesting an invoice.')
    if not a.enabled: frappe.throw('Subscription is suspended')
    if a.cancel_at_end: frappe.throw('Resume your subscription before creating an invoice')
    now=now_datetime()
    if now<get_datetime(a.trial_until) and not a.paid_until:
        frappe.throw('Your free trial is still active. Billing begins after it ends.')
    if a.paid_until and now<get_datetime(a.paid_until):
        frappe.throw('Your subscription is already paid. Your next invoice is created on the renewal date.')
    existing=frappe.db.get_value(INVOICE,{'subscription':a.name,'status':'Unpaid'},'name')
    if existing:
        bill=frappe.get_doc(INVOICE,existing,for_update=True)
        if now<get_datetime(bill.period_end): return bill
        bill.status='Void'; bill.open_key=None; save(bill)
    # A lapsed account resumes from a new checkout date; no fees for locked-out months.
    start=get_datetime(a.paid_until) if a.paid_until and now-get_datetime(a.paid_until)<timedelta(days=1) else now
    anchor=int(a.anchor_day or start.day) if a.paid_until and start==get_datetime(a.paid_until) else start.day
    plan=a.next_plan or a.plan
    return save(frappe.get_doc(dict(doctype=INVOICE,subscription=a.name,open_key=a.name,plan=plan,country=a.billing_country,
        currency=currency_for(a),amount_minor=price(a,plan),period_start=start,
        period_end=next_anniversary(start,anchor),anchor_day=anchor,status='Unpaid',version=VERSION,
        billed_to=a.display_name,billing_email=a.billing_email or a.user)))

@frappe.whitelist(methods=['POST'])
def invoice():
    a=account(create=True,lock=True)
    prior=frappe.db.get_value(INVOICE,{'subscription':a.name,'status':'Unpaid'},'name')
    bill=make_invoice(a)
    if bill.name!=prior:queue_document(bill,'Invoice')
    return {'invoice':bill.name,'amount_minor':bill.amount_minor,'currency':bill.currency,'checkout_available':False,
            'message':'Invoice created. Payment gateway is not connected; no charge has been made.'}

@frappe.whitelist(methods=['POST'])
def cancel(cancel=True):
    a=account(create=True,lock=True)
    a.cancel_at_end=1 if cancel in (True,1,'1','true') else 0
    save(a)
    if a.cancel_at_end: void_open(a)
    return public_account(a)

def record_verified_payment(invoice, reference, received_minor, currency, channel):
    """Internal only. Future adapter calls AFTER signature, merchant and settlement checks.

    No whitelisted browser callback can call this function. Reference must include
    gateway/merchant namespace so duplicate events cannot pay different invoices.
    """
    key=frappe.db.get_value(INVOICE,invoice,'subscription')
    if not key: frappe.throw('Invoice not found')
    a=frappe.get_doc(ACCOUNT,key,for_update=True)
    bill=frappe.get_doc(INVOICE,invoice,for_update=True)
    reference=str(reference).strip()
    if not reference or len(reference)>140 or not (type(received_minor) is int and received_minor == int(bill.amount_minor) and currency == bill.currency):
        frappe.throw('Settlement amount, currency or reference does not match')
    if bill.status=='Paid':
        if bill.payment_reference==reference:return bill
        frappe.throw('Invoice already paid with another reference')
    if bill.status!='Unpaid' or not a.enabled: frappe.throw('Invoice is not payable')
    if get_datetime(bill.period_end)<=now_datetime(): frappe.throw('Invoice expired; review the payment before refund or allocation')
    if frappe.db.exists(INVOICE,{'payment_reference':reference}): frappe.throw('Payment reference already used')
    if frappe.conf.get('il_usage_billing_enabled') and frappe.db.exists('IL Usage Invoice',{'payment_reference':reference}):
        frappe.throw('Payment reference already allocated to a usage invoice')
    bill.status='Paid';bill.open_key=None;bill.payment_reference=reference;bill.payment_channel=channel
    bill.paid_at=now_datetime();bill.receipt_number='SISU-R-'+bill.name;save(bill)
    a.paid_until=bill.period_end;a.anchor_day=bill.anchor_day;a.plan=bill.plan;a.next_plan=None
    save(a)
    queue_document(bill,'Receipt')
    return bill

@frappe.whitelist(methods=['POST'])
def confirm_bank_payment(invoice, reference, amount_minor, reason):
    require_owner()
    if len(str(reason).strip())<10:frappe.throw('Record the bank settlement evidence reviewed')
    try:
        cents=int(str(amount_minor))
    except (ValueError,TypeError):frappe.throw('Enter whole USD cents')
    bill=record_verified_payment(invoice,'bank:'+str(reference),cents,frappe.db.get_value(INVOICE,invoice,'currency'),'Verified bank transfer')
    bill.review_note=str(reason)[:1000];bill.reviewed_by=frappe.session.user;save(bill)
    return {'receipt':bill.receipt_number}

def document_html(bill):
    e=lambda value:html.escape(str(value or '—'))
    total=f'{e(bill.currency)} {int(bill.amount_minor)/100:,.2f}'
    heading='Payment receipt' if bill.status=='Paid' else 'Subscription invoice'
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>{e(heading)} · {e(bill.name)}</title>
    <style>body{{font:15px Arial;color:#28203b;margin:50px auto;max-width:850px;padding:30px}}header{{display:flex;justify-content:space-between;border-bottom:3px solid #56288d;padding-bottom:28px}}h1{{color:#56288d}}table{{width:100%;border-collapse:collapse;margin:35px 0}}td,th{{padding:18px 10px;text-align:left;border-bottom:1px solid #ddd}}.total{{text-align:right;font-size:25px}}small{{color:#655975}}@media print{{body{{margin:0;padding:25px}}}}</style></head><body>
    <header><div><h1>sisu.</h1><p>SISU Academy · Monthly subscription</p></div><div><h2>{e(heading)}</h2><p>{e(bill.name)}</p><b>{e(bill.status)}</b></div></header>
    <p>Bill to: <b>{e(bill.billed_to)}</b><br>{e(bill.billing_email)}</p>
    <p>Issued: {e(bill.creation)}<br>Subscription: {e(bill.subscription)}<br>Service period: {e(bill.period_start)} → {e(bill.period_end)} (end exclusive)</p>
    <table><tr><th>Description</th><th>Quantity</th><th>Amount</th></tr><tr><td>{e(bill.plan)} · fixed monthly subscription</td><td>1 month</td><td>{total}</td></tr></table>
    <p class="total">Total · {total}</p><p>Receipt: {e(bill.receipt_number)}<br>Payment date: {e(bill.paid_at)}<br>Payment method: {e(bill.payment_channel)}</p>
    <small>Class tuition is billed separately by the teacher or institute. Provider active-student usage, where applicable, is invoiced separately. An unpaid invoice is not proof of payment. This is a subscription billing document, not a tax invoice.</small></body></html>'''

def queue_document(bill,kind):
    if bill.billing_email:
        frappe.sendmail(recipients=[bill.billing_email],subject=f'SISU {kind} · {bill.name}',message=document_html(bill),delayed=True)

@frappe.whitelist(methods=['POST'])
def document(invoice):
    bill=frappe.get_doc(INVOICE,invoice)
    if not privileged() and bill.subscription!=account().name:frappe.throw('Invoice unavailable',frappe.PermissionError)
    return {'html':document_html(bill),'filename':bill.name+'.html'}

def daily():
    if frappe.conf.get('il_control_plane'):return
    for name in frappe.get_all(ACCOUNT,filters={'enabled':1,'cancel_at_end':0,'country_status':['in',['Verified','Change requested']]},pluck='name'):
        a=frappe.get_doc(ACCOUNT,name,for_update=True)
        if frappe.conf.get('il_usage_billing_enabled') and a.role == 'Student':continue
        if state(a)['available']:continue
        old=frappe.db.get_value(INVOICE,{'subscription':a.name,'status':'Unpaid'},'name')
        # Initial invoices are requested by the user; renew only an established paid account.
        if not a.paid_until:continue
        if old:continue  # Do not accumulate invoices while access is locked; user may request a fresh period.
        bill=make_invoice(a)
        if bill.name!=old:queue_document(bill,'Invoice')

def guard_request():
    """Subscription recovery is always reachable; protected APIs fail closed."""
    if frappe.conf.get('il_control_plane') or frappe.session.user=='Guest' or privileged():return
    path=frappe.local.request.path
    method=frappe.form_dict.get('cmd') or (path.split('/method/',1)[1].rstrip('/') if '/method/' in path else '')
    module=method.split('.')[1] if method.startswith('institute_lms.') else ''
    if module in ('usage_billing','account_billing','portal_session','portal_policy','registration','mobile_auth','mobile_verification','profiles','private_contact','contact','health','saas','devices'):
        return
    if method in ('login','logout','frappe.auth.get_logged_user') or method.startswith('frappe.integrations.oauth2_logins.') or 'reset_password' in method or 'update_password' in method:return
    if method.endswith('.notify') and module in ('payments_lk','payments','lectures'):return
    if method=='institute_lms.live_classes.webhook':return
    if not (module or method.startswith('lms.') or path.startswith(('/api/','/private/files/','/lms'))):return
    from .api import institute
    inst=institute()
    member=frappe.db.get_value('IL Member',{'institute':inst.name,'user':frappe.session.user,'active':1},'*',as_dict=True)
    if not member:return # Onboarding / scoped APIs retain their own permission checks.
    if not state(account(inst,member))['available']:
        frappe.throw('Your 14-day trial or paid subscription has ended. Open Subscription to continue.',frappe.PermissionError)
