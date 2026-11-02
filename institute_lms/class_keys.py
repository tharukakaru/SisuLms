"""Student-bound bank approval keys. A key never substitutes for paid approval."""
import hashlib
import hmac
import secrets
import frappe
from frappe.utils import now_datetime, get_datetime

def digest(key):
    return hashlib.sha256(key.strip().upper().encode()).hexdigest()

def issue(invoice,room,start,end):
    from .commercial import grant
    from .account_confirmations import queue
    key=secrets.token_hex(8).upper()
    grant(invoice,room,start,end,'Bank transfer',enrollment_key_hash=digest(key))
    user=frappe.db.get_value('IL Member',invoice.student,'user')
    queue(user,'enrollment-key:'+invoice.name,'Payment approved for '+room.title,
          'Your payment was approved. Open My classrooms, choose Enroll now and enter '+key+
          '. Only your student account can use this key, once. Use it before '+str(end)+'.')

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
        frappe.throw('Enter bank name, account holder, account number and branch (10–2000 characters).')
    account=account_for(room);account.bank_instructions=instructions.strip();save(account)
    return {'saved':True}
