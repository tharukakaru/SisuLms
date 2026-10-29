"""Scoped transactional WhatsApp templates; no browser-supplied message or phone."""
import re
import frappe
from frappe.utils import now_datetime, get_datetime
from .commercial import account_for, locked_reason
from .plan_catalog import plan_features

KINDS={'payment_approved':'Payment approved','enrolment_reminder':'Enrolment reminder','class_scheduled':'Class scheduled'}

def scope(classroom):
    from .api import classroom_for
    inst,member,room=classroom_for(classroom,True)
    account=account_for(room,False)
    if account and locked_reason(account):frappe.throw(locked_reason(account),frappe.PermissionError)
    if not room.active:frappe.throw('Classroom unavailable',frappe.PermissionError)
    return inst,member,room,account

def entitled(account):return bool(account and plan_features(account.plan).get('whatsapp'))

def configured(event,language):
    templates=frappe.conf.get('il_whatsapp_event_templates') or {}
    template=templates.get(event,{}).get(language)
    return bool(frappe.conf.get('il_whatsapp_token') and frappe.conf.get('il_whatsapp_phone_id') and frappe.conf.get('il_whatsapp_graph_version') and template and template.get('name') and template.get('language'))

@frappe.whitelist()
def options(classroom,search=''):
    inst,_,room,account=scope(classroom)
    if not entitled(account):return {'available':False,'plan':account.plan if account else 'Unassigned','students':[],'sessions':[]}
    names=frappe.get_all('IL Enrollment',filters={'classroom':room.name,'active':1},pluck='student')
    rows=frappe.get_all('IL Member',filters={'name':['in',names or ['__none__']],'institute':inst.name,'active':1},or_filters={'full_name':['like','%'+str(search)[:100]+'%'],'name':['like','%'+str(search)[:100]+'%']} if search else None,fields=['name','full_name'],limit_page_length=51)
    sessions=frappe.get_all('IL Session',filters={'classroom':room.name,'status':['!=','Cancelled'],'ends_at':['>',now_datetime()]},fields=['name','title','starts_at','ends_at'],order_by='starts_at asc',limit_page_length=30)
    return {'available':True,'plan':account.plan,'students':rows[:50],'has_more':len(rows)>50,'sessions':sessions}

def prepared(classroom,student,kind,session=None,slip=None):
    from .notifications import whatsapp_allowed
    from .notification_service import preference
    inst,_,room,account=scope(classroom)
    if not entitled(account):frappe.throw('WhatsApp templates require Gold or Platinum',frappe.PermissionError)
    if kind not in KINDS:frappe.throw('Choose a message template')
    if not frappe.db.exists('IL Enrollment',{'classroom':room.name,'student':student,'active':1}):frappe.throw('Choose a student in this class',frappe.PermissionError)
    person=frappe.get_doc('IL Member',student)
    if person.institute!=inst.name or person.role!='Student' or not person.active:frappe.throw('Student unavailable',frappe.PermissionError)
    event='whatsapp.'+kind
    eligible=bool(whatsapp_allowed(person) and preference(person.user,event).get('WHATSAPP'))
    if kind=='payment_approved':
        payment=frappe.get_doc('IL Bank Slip',slip) if slip else None
        if not payment or payment.classroom!=room.name or payment.student!=person.name or payment.institute!=inst.name or payment.status!='Approved':frappe.throw('Select this student’s approved bank payment')
        body=f'Hello {person.full_name}, your payment for {room.title} has been approved. Open SISU to view your class access and learning materials.'
        context_key=payment.name
    elif kind=='class_scheduled':
        lesson=frappe.get_doc('IL Session',session) if session else None
        if not lesson or lesson.classroom!=room.name or lesson.status=='Cancelled' or get_datetime(lesson.ends_at)<=now_datetime():frappe.throw('Choose an upcoming session from this class')
        body=f'Hello {person.full_name}, your teacher has scheduled {lesson.title} for {lesson.starts_at} (Sri Lanka time). Open {room.title} in SISU for the class link and details.'
        context_key=lesson.name+':'+str(lesson.modified)
    else:
        body=f'Hello {person.full_name}, ready for your next lesson? Open {room.title} in SISU to review your enrolment and complete any outstanding class payment.'
        context_key=room.name+':'+str(now_datetime().date())
    return dict(body=body,event=event,eligible=eligible,configured=configured(event,person.language),recipient_name=person.full_name,recipient_id=person.name,context_key=context_key),room,person

@frappe.whitelist()
def preview(classroom,student,kind,session=None,slip=None):
    result,_,_=prepared(classroom,student,kind,session,slip)
    return {k:v for k,v in result.items() if k!='context_key'}

@frappe.whitelist(methods=['POST'])
def send(classroom,student,kind,request_id,session=None,slip=None):
    from .notification_service import emit
    if not re.fullmatch(r'[A-Za-z0-9-]{16,80}',str(request_id)):frappe.throw('Invalid message request')
    result,room,person=prepared(classroom,student,kind,session,slip)
    if not result['eligible']:frappe.throw('This student has not enabled eligible WhatsApp updates')
    if not result['configured']:frappe.throw('Connect WhatsApp and configure an approved template for this language first')
    # One context message per student prevents duplicate approvals/reminders on repeated clicks.
    key='manual-whatsapp:'+kind+':'+result['context_key']
    name=emit(room.institute,person.name,result['event'],key,result['body'],channels=('WHATSAPP',),classroom=room.name)
    status=frappe.db.get_value('IL Notification',{'event':name,'channel':'WhatsApp'},'status') or 'Queued'
    return {'event':name,'status':status,'message':'WhatsApp update: '+status+'. Repeat requests reuse this message; acceptance and delivery are tracked separately.'}
