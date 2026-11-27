"""One reminder per expiry, with durable email queue and fail-closed SMS delivery."""
import hashlib
from html import escape
import frappe
from .message_templates import sendmail
from frappe.utils import now_datetime, get_datetime
from .renewal_rules import expiry, window

DT='IL Renewal Notice'

def queue(account, now=None, test=False):
    now=now or now_datetime()
    end=expiry(account)
    if not end or end<=now or not window(account,now)['renewal_available']:
        return None
    from .subscription_sms import customer_user
    user=customer_user(account)
    if not user or not frappe.db.get_value('User',user,'enabled'):
        return None
    key=hashlib.sha256(f'{"qa" if test else "renewal"}:{account.name}:{end}:{user}'.encode()).hexdigest()
    existing=frappe.db.get_value(DT,{'notice_key':key},'name')
    if existing:return existing
    email=account.billing_email or user
    phone=frappe.db.get_value('IL Verified Phone',{'user':user},'phone')
    label='plan' if account.paid_until else 'personal trial'
    body=(f'Renewal is open\nYour SISU {label} ends: {end:%d %b %Y, %I:%M %p} (Sri Lanka time).\n'
          'Open Subscription to renew. Early renewal keeps your remaining days; '
          'the next month starts when current access ends. No automatic charge.')
    if test:body='LOCAL QA REMINDER TEST: '+body
    notice=frappe.get_doc(dict(doctype=DT,notice_key=key,subscription=account.name,user=user,
        expires_at=end,email=email,phone=phone,body=body,email_status='Pending',sms_status='Pending')).insert(ignore_permissions=True)
    frappe.enqueue('institute_lms.renewal_notices.deliver',notice=notice.name,enqueue_after_commit=True,queue='short')
    return notice.name

def deliver(notice):
    with frappe.cache.lock('renewal-notice:'+notice,timeout=90):
        row=frappe.get_doc(DT,notice,for_update=True)
        account=frappe.get_doc('IL Account Subscription',row.subscription)
        from .subscription_sms import customer_user
        valid=(account.enabled and not account.cancel_at_end and customer_user(account)==row.user
               and expiry(account)==get_datetime(row.expires_at) and get_datetime(row.expires_at)>now_datetime())
        if not valid:
            if row.email_status=='Pending':row.email_status='Skipped'
            if row.sms_status=='Pending':row.sms_status='Skipped'
            row.save(ignore_permissions=True);frappe.db.commit();return
        if row.email_status=='Pending':
            if row.email and row.email==(account.billing_email or row.user) and not row.email.endswith('.invalid'):
                queued=sendmail(frappe, recipients=[row.email],subject='Your SISU renewal is open',
                    message='<p>'+escape(row.body).replace('\n','<br>')+'</p><p>Sign in to SISU and open Subscription.</p>',
                    delayed=True,now=True,reference_doctype=DT,reference_name=row.name)
                if not queued:raise RuntimeError('Renewal email could not be queued')
                row.email_status='Queued'
            else:row.email_status='Skipped'
            row.save(ignore_permissions=True);frappe.db.commit()
        if row.sms_status=='Pending':
            phone=frappe.db.get_value('IL Verified Phone',{'user':row.user},'phone')
            if not phone or phone!=row.phone or row.user.endswith('.invalid'):
                row.sms_status='Skipped';row.save(ignore_permissions=True);frappe.db.commit();return
            row.sms_status='Review';row.save(ignore_permissions=True);frappe.db.commit()
            try:
                from .providers import sms
                sms(phone,row.body,row.notice_key)
                row.sms_status='Accepted'
            except Exception:
                row.last_error='SMS acceptance uncertain; reconcile before retrying.'
            row.save(ignore_permissions=True);frappe.db.commit()

def dispatch():
    if frappe.conf.get('il_control_plane'):return
    for name in frappe.get_all('IL Account Subscription',filters={'enabled':1,'cancel_at_end':0,'role':['in',['Teacher','Institute']]},pluck='name'):
        with frappe.cache.lock('renewal-queue:'+name,timeout=20):
            queue(frappe.get_doc('IL Account Subscription',name))
    for name in frappe.get_all(DT,or_filters={'email_status':'Pending','sms_status':'Pending'},pluck='name',limit_page_length=50):
        frappe.enqueue('institute_lms.renewal_notices.deliver',notice=name,enqueue_after_commit=True,queue='short')
