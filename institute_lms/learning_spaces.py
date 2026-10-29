"""Public provider discovery plus student-owned enrollment state within this installed site."""
import frappe
from .api import identity,require_role
from .catalog import provider,class_filters,FIELDS

def following():
    return set(frappe.get_all('IL Profile Relationship',filters={'user':frappe.session.user,'kind':'Follow','status':'Active'},pluck='profile',limit_page_length=0))

@frappe.whitelist()
def directory(query='',page=0):
    identity()
    term=str(query).strip().lstrip('@')[:80]
    rows=frappe.get_all('IL Public Profile',filters={'status':'Verified','kind':['in',['Institute','Teacher']]},or_filters=[['username','like','%'+term+'%'],['display_name','like','%'+term+'%']],fields=FIELDS+['user'],order_by='display_name asc',limit_start=max(0,int(page))*24,limit_page_length=24)
    followed=following()
    affiliated=set(frappe.get_all('IL Profile Relationship',filters={'kind':'Teacher membership','status':'Active','user':['in',[p.user for p in rows] or ['__none__']]},pluck='user'))
    for p in rows:
        p.following=p.name in followed
        p.independent=p.kind!='Teacher' or p.user not in affiliated
        p.followers=frappe.db.count('IL Profile Relationship',{'profile':p.name,'kind':'Follow','status':'Active'})
        p.pop('user',None)
    return rows

@frappe.whitelist()
def choices():
    inst,m=identity();require_role(m,'Student')
    names=following()
    rooms=frappe.get_all('IL Enrollment',filters={'institute':inst.name,'student':m.name,'active':1},pluck='classroom')
    names.update(frappe.get_all('IL Classroom',filters={'name':['in',rooms or ['__none__']],'institute':inst.name},pluck='public_provider'))
    return frappe.get_all('IL Public Profile',filters={'name':['in',list(names) or ['__none__']],'status':'Verified','kind':['in',['Teacher','Institute']]},fields=['name','display_name','kind','lms_id','profile_image'],order_by='display_name asc')

def filters_for(profile,inst):
    p=provider(profile)
    filters=class_filters(p,inst)
    if p.kind=='Teacher':filters['owner_type']='Teacher'
    return filters

def notification_rooms(profile,inst):
    if not profile:return None
    # Public catalogue filtering never grants lesson/payment access.
    filters=filters_for(profile,inst)
    filters.pop('active',None);filters.pop('published',None)
    return frappe.get_all('IL Classroom',filters=filters,pluck='name',limit_page_length=0)

@frappe.whitelist()
def classes(profile='',page=0):
    from .api import access
    inst,m=identity();require_role(m,'Student')
    filters=filters_for(profile,inst) if profile else {'institute':inst.name,'active':1}
    if not profile:
        enrolled=frappe.get_all('IL Enrollment',filters={'institute':inst.name,'student':m.name,'active':1},pluck='classroom')
        filters['name']=['in',enrolled or ['__none__']]
    names=frappe.get_all('IL Classroom',filters=filters,pluck='name',order_by='title asc',limit_start=max(0,int(page))*24,limit_page_length=24)
    result=[]
    for name in names:
        room=frappe.get_doc('IL Classroom',name)
        ename=frappe.db.get_value('IL Enrollment',{'classroom':room.name,'student':m.name,'active':1},'name')
        e=frappe.get_doc('IL Enrollment',ename) if ename else None
        if e and e.get('programme_enrollment'):
            billing=frappe.db.get_value('IL Programme Enrollment',e.programme_enrollment,'billing_enrollment')
            if billing:e=frappe.get_doc('IL Enrollment',billing)
        decision=access(room,m) if e else {'allowed':False}
        pending=bool(e and frappe.db.exists('IL Bank Slip',{'student':m.name,'invoice':['in',frappe.get_all('IL Invoice',filters={'enrollment':e.name},pluck='name') or ['__none__']],'status':'Pending'}))
        state='available' if not e else 'unlocked' if decision['allowed'] else 'pending' if pending else 'payment'
        result.append(dict(name=room.name,title=room.title,cover_image=room.cover_image,teacher_name=frappe.db.get_value('IL Member',room.teacher,'full_name'),teacher_id=frappe.db.get_value('IL Public Profile',{'user':frappe.db.get_value('IL Member',room.teacher,'user'),'status':'Verified'},'lms_id'),fee=room.fee,fee_mode=room.fee_mode,programme=room.get('programme'),state=state,payment_approved=bool(e and frappe.db.exists('IL Invoice',{'enrollment':e.name,'student':m.name,'status':'Paid'})),reason=decision.get('reason','')))
    return {'classes':result,'has_more':len(names)==24}
