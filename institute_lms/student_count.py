"""Student-count fees owed to SISU by institutes and personal teaching providers.

This is separate from student tuition and the retired plan-based usage tariff.
Only completed calendar months can be billed; issued counts/rates are immutable.
"""
import hashlib
import json
from pathlib import Path
from collections import defaultdict
import frappe
from frappe.utils import now_datetime, get_datetime
from .student_count_rules import month_bounds, qualified_students, price_for, rate_minor

SETTINGS = 'IL Student Count Policy'
BILL = 'IL Student Count Bill'


def save(doc):
    doc.flags.student_count_service = True
    if doc.name and not frappe.db.exists(doc.doctype, doc.name):
        return doc.insert(ignore_permissions=True)
    return doc.save(ignore_permissions=True)


def policy():
    from .plan_catalog_source import source_site
    source = source_site()
    if source and source != frappe.local.site:
        from .owner_operations import connect
        import re
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.-]+', source) or '..' in source:
            raise ValueError('Invalid policy source')
        connection = connect(source)
        try:
            with connection.cursor() as c:
                c.execute('START TRANSACTION READ ONLY')
                c.execute('SELECT payload,revision FROM `tabIL Student Count Policy` WHERE name=%s', ('current',))
                row = c.fetchone()
        finally:
            connection.close()
    else:
        row = frappe.db.get_value(SETTINGS, 'current', ['payload','revision'], as_dict=True)
    return dict(**json.loads(row['payload']), revision=row['revision']) if row else dict(rates=[],bank={},revision=0)


def payer():
    from .api import identity, require_role
    from .account_billing import account
    inst, member = identity()
    require_role(member, 'Admin', 'Teacher')
    if member.role == 'Teacher':
        # Billing remains accessible after the personal subscription expires.
        # Workspace ownership, not subscription availability, determines the payer.
        if frappe.db.exists('IL Public Profile', {'workspace': inst.name, 'kind': 'Institute'}):
            frappe.throw('Your institute manages student-count payments.', frappe.PermissionError)
    return inst, member, account(inst, member, create=True)


def provider_rooms(account):
    filters = dict(institute=account.institute, owner_type=account.role)
    if account.role == 'Teacher':
        filters['owner_user'] = account.user
    # Historical attendance still counts if a classroom has since been archived.
    return frappe.get_all('IL Classroom', filters=filters, pluck='name')


def attendance_for(institute, rooms, month):
    start, end = month_bounds(month)
    if not rooms:
        return []
    return frappe.db.sql('''SELECT m.user AS student,m.name AS member,m.full_name,
        a.session,a.classroom,a.status,s.title AS session_title,s.starts_at
        FROM `tabIL Attendance` a JOIN `tabIL Session` s ON s.name=a.session AND s.classroom=a.classroom
        JOIN `tabIL Member` m ON m.name=a.student AND m.institute=a.institute AND m.role='Student'
        WHERE a.institute=%s AND s.institute=%s AND a.classroom IN %s
        AND a.status='Present' AND s.status!='Cancelled' AND s.starts_at>=%s AND s.starts_at<%s
        AND s.starts_at<=%s''', (institute,institute,tuple(rooms),start,end,now_datetime()), as_dict=True)


def calculate(account, month, config=None):
    config = config or policy()
    rate = price_for(config, month)
    rows = attendance_for(account.institute, provider_rooms(account), month)
    qualified = qualified_students(rows)
    return dict(month=month,quantity=len(qualified),unit_minor=rate['unit_minor'] if rate else 500,
                amount_minor=len(qualified)*(rate['unit_minor'] if rate else 500),
                enabled=bool(rate and rate['enabled']),students=qualified)


def finalize(account, month, config=None):
    start, end = month_bounds(month)
    if end > now_datetime():
        frappe.throw('The month must finish before a student-count bill is issued.')
    # Serializes the monthly snapshot and prevents duplicate charges.
    frappe.db.sql('SELECT name FROM `tabIL Account Subscription` WHERE name=%s FOR UPDATE', (account.name,))
    key = hashlib.sha256((account.name+':'+month).encode()).hexdigest()
    old = frappe.db.get_value(BILL, {'period_key':key}, 'name')
    if old:
        return old
    result = calculate(account, month, config)
    if not result['enabled'] or not result['quantity'] or not result['amount_minor']:
        return None
    doc = frappe.get_doc(dict(doctype=BILL,period_key=key,subscription=account.name,institute=account.institute,
        provider_name=account.display_name,provider_role=account.role,month=month,
        quantity=result['quantity'],unit_minor=result['unit_minor'],amount_minor=result['amount_minor'],
        student_snapshot=json.dumps(result['students'],sort_keys=True),status='Unpaid'))
    return save(doc).name


def daily():
    if frappe.conf.get('il_control_plane'):
        return
    config = policy()
    active = [r['month'] for r in config['rates'] if r['enabled']]
    if not active:
        return
    current = now_datetime().strftime('%Y-%m')
    for name in frappe.get_all('IL Account Subscription', filters={'role':['in',['Teacher','Institute']]},pluck='name'):
        account = frappe.get_doc('IL Account Subscription', name)
        month = max(min(active), get_datetime(account.creation).strftime('%Y-%m'))
        while month < current:
            finalize(account, month, config)
            month = month_bounds(month)[1].strftime('%Y-%m')
        frappe.db.commit()


@frappe.whitelist(methods=['GET'])
def summary(month=None):
    inst, member, account = payer()
    month = month or now_datetime().strftime('%Y-%m')
    try:
        month_bounds(month)
    except ValueError as exc:
        frappe.throw(str(exc))
    config = policy()
    result = calculate(account,month,config)
    result.pop('students')
    result.update(bank=config['bank'],provider=account.display_name,invoices=frappe.get_all(BILL,
        filters={'subscription':account.name},fields=['name','month','quantity','unit_minor','amount_minor','status','reference','review_note','paid_at'],order_by='month desc',limit_page_length=100))
    result['final']=month_bounds(month)[1]<=now_datetime()
    return result


@frappe.whitelist(methods=['POST'])
def issue(month):
    _, _, account = payer()
    return {'name':finalize(account,month)}


@frappe.whitelist(methods=['POST'])
def submit(invoice,proof,reference):
    _, _, account = payer()
    doc = frappe.get_doc(BILL,invoice,for_update=True)
    if doc.subscription != account.name:
        frappe.throw('Payment unavailable.',frappe.PermissionError)
    if doc.status not in ('Unpaid','Rejected'):
        frappe.throw('This payment is already pending review or paid.')
    bank=policy()['bank']
    if not all(bank.get(k) for k in ('bank_name','account_name','account_number','branch')):
        frappe.throw('SISU has not configured the receiving bank details yet.')
    reference=str(reference).strip()
    if not 3<=len(reference)<=140:
        frappe.throw('Enter the transfer reference (3–140 characters).')
    from .commercial import owned_proof
    file,digest=owned_proof(proof)
    if frappe.db.exists(BILL,{'proof_hash':digest}):
        frappe.throw('This receipt has already been submitted.')
    doc.update(dict(proof_file=file.name,proof_hash=digest,reference=reference,status='Pending',submitted_at=now_datetime(),review_note=''))
    save(doc)
    file.attached_to_doctype=BILL;file.attached_to_name=doc.name;file.save(ignore_permissions=True)
    return {'status':'Pending'}


@frappe.whitelist(methods=['GET'])
def students(month=None,classroom='',search='',page=0):
    from .api import identity, require_role, room_filters
    inst, member = identity(); require_role(member,'Admin','Teacher')
    month=month or now_datetime().strftime('%Y-%m');month_bounds(month)
    rooms=frappe.get_all('IL Classroom',filters=room_filters(inst,member),fields=['name','title','programme'])
    allowed={r.name:r for r in rooms}
    if classroom and classroom not in allowed:
        frappe.throw('Classroom unavailable.',frappe.PermissionError)
    names=[classroom] if classroom else list(allowed)
    if not names:
        return dict(rows=[],rooms=rooms,total=0,page=0)
    query='%'+str(search).strip()[:100]+'%'
    page=max(0,min(int(page),10000))
    params=(inst.name,tuple(names),query,query,query)
    where=""" FROM `tabIL Member` m WHERE m.institute=%s AND m.role='Student'
        AND EXISTS (SELECT 1 FROM `tabIL Enrollment` e WHERE e.student=m.name AND e.institute=m.institute AND e.classroom IN %s AND e.active=1)
        AND (m.full_name LIKE %s OR m.name LIKE %s OR m.user LIKE %s)"""
    total=frappe.db.sql('SELECT COUNT(*)'+where,params)[0][0]
    people=frappe.db.sql('SELECT m.name,m.full_name'+where+' ORDER BY m.full_name,m.name LIMIT 50 OFFSET %s',params+(page*50,),as_dict=True)
    ids=tuple(r.name for r in people) or ('__none__',)
    links=frappe.get_all('IL Enrollment',filters={'institute':inst.name,'classroom':['in',list(allowed)],'student':['in',ids],'active':1},fields=['student','classroom'])
    attendance=attendance_for(inst.name,names,month)
    for person in people:
        person['courses']=[dict(name=e.classroom,title=allowed[e.classroom].title,programme=allowed[e.classroom].programme) for e in links if e.student==person.name]
        person['sessions']=[dict(name=a.session,title=a.session_title,starts_at=a.starts_at,classroom=a.classroom) for a in attendance if a.member==person.name]
        person['session_count']=len({s['name'] for s in person['sessions']})
    return dict(rows=people,rooms=rooms,total=total,page=page,month=month)
