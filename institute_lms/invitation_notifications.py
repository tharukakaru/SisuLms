"""Transactional invitation replies; SMS ambiguity never triggers a blind resend."""
import hashlib
from html import escape
import frappe
from .message_templates import sendmail
from frappe.utils import now_datetime

EVENT = 'teacher.invitation.responded'


def queue_response(invitation,teacher):
    from .notification_service import emit
    from .invitations import invitation_origin
    title=frappe.db.get_value('IL Public Profile',invitation.profile,'display_name')
    verb='accepted' if invitation.status=='Accepted' else 'rejected'
    body=f'{teacher.display_name} (@{teacher.username}) {verb} your invitation to teach at {title}.'
    for member in frappe.get_all('IL Member',filters={'institute':invitation.institute,'role':'Admin','active':1},fields=['name','user']):
        event=emit(invitation.institute,member.name,EVENT,'invitation:'+invitation.name+':'+invitation.status,body,channels=['IN_APP'])
        for channel in ('Email','SMS'):
            key=hashlib.sha256((event+':reply:'+channel).encode()).hexdigest()
            if frappe.db.exists('IL Notification',{'event_key':key}):continue
            phone=frappe.db.get_value('IL Verified Phone',{'user':member.user},'phone') if channel=='SMS' else None
            row=frappe.get_doc(dict(doctype='IL Notification',institute=invitation.institute,recipient=member.name,event=event,
                event_key=key,channel=channel,body=body,status='Queued',attempts=0,next_attempt=now_datetime())).insert(ignore_permissions=True)
            if channel=='Email':
                if frappe.db.get_value('User',member.user,'enabled'):
                    sendmail(frappe, recipients=[member.user],subject='Teacher invitation '+verb,
                        message='<p>'+escape(body)+'</p><p><a href="'+escape(invitation_origin()+'/campus#team',quote=True)+'">Open teaching team</a></p>',
                        delayed=True,reference_doctype='IL Notification',reference_name=row.name)
                    row.status='Accepted';row.save(ignore_permissions=True)
                    frappe.enqueue('institute_lms.invitation_notifications.deliver_email',notice=row.name,enqueue_after_commit=True,queue='short')
                else:row.status='Skipped';row.save(ignore_permissions=True)
            elif phone:
                frappe.enqueue('institute_lms.invitation_notifications.deliver_sms',notice=row.name,enqueue_after_commit=True,queue='short')
            else:row.status='Skipped';row.last_error='No verified mobile number';row.save(ignore_permissions=True)


def deliver_email(notice):
    if frappe.db.get_default('suspend_email_queue') in (1,'1') or frappe.are_emails_muted():return
    for name in frappe.get_all('Email Queue',filters={'reference_doctype':'IL Notification','reference_name':notice,'status':['in',['Not Sent','Partially Sent']]},pluck='name'):
        frappe.get_doc('Email Queue',name,for_update=True).send()


def deliver_sms(notice):
    with frappe.cache.lock('invitation-sms:'+notice,timeout=90):
        row=frappe.get_doc('IL Notification',notice,for_update=True)
        if row.channel!='SMS' or row.status!='Queued' or frappe.db.get_value('IL Notification Event',row.event,'event_type')!=EVENT:return
        member=frappe.get_doc('IL Member',row.recipient)
        phone=frappe.db.get_value('IL Verified Phone',{'user':member.user},'phone')
        if not phone or not member.active or member.role!='Admin' or member.institute!=row.institute:
            row.status='Skipped';row.save(ignore_permissions=True);frappe.db.commit();return
        if not frappe.conf.get('il_sms_adapter'):return
        row.status='Review';row.attempts=int(row.attempts or 0)+1;row.save(ignore_permissions=True);frappe.db.commit()
        try:
            from .providers import sms
            result=sms(phone,row.body,row.event_key)
            row.status='Accepted';row.provider_id=result.get('provider_id');row.sent_at=now_datetime()
        except Exception:
            row.last_error='SMS acceptance uncertain; reconcile with Notify.lk before retrying.'
        row.save(ignore_permissions=True);frappe.db.commit()
