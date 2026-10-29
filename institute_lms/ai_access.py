"""All AI content paths require a real site-local membership, including operators."""
import frappe
from .saas import require

def authorize(feature,classroom=None,teacher=False,admin=False):
    require(feature)
    if frappe.conf.get('il_control_plane'):frappe.throw('Learning data is tenant-local',frappe.PermissionError)
    from .api import identity,classroom_for,accessible_room
    inst,m=identity()
    # identity's System Manager convenience must not grant AI content access.
    if not m.name or not frappe.db.exists('IL Member',{'name':m.name,'user':frappe.session.user,'institute':inst.name,'active':1}):
        frappe.throw('Active local membership required',frappe.PermissionError)
    if admin and m.role!='Admin':frappe.throw('Institute Admin required',frappe.PermissionError)
    if teacher and m.role not in ('Teacher','Admin'):frappe.throw('Teacher required',frappe.PermissionError)
    from .soul import student_ready
    if not student_ready(m):frappe.throw('Student AI is not enabled for this account',frappe.PermissionError)
    room=None
    if classroom:
        _,_,room=classroom_for(classroom,write=True) if teacher else accessible_room(classroom)
        from .retention import access_allowed
        if room.institute!=inst.name or not room.active or not access_allowed(room):frappe.throw('Course expired or unavailable',frappe.PermissionError)
    return inst,m,room

def hosted_student(member):
    if member.role=='Student' and not frappe.conf.get('il_ai_hosted_student_reviewed'):
        frappe.throw('Hosted retrieval is not enabled for student accounts',frappe.PermissionError)

def owned_conversation(name,feature='ai.assistant',active=False):
    d=frappe.get_doc('IL AI Conversation',name)
    inst,m,room=authorize(feature,d.classroom)
    if d.user!=frappe.session.user or d.institute!=inst.name or d.status=='Deleted' or (active and d.status!='Active'):
        frappe.throw('Conversation unavailable',frappe.PermissionError)
    return d,inst,m,room
