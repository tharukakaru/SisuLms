"""Labelled demo practice and classroom access; never settles real payments."""
import hashlib,hmac
import frappe
USERS={'sisu-public-demo-admin@example.invalid','sisu-public-demo-teacher@example.invalid','sisu-public-demo-independent@example.invalid'}

def demo(room):
    if frappe.local.site!='sisuacademylk.com' or not room.title.startswith('[DEMO] '):return False
    if frappe.db.get_value('IL Institute',room.institute,'code')!='SISUDEMO':return False
    user=frappe.db.get_value('IL Public Profile',room.public_provider,'user')
    return user in USERS and frappe.db.get_value('User',user,'enabled')==0

def key(room):return 'il_demo_practice:'+hashlib.sha256((frappe.session.user+':'+room).encode()).hexdigest()

def classroom_allowed(room,member):
    if member.role!='Student' or not demo(room):return False
    if not frappe.db.exists('IL Member',{'name':member.name,'user':frappe.session.user,'institute':room.institute,'active':1}):return False
    return bool(frappe.cache.get_value(key(room.name)))

@frappe.whitelist(methods=['POST'])
def enter_classroom(classroom,enrollment_key=''):
    from .campus_context import membership,select
    # Verify profile, follow, exact demo ownership and key before enrollment.
    open_practice(classroom,enrollment_key)
    room=frappe.get_doc('IL Classroom',classroom)
    member=membership(room.institute)
    if member.role!='Student':frappe.throw('Use your registered student account.')
    frappe.db.sql('SELECT name FROM `tabIL Member` WHERE name=%s FOR UPDATE',(member.name,))
    prior=frappe.db.get_value('IL Enrollment',{'classroom':room.name,'student':member.name},['name','active'],as_dict=True)
    if prior and not prior.active:frappe.throw('Ask your provider to review this inactive enrollment.')
    if not prior:
        frappe.get_doc({'doctype':'IL Enrollment','institute':room.institute,'classroom':room.name,
            'student':member.name,'active':1,'fee':0,'access_override':'Automatic'}).insert(ignore_permissions=True)
    frappe.cache.set_value(key(room.name),True,expires_in_sec=604800)
    select(room.institute)
    return {'classroom':room.name,'demo':True}

def decorate(rows):
    for row in rows:
        room=frappe.get_doc('IL Classroom',row['name'])
        row['demo']=bool(demo(room))
        row['unlocked']=bool(row['demo'] and (room.fee_mode=='Free' and float(room.fee or 0)==0 or frappe.cache.get_value(key(room.name))))
    return rows

@frappe.whitelist(methods=['POST'])
def open_practice(classroom,enrollment_key=''):
    from .profiles import required
    student=required()
    if student.kind!='Student':frappe.throw('Use your verified student account.',frappe.PermissionError)
    room=frappe.get_doc('IL Classroom',classroom)
    if not demo(room) or not room.active or not room.published:frappe.throw('This demo is unavailable.',frappe.PermissionError)
    # Either follow the exact provider or its institute. Following never grants real paid access.
    profiles=[room.public_provider]
    member=frappe.db.get_value('IL Member',room.teacher,['institute','active'],as_dict=True)
    if member and member.active and member.institute==room.institute:
        profiles+=frappe.get_all('IL Public Profile',filters={'kind':'Institute','workspace':room.institute,'status':'Verified'},pluck='name')
    if not frappe.db.exists('IL Profile Relationship',{'user':frappe.session.user,'profile':['in',profiles],'kind':'Follow','status':'Active'}):
        frappe.throw('Follow this teacher or institute first.')
    free=room.fee_mode=='Free' and float(room.fee or 0)==0
    if not free and not frappe.cache.get_value(key(room.name)):
        from .registration import limit
        limit('self-signup:demo-key:'+frappe.session.user)
        if not isinstance(enrollment_key,str) or not hmac.compare_digest(enrollment_key.strip(),'SISU-DEMO'):
            frappe.throw('Enter the demo enrollment key SISU-DEMO to try this practice lesson.')
        frappe.cache.set_value(key(room.name),True,expires_in_sec=604800)
    return {'title':room.title,'unlocked':True,'body':'Practice: solve 2x + 3 = 11. Subtract 3 from both sides, then divide by 2. Answer: x = 4. Now try 3x + 6 = 21. Answer: x = 5.','notice':'Fictional practice lesson. This demo unlock lasts 7 days and does not grant access to real paid classes or record a payment.'}
