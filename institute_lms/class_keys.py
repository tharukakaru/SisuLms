"""Student-bound bank approval keys. A key never substitutes for paid approval."""
import hashlib
import hmac
import secrets
import time
import re
import frappe
from frappe.utils import now_datetime, get_datetime

def digest(key):
    return hashlib.sha256(key.strip().upper().encode()).hexdigest()

KEY_SECONDS = 15 * 60

def new_key():
    return str(int(time.time())) + '-' + secrets.token_hex(8).upper()

def key_is_current(key):
    value=key.strip().upper()
    if not re.fullmatch(r'[0-9]{10}-[A-F0-9]{16}',value):return False
    age=time.time()-int(value.split('-')[0])
    return 0<=age<KEY_SECONDS

def send_key(user,reference,room,key):
    from .account_confirmations import queue
    queue(user,'enrollment-key:'+reference+':'+digest(key)[:16],
          'Payment accepted — enrollment key',
          'Payment accepted for '+room.title[:100]+'. Your personal enrollment key: '+key+
          '. Expires in 15 minutes. Only your account can use it, once. Open My classrooms to enroll. If expired, choose Resend enrollment key; no second payment is needed.')

def issue(invoice,room,start,end):
    from .commercial import grant
    key=new_key()
    grant(invoice,room,start,end,'Bank transfer',enrollment_key_hash=digest(key))
    user=frappe.db.get_value('IL Member',invoice.student,'user')
    send_key(user,invoice.name,room,key)


@frappe.whitelist(methods=['POST'])
def redeem(classroom,key):
    from .api import identity, scoped, require_role
    from .commercial import locked,save
    from .registration import limit
    from .account_confirmations import queue
    inst,member=identity();require_role(member,'Student')
    room=scoped('IL Classroom',classroom,inst)
    limit('self-signup:class-key:'+frappe.session.user)
    if not isinstance(key,str) or not 8<=len(key)<=64:frappe.throw('Check your enrollment key.')
    names=frappe.get_all('IL Paid Access',filters={'classroom':room.name,'student':member.name,'institute':inst.name,'status':'Awaiting key'},pluck='name')
    for name in names:
        access=locked('IL Paid Access',name)
        if access.student!=member.name or access.institute!=inst.name or access.classroom!=room.name:
            frappe.throw('Enrollment unavailable.',frappe.PermissionError)
        if access.status!='Awaiting key' or not hmac.compare_digest(access.enrollment_key_hash or '',digest(key)):continue
        if not key_is_current(key):frappe.throw('This enrollment key expired. Choose Resend enrollment key; your payment is still approved.')
        if get_datetime(access.ends_at)<=now_datetime():frappe.throw('This access period has ended. Contact your provider.')
        if not frappe.db.exists('IL Invoice',{'name':access.invoice,'student':member.name,'status':'Paid'}):frappe.throw('Payment approval is required.')
        access.status='Active';access.enrollment_key_hash=None;save(access)
        queue(frappe.session.user,'enrollment-complete:'+access.name,'Enrollment successful',
              'You are enrolled in '+room.title+'. Open My classrooms to view your classroom.')
        return {'enrolled':True}
    frappe.throw('This key is invalid, already used, or belongs to another student.')

@frappe.whitelist(methods=['GET'])
def bank_details(classroom):
    from .api import identity,scoped,require_role
    from .commercial import account_for
    inst,member=identity();require_role(member,'Student','Admin','Teacher')
    room=scoped('IL Classroom',classroom,inst)
    account=account_for(room)
    return {'instructions':account.bank_instructions or '', 'recipient':
            frappe.db.get_value('User',room.owner_user,'full_name') if room.owner_type=='Teacher' else inst.title,
            'fee':room.fee,'classroom':room.name}

@frappe.whitelist(methods=['POST'])
def save_bank_details(classroom,instructions):
    from .api import classroom_for
    from .commercial import account_for,save
    inst,member,room=classroom_for(classroom,True)
    if not (room.owner_type=='Institute' and member.role=='Admin' or
            room.owner_type=='Teacher' and room.owner_user==frappe.session.user):
        frappe.throw('Only the payment recipient can change these bank details.',frappe.PermissionError)
    if not isinstance(instructions,str) or not 10<=len(instructions.strip())<=2000:
        frappe.throw('Enter bank name, account holder, account number and branch (10Ã¢â‚¬â€œ2000 characters).')
    account=account_for(room);account.bank_instructions=instructions.strip();save(account)
    return {'saved':True}


@frappe.whitelist(methods=['GET'])
def key_status(classroom):
    from .api import identity, scoped, require_role
    inst,member=identity();require_role(member,'Student')
    room=scoped('IL Classroom',classroom,inst)
    rows=frappe.get_all('IL Paid Access',filters={'classroom':room.name,'student':member.name,
        'institute':inst.name,'status':'Awaiting key'},fields=['name','invoice','ends_at'])
    approved=any(get_datetime(r.ends_at)>now_datetime() and frappe.db.exists('IL Invoice',
        {'name':r.invoice,'student':member.name,'status':'Paid'}) for r in rows)
    return {'payment_approved':approved,'key_valid_for_seconds':KEY_SECONDS}

@frappe.whitelist(methods=['POST'])
def resend(classroom):
    from .api import identity, scoped, require_role
    from .commercial import locked,save
    inst,member=identity();require_role(member,'Student')
    room=scoped('IL Classroom',classroom,inst)
    names=frappe.get_all('IL Paid Access',filters={'classroom':room.name,'student':member.name,
        'institute':inst.name,'status':'Awaiting key'},pluck='name',order_by='creation desc')
    for name in names:
        access=locked('IL Paid Access',name)
        if access.student!=member.name or access.institute!=inst.name or access.classroom!=room.name:
            frappe.throw('Enrollment unavailable.',frappe.PermissionError)
        if access.status!='Awaiting key' or get_datetime(access.ends_at)<=now_datetime():continue
        if not frappe.db.exists('IL Invoice',{'name':access.invoice,'student':member.name,'status':'Paid'}):continue
        throttle='il_class_key_resend:'+access.name
        last=frappe.cache.get_value(throttle)
        if last and time.time()-float(last)<60:frappe.throw('Please wait one minute before requesting another key.')
        key=new_key();access.enrollment_key_hash=digest(key);save(access)
        send_key(frappe.session.user,access.invoice,room,key)
        frappe.cache.set_value(throttle,time.time(),expires_in_sec=60)
        return {'queued':True,'expires_in_seconds':KEY_SECONDS,'retry_after_seconds':60}
    frappe.throw('No approved payment awaiting enrollment. Refresh your classroom or contact your provider.')


@frappe.whitelist(methods=['GET'])
def classroom_bank_settings(classroom=None):
    from .api import identity, classroom_for, require_role
    from .commercial import account_for
    inst,member=identity();require_role(member,'Teacher','Admin')
    if classroom:
        inst,member,room=classroom_for(classroom,True)
    else:
        room=frappe._dict(institute=inst.name,owner_type='Institute' if member.role=='Admin' else 'Teacher',owner_user=member.user)
    editable=False  # Receiving accounts are managed centrally in the provider profile.
    account=account_for(room,False)
    return {'instructions':account.bank_instructions or '' if account else '', 'editable':bool(editable),'owner_type':room.owner_type}


@frappe.whitelist(methods=['GET'])
def institute_bank_details():
    from .api import identity, require_role
    from .commercial import account_for
    inst, member = identity()
    require_role(member, 'Admin')
    account = account_for({'owner_type':'Institute','institute':inst.name})
    return {'instructions':account.bank_instructions or '', 'institute':inst.title}


@frappe.whitelist(methods=['POST'])
def save_institute_bank_details(instructions):
    from .api import identity, require_role
    from .commercial import account_for, locked, save
    inst, member = identity()
    require_role(member, 'Admin')
    if not isinstance(instructions,str) or not 10<=len(instructions.strip())<=2000:
        frappe.throw('Enter bank name, account holder, account number and branch (10–2000 characters).')
    account = account_for({'owner_type':'Institute','institute':inst.name})
    account = locked('IL Provider Account',account.name)
    account.bank_instructions = instructions.strip()
    save(account)
    return {'saved':True}


def independent_bank_account():
    from .api import identity, require_role
    from .commercial import account_for, account_access
    inst, member = identity()
    require_role(member, 'Teacher')
    account = account_for({'owner_type':'Teacher','owner_user':frappe.session.user,'institute':inst.name})
    account_access(account)
    return account


@frappe.whitelist(methods=['GET'])
def teacher_bank_details():
    account = independent_bank_account()
    return {'instructions':account.bank_instructions or ''}


@frappe.whitelist(methods=['POST'])
def save_teacher_bank_details(instructions):
    from .commercial import locked, save
    account = independent_bank_account()
    if not isinstance(instructions,str) or not 10<=len(instructions.strip())<=2000:
        frappe.throw('Enter bank name, account holder, account number and branch (10–2000 characters).')
    account = locked('IL Provider Account',account.name)
    account.bank_instructions = instructions.strip()
    save(account)
    return {'saved':True}
