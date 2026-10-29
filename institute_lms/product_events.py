"""Durable notification triggers; no direct provider sends from business transactions."""
import frappe

def user_event(institute,user,event,key,body):
    from .notification_service import emit
    member=frappe.db.get_value('IL Member',{'institute':institute,'user':user,'active':1},'name')
    if member:return emit(institute,member,event,event+':'+key,body)

def classroom_event(classroom,event,key,body):
    from .notification_service import emit
    room=frappe.get_doc('IL Classroom',classroom)
    recipients=set(frappe.get_all('IL Enrollment',filters={'classroom':classroom,'active':1},pluck='student'))
    if room.teacher:recipients.add(room.teacher)
    for member in recipients:
        if frappe.db.exists('IL Member',{'name':member,'institute':room.institute,'active':1}):
            emit(room.institute,member,event,event+':'+key,body)

def observe(doc,method=None):
    """Doc hooks run inside the originating transaction. Keys represent transitions."""
    if doc.doctype=='IL Live Room':
        if doc.has_value_changed('status'):
            classroom_event(doc.classroom,'live.changed',doc.name+':'+doc.status,'Live class '+doc.title+': '+doc.status)
        if doc.recording_status=='Ready' and doc.has_value_changed('recording_status'):
            room=frappe.get_doc('IL Classroom',doc.classroom)
            user=frappe.db.get_value('IL Member',room.teacher,'user')
            if user:user_event(doc.institute,user,'recording.ready',doc.name,'Recording ready for teacher review: '+doc.title)
    elif doc.doctype=='IL Paper Generation Job' and doc.has_value_changed('status') and doc.status in ('Draft','Review'):
        user_event(doc.institute,doc.user,'paper.ready',doc.name+':'+doc.status,'Paper generation '+doc.status+'. Review before publication.')
    elif doc.doctype=='IL Lecture Order' and doc.has_value_changed('status') and doc.status in ('succeeded','failed','cancelled'):
        user_event(doc.institute,doc.user,'lesson.payment',doc.name+':'+doc.status,'Lesson payment '+doc.status+'. Check My Purchases for server-confirmed access.')
