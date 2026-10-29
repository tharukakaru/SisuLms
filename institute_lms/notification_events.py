"""Domain event adapters; deduplication keys describe persisted business transitions."""
from datetime import timedelta
import frappe
from frappe.utils import now_datetime
from .notification_service import emit

def classroom(room,event,key,body):
    for member in frappe.get_all('IL Enrollment',filters={'classroom':room.name,'active':1},pluck='student'):
        emit(room.institute,member,event,key,body)

def paper_changed(doc,method=None):
    old=doc.get_doc_before_save()
    if doc.status=='Published' and (not old or old.status!='Published'):
        room=frappe.get_doc('IL Classroom',doc.classroom)
        event='assignment.created' if doc.allow_upload else 'quiz.available'
        classroom(room,event,'paper:'+doc.name+':published',doc.title+' is available')

def attempt_changed(doc,method=None):
    old=doc.get_doc_before_save()
    if doc.status=='Graded' and (not old or old.status!='Graded' or old.score!=doc.score):
        paper=frappe.get_doc('IL Paper',doc.paper)
        emit(paper.institute,doc.student,'quiz.result','result:'+doc.name+':'+str(doc.score),'Your result is available: '+paper.title)

def due_reminders():
    if frappe.conf.get('il_control_plane'):return
    now=now_datetime()
    for paper in frappe.get_all('IL Paper',filters={'status':'Published','closes_at':['between',[now,now+timedelta(hours=24)]]},fields=['name','title','classroom','closes_at'],limit_page_length=500):
        room=frappe.get_doc('IL Classroom',paper.classroom)
        classroom(room,'assignment.due','due:'+paper.name+':'+str(paper.closes_at),paper.title+' closes within 24 hours')

def certificate_issued(doc,method=None):
    user=doc.get('member')
    if not user:return
    member=frappe.db.get_value('IL Member',{'user':user,'active':1},['name','institute'],as_dict=True)
    if member:emit(member.institute,member.name,'certificate.issued','certificate:'+doc.name,'Your certificate is available')
