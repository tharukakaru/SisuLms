"""Provider-owned collections, manual bank review and monthly SISU invoices.

All financial mutations execute in the enclosing Frappe POST transaction. This
module never sends a bank transfer and never treats a browser return as settlement.
"""
import hashlib
import json
from datetime import timedelta
import frappe
from .plan_catalog import plan_features
from frappe.utils import now_datetime, get_datetime, getdate
from .commercial_rules import PLANS, next_month, access_window, billing_units, invoice_totals, overdue, money_minor, beneficiary

def save(doc):
    doc.flags.commercial_service=True
    return doc.save(ignore_permissions=True)

def locked(doctype,name):
    frappe.db.sql('SELECT name FROM `tab'+doctype+'` WHERE name=%s FOR UPDATE',(name,))
    return frappe.get_doc(doctype,name)

def account_for(room,required=True):
    name=frappe.db.get_value('IL Provider Account',{'provider_key':beneficiary(room)},'name')
    if not name and required: frappe.throw('The platform owner must configure this providerÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢s package first')
    return frappe.get_doc('IL Provider Account',name) if name else None

def account_access(account):
    from .api import identity
    inst,m=identity()
    if account.institute!=inst.name or not (m.role=='Admin' and account.owner_type=='Institute' or m.role=='Teacher' and account.owner_type=='Teacher' and account.owner_user==m.user):
        frappe.throw('This provider account is not yours',frappe.PermissionError)
    return inst,m

def current_account():
    from .api import institute
    inst=institute()
    teacher=account_for({'owner_type':'Teacher','owner_user':frappe.session.user,'institute':inst.name},False)
    return teacher or account_for({'institute':inst.name},False)

def feature_policy():
    from .account_billing import policy
    return policy()


def locked_reason(account):
    if not account.enabled:return 'Provider account suspended'
    from .account_billing import ACCOUNT,state
    key='Institute:'+account.institute if account.owner_type=='Institute' else 'Teacher:'+account.owner_user
    name=frappe.db.get_value(ACCOUNT,{'account_key':key},'name')
    if not name:return 'Provider subscription needs setup'
    return '' if state(frappe.get_doc(ACCOUNT,name))['available'] else 'Provider subscription needs payment'


def require_room(room,feature='lms'):
    account=account_for(room,False)
    if not account:return  # Legacy sites require explicit commercial migration.
    reason=locked_reason(account)
    if reason:frappe.throw(reason,frappe.PermissionError)
    if not plan_features(account.plan).get(feature):frappe.throw('This feature requires a Gold or Platinum package',frappe.PermissionError)

def enforce_enrollment_limit(doc, method=None):
    # No per-student cap, but suspended providers cannot admit new students.
    if not doc.active:
        return
    room = frappe.get_doc('IL Classroom', doc.classroom)
    account = account_for(room, False)
    if account:
        reason = locked_reason(account)
        if reason:
            frappe.throw(reason, frappe.PermissionError)

def grant(invoice,room,start,end,channel):
    """No wallet credit: money is already paid directly to the provider."""
    account=account_for(room)
    if frappe.db.exists('IL Paid Access',{'invoice':invoice.name}):return
    enrollment=frappe.get_doc('IL Enrollment',invoice.enrollment)
    programme=enrollment.get('programme_enrollment')
    product='Programme:'+programme if programme else 'Class:'+room.name
    save(frappe.get_doc({'doctype':'IL Paid Access','grant_key':'invoice:'+invoice.name,'invoice':invoice.name,'institute':room.institute,
        'provider_account':account.name,'student':invoice.student,'classroom':room.name,'teacher':room.teacher,
        'product_key':product,'title':room.title,'starts_at':start,'ends_at':end,'status':'Active',
        'payment_channel':channel,'gross_minor':money_minor(invoice.amount)}))

def configured_access(room,start,ends_at=None):
    start=get_datetime(start)
    if room.get('programme'):
        programme=frappe.get_doc('IL Programme',room.get('programme'))
        days=programme.get('access_duration_days') or (int(programme.get('duration_months') or 1)*30)
    else:days=room.get('access_duration_days')
    if days:return start,start+timedelta(days=int(days))
    return access_window(room.get('paid_access_kind') or 'Month',start,ends_at or room.get('paid_access_end'))

@frappe.whitelist()
def pricing_context(classroom=None):
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')


def validate_pricing_ack(room,data):
    return  # Enrolments no longer create SISU usage fees.


def free_access(room,enrollment,student):
    account=account_for(room,False)
    if not account:return
    reason=locked_reason(account)
    if reason:frappe.throw(reason,frappe.PermissionError)
    programme=frappe.db.get_value('IL Enrollment',enrollment,'programme_enrollment')
    key='enrollment:'+enrollment
    if frappe.db.exists('IL Paid Access',{'grant_key':key}):return
    start,end=configured_access(room,now_datetime())
    save(frappe.get_doc({'doctype':'IL Paid Access','grant_key':key,'institute':room.institute,
        'provider_account':account.name,'student':student,'classroom':room.name,'teacher':room.teacher,
        'product_key':'Programme:'+programme if programme else 'Class:'+room.name,'title':room.title,'starts_at':start,'ends_at':end,'status':'Active',
        'payment_channel':'Free enrolment','gross_minor':0}))

def access_granted(room,member):
    now=now_datetime()
    invoice_rooms=[room.name]
    if room.get('programme'):
        invoice_rooms=frappe.get_all('IL Classroom',filters={'programme':room.programme,'institute':room.institute},pluck='name')
    return bool(frappe.db.exists('IL Paid Access',{'classroom':['in',invoice_rooms],'student':member.name,
        'status':'Active','starts_at':['<=',now],'ends_at':['>',now]}))

def notify_people(room,event,key,body,student=None):
    from .notification_service import emit
    recipients=set(frappe.get_all('IL Member',filters={'institute':room.institute,'role':'Admin','active':1},pluck='name')) if room.owner_type!='Teacher' else set()
    if room.teacher:recipients.add(room.teacher)
    if student:recipients.add(student)
    for recipient in sorted(recipients):emit(room.institute,recipient,event,key,body,classroom=room.name)

def owned_proof(name):
    file=frappe.get_doc('File',name)
    if not file.is_private or file.owner!=frappe.session.user or file.attached_to_name:
        frappe.throw('Upload a new private proof file from your own account',frappe.PermissionError)
    content=file.get_content()
    if isinstance(content,str):content=content.encode()
    if not 0<len(content)<=5*1024*1024:frappe.throw('Proof must be at most 5 MB')
    if not (content.startswith(b'%PDF-') or content.startswith(b'\x89PNG\r\n\x1a\n') or content.startswith(b'\xff\xd8\xff')):
        frappe.throw('Use a PDF, PNG or JPEG bank slip')
    return file,hashlib.sha256(content).hexdigest()

@frappe.whitelist(methods=['POST'])
def upload_proof():
    from .api import identity
    identity()
    file=frappe.request.files.get('file')
    if not file:frappe.throw('Choose a proof file')
    content=file.stream.read(5*1024*1024+1)
    if not content or len(content)>5*1024*1024:frappe.throw('Proof must be at most 5 MB')
    ext='pdf' if content.startswith(b'%PDF-') else 'png' if content.startswith(b'\x89PNG\r\n\x1a\n') else 'jpg' if content.startswith(b'\xff\xd8\xff') else None
    if not ext:frappe.throw('Use PDF, PNG or JPEG')
    from frappe.utils.file_manager import save_file
    f=save_file('bank-proof.'+ext,content,None,None,is_private=1)
    return {'name':f.name}

@frappe.whitelist(methods=['POST'])
def submit_slip(invoice,proof,reference,amount,transfer_date):
    from .api import identity,scoped
    inst,m=identity();doc=locked('IL Invoice',invoice)
    if doc.institute!=inst.name or m.role!='Student' or doc.student!=m.name:frappe.throw('Only the invoiced student can submit a slip',frappe.PermissionError)
    if doc.status=='Paid':frappe.throw('This invoice is already paid')
    if frappe.db.exists('IL Bank Slip',{'invoice':invoice,'status':'Pending'}):frappe.throw('Your slip is already awaiting review')
    room=scoped('IL Classroom',doc.classroom,inst);account=account_for(room)
    if doc.get('provider_account')!=account.name:frappe.throw('This invoice needs commercial migration before bank review')
    if money_minor(amount)!=money_minor(doc.amount):frappe.throw('The transferred amount must match this invoice')
    if not str(reference).strip() or len(str(reference))>140:frappe.throw('Add the bank transaction reference')
    if getdate(transfer_date)>getdate(now_datetime()):frappe.throw('Transfer date cannot be in the future')
    file,digest=owned_proof(proof)
    if frappe.db.exists('IL Bank Slip',{'proof_hash':digest}) or frappe.db.exists('IL Delivery Order',{'proof_hash':digest}):frappe.throw('This slip has already been submitted. Contact your teacher if it covers multiple invoices.')
    slip=save(frappe.get_doc({'doctype':'IL Bank Slip','invoice':invoice,'institute':inst.name,'student':m.name,'classroom':room.name,
        'provider_account':account.name,'proof_file':file.name,'proof_hash':digest,'reference':str(reference).strip(),
        'claimed_minor':money_minor(amount),'transfer_date':transfer_date,'status':'Pending'}))
    file.attached_to_doctype='IL Bank Slip';file.attached_to_name=slip.name;file.save(ignore_permissions=True)
    notify_people(room,'payment.slip','slip:'+slip.name,'A bank payment slip is awaiting review for '+room.title)
    return {'name':slip.name,'status':'Pending'}

def reviewer(slip):
    from .api import classroom_for
    inst,m,room=classroom_for(slip.classroom,True)
    if slip.institute!=inst.name or m.role not in ('Admin','Teacher'):frappe.throw('Class payment reviewer required',frappe.PermissionError)
    from .teaching import require
    require(room,m,'fees')
    account=account_for(room,False)
    if account and locked_reason(account):frappe.throw(locked_reason(account),frappe.PermissionError)
    return inst,m,room

@frappe.whitelist(methods=['POST'])
def review_slip(name,decision,note='',access_kind=None,starts_at=None,ends_at=None,rejection_reason=''):
    if decision not in ('Approved','Rejected'):frappe.throw('Choose approve or reject')
    from .payment_review_rules import review_note
    note=review_note(decision,note,rejection_reason)
    slip=locked('IL Bank Slip',name);inst,m,room=reviewer(slip)
    if slip.status!='Pending':frappe.throw('This slip has already been reviewed')
    if not str(note).strip():frappe.throw('Record the bank confirmation or rejection reason')
    doc=locked('IL Invoice',slip.invoice)
    if doc.status=='Paid':frappe.throw('Already paid through another payment method; reconcile the duplicate transfer')
    if decision=='Approved':
        start,end=configured_access(room,starts_at or now_datetime(),ends_at) if room.get('access_duration_days') or room.get('programme') else access_window(access_kind or room.get('paid_access_kind') or 'Month',starts_at or now_datetime(),ends_at or room.get('paid_access_end'))
        if end<=now_datetime():frappe.throw('Access must end in the future')
        # A stable provider/reference key prevents one transfer settling two invoices.
        payment_id='BANK-'+hashlib.sha256((slip.provider_account+':'+slip.reference.strip().casefold()).encode()).hexdigest()
        if frappe.db.exists('IL Invoice',{'payment_id':payment_id}) or frappe.db.exists('IL Delivery Order',{'payment_key':payment_id.removeprefix('BANK-')}):frappe.throw('This bank reference was already used')
        doc.update(dict(status='Paid',paid_at=now_datetime(),payment_id=payment_id,receipt_number='RC-'+doc.name,payment_channel='Bank transfer'))
        doc.save(ignore_permissions=True)
        grant(doc,room,start,end,'Bank transfer')
        slip.update(dict(access_kind=access_kind or room.get('paid_access_kind') or 'Month',starts_at=start,ends_at=end))
    slip.rejection_reason=rejection_reason if decision=='Rejected' else ''
    slip.update(dict(status=decision,reviewed_by=frappe.session.user,reviewed_at=now_datetime(),review_note=str(note)[:1000]));save(slip)
    notify_people(room,'payment.review','slip-review:'+slip.name,'Bank payment '+decision.lower()+' for '+room.title,slip.student)
    return {'status':slip.status}

@frappe.whitelist()
def slips(page=0):
    from .api import identity,room_filters
    inst,m=identity();filters={'institute':inst.name}
    if m.role=='Student':filters['student']=m.name
    else:
        names=frappe.get_all('IL Classroom',filters=room_filters(inst,m),pluck='name')
        filters['classroom']=['in',names or ['__none__']]
    rows=frappe.get_all('IL Bank Slip',filters=filters,fields=['name','invoice','student','classroom','reference','claimed_minor','transfer_date','status','review_note','rejection_reason','starts_at','ends_at','creation'],order_by='creation desc',limit_start=max(0,int(page))*50,limit_page_length=50)
    names=list({r.student for r in rows})
    members=frappe.get_all('IL Member',filters={'name':['in',names or ['__none__']],'institute':inst.name},fields=['name','full_name','user','phone'])
    contacts=frappe.get_all('IL Private Contact',filters={'user':['in',[x.user for x in members] or ['__none__']]},fields=['user','contact_phone'])
    phones={x.user:x.contact_phone for x in contacts}
    people={x.name:x for x in members}
    for row in rows:
        person=people.get(row.student)
        row.update(student_lms_id=row.student,student_name=person.full_name if person else row.student,contact_number=(phones.get(person.user) or person.phone) if person else '',submitted_at=row.creation)
    return rows

@frappe.whitelist()
def proof(name):
    from .api import identity
    slip=frappe.get_doc('IL Bank Slip',name);inst,m=identity()
    if m.role=='Student':
        if slip.student!=m.name or slip.institute!=inst.name:frappe.throw('Proof unavailable',frappe.PermissionError)
    else:reviewer(slip)
    f=frappe.get_doc('File',slip.proof_file)
    frappe.local.response.update(type='download',filename=f.file_name,filecontent=f.get_content(),display_content_as='attachment')

@frappe.whitelist()
def catalog():
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')

@frappe.whitelist(methods=['POST'])
def configure(owner_type,plan,billing_email,owner_user=None,bank_instructions='',reason=''):
    from .registration import require_owner
    require_owner()
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')

def my_accounts():
    from .api import identity
    inst,m=identity()
    if m.role=='Student':return []
    filters={'institute':inst.name,'owner_type':'Institute' if m.role=='Admin' else 'Teacher'}
    if m.role=='Teacher':filters['owner_user']=m.user
    return frappe.get_all('IL Provider Account',filters=filters,fields=['*'])

@frappe.whitelist()
def summary():
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')

def issue_cycle(account):
    frappe.throw('Usage billing has been retired. Use account subscriptions.')

def daily():
    return  # Retained for already-queued legacy jobs; never issue usage invoices.

@frappe.whitelist(methods=['POST'])
def submit_invoice_payment(name,reference,proof_file):
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')

@frappe.whitelist()
def owner_invoices():
    from .registration import require_owner
    require_owner()
    return {'accounts':frappe.get_all('IL Provider Account',fields=['name','provider_key','plan','next_plan','billing_email','cycle_end']),
        'invoices':frappe.get_all('IL Provider Invoice',fields=['*'],order_by='issued_at desc',limit_page_length=100),'plans':catalog()}

@frappe.whitelist(methods=['POST'])
def approve_invoice(name,reference,received_amount,note):
    from .registration import require_owner
    from .saas import audit
    require_owner();bill=locked('IL Provider Invoice',name)
    if bill.status=='Paid':return {'status':'Paid'}
    if bill.collection_status=='Pending':frappe.throw('Reconcile the pending card charge before approving a bank payment')
    if bill.status=='Void' or money_minor(received_amount)!=bill.total_minor:frappe.throw('Verify the exact invoice amount')
    if not reference.strip() or not note.strip():frappe.throw('Record the bank reference and verification note')
    if frappe.db.exists('IL Provider Invoice',{'status':'Paid','payment_reference':reference,'name':['!=',bill.name]}):frappe.throw('Bank reference already used')
    settlement_key=hashlib.sha256(reference.strip().casefold().encode()).hexdigest()
    bill.update(dict(status='Paid',settlement_key=settlement_key,payment_reference=reference[:140],reviewed_by=frappe.session.user,paid_at=now_datetime(),review_note=note[:1000],receipt_number='RC-'+bill.name,payment_channel='Bank transfer'));save(bill)
    from .provider_documents import queue_document
    queue_document(bill,'receipt')
    audit('Verify provider invoice payment',bill.name,note)
    return {'status':'Paid','locked_reason':locked_reason(frappe.get_doc('IL Provider Account',bill.provider_account))}

@frappe.whitelist()
def invoice_detail(name):
    from .wallet import admin_actor
    bill=frappe.get_doc('IL Provider Invoice',name)
    if not admin_actor():account_access(frappe.get_doc('IL Provider Account',bill.provider_account))
    result=bill.as_dict()
    a=frappe.get_doc('IL Provider Account',bill.provider_account)
    from .provider_cards import safe_account
    info=safe_account(a)
    for field in ('gateway_request','gateway_card_id','gateway_request_key'):result.pop(field,None)
    result.update(recipient=info['display_name'],recipient_id=info['lms_id'],billing_email=a.billing_email,bank_instructions=a.bank_instructions)
    return result

@frappe.whitelist()
def provider_proof_data(name):
    import base64
    bill=invoice_detail(name)
    if not bill.get('payment_proof'):frappe.throw('No payment proof has been submitted')
    f=frappe.get_doc('File',bill['payment_proof'])
    if f.attached_to_doctype!='IL Provider Invoice' or f.attached_to_name!=name or not f.is_private:
        frappe.throw('Proof unavailable',frappe.PermissionError)
    content=f.get_content()
    if len(content)>5*1024*1024:frappe.throw('Proof exceeds the supported size')
    return {'filename':f.file_name,'content':base64.b64encode(content).decode('ascii')}

@frappe.whitelist()
def provider_proof(name):
    bill=invoice_detail(name)
    if not bill.get('payment_proof'):frappe.throw('No payment proof has been submitted')
    f=frappe.get_doc('File',bill['payment_proof'])
    if f.attached_to_doctype!='IL Provider Invoice' or f.attached_to_name!=name or not f.is_private:
        frappe.throw('Proof unavailable',frappe.PermissionError)
    frappe.local.response.update(type='download',filename=f.file_name,filecontent=f.get_content(),display_content_as='attachment')

@frappe.whitelist()
def metrics(start_date=None,end_date=None):
    from .api import identity,room_filters
    inst,m=identity()
    if m.role not in ('Admin','Teacher'):frappe.throw('Provider access required',frappe.PermissionError)
    rooms=frappe.get_all('IL Classroom',filters=room_filters(inst,m),fields=['name','title','teacher','owner_type'])
    names=[r.name for r in rooms] or ['__none__']
    from .report_dates import report_window
    try:start,stop=report_window(start_date,end_date,now_datetime())
    except ValueError as exc:frappe.throw(str(exc))
    params={'names':tuple(names),'start':str(start),'stop':str(stop)}
    rows=frappe.db.sql('SELECT classroom,payment_channel,COUNT(*) payments,SUM(gross_minor) gross_minor,COUNT(DISTINCT student) students FROM `tabIL Paid Access` WHERE classroom IN %(names)s AND payment_channel!="Free enrolment" AND creation>=%(start)s AND creation<%(stop)s GROUP BY classroom,payment_channel',params,as_dict=True)
    hours=frappe.db.sql('SELECT classroom,SUM(GREATEST(0,TIMESTAMPDIFF(MINUTE,GREATEST(starts_at,%(month_start)s),ends_at)))/60 hours FROM `tabIL Session` WHERE classroom IN %(names)s AND ends_at<=%(now)s AND ends_at>%(month_start)s AND status!="Cancelled" GROUP BY classroom',{'names':tuple(names),'now':now_datetime(),'month_start':now_datetime().replace(day=1,hour=0,minute=0,second=0,microsecond=0)},as_dict=True)
    monthly=frappe.db.sql("SELECT DATE_FORMAT(creation,'%%Y-%%m') month,SUM(gross_minor) gross_minor FROM `tabIL Paid Access` WHERE classroom IN %(names)s AND payment_channel!='Free enrolment' AND creation>=%(start)s AND creation<%(stop)s GROUP BY month ORDER BY month",params,as_dict=True)
    return {'start_date':str(start),'end_date':str(stop-timedelta(days=1)),'classrooms':rooms,'collections':rows,'monthly_collections':monthly,'scheduled_completed_hours':hours,'hours_note':'Current calendar month: completed scheduled hours, not measured meeting attendance.'}

@frappe.whitelist(methods=['POST'])
def hnb_checkout(invoice):
    frappe.throw('HNB payments are not configured. Use bank transfer until the merchant integration has passed sandbox testing.')

def request_policy(method,module):
    return False  # Account billing and the feature policy are authoritative.


@frappe.whitelist(methods=['POST'])
def save_billing_preferences(account,payment_method,billing_email,auto_pay=False,consent=False):
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')

@frappe.whitelist(methods=['POST'])
def card_setup(account):
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')

@frappe.whitelist(methods=['POST'])
def remove_card(account):
    from .provider_cards import remove
    return remove(account)

@frappe.whitelist(methods=['POST'])
def card_checkout(name):
    frappe.throw('Usage billing is retired. Open Subscription for fixed monthly USD pricing.')
