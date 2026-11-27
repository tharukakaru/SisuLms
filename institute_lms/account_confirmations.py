"""Transaction-coupled account receipts; no WhatsApp and no ambiguous-send retries."""
import hashlib
from html import escape
import frappe
from .message_templates import add_email_design

def local_demo(user):
    from .signup_environment import local_signup_allowed
    config=getattr(frappe,'conf',{})
    return user.endswith('@demo.sisu.test') and local_signup_allowed(config,config.get('host_name'))

def queue(user,reference,subject,body):
    site=getattr(frappe.local,'site',None)
    if site not in ('sisuacademylk.com','staging.sisuacademylk.com'):return
    name='sisu-confirm-'+hashlib.sha256((user+':'+reference).encode()).hexdigest()[:32]
    if site=='staging.sisuacademylk.com' and not reference.startswith(('enrollment-key:','enrollment-complete:')):return
    if frappe.db.exists('Notification Log',name):return
    frappe.get_doc({'doctype':'Notification Log','for_user':user,'type':'Alert','subject':subject,
        'email_content':escape(body)}).insert(ignore_permissions=True,set_name=name)
    if site=='staging.sisuacademylk.com' or local_demo(user):return  # Test keys stay in-app.
    frappe.enqueue('institute_lms.account_confirmations.deliver',notice=name,enqueue_after_commit=True)

def deliver(notice):
    if getattr(frappe.local,'site',None)!='sisuacademylk.com':return
    log=frappe.get_doc('Notification Log',notice)
    user=log.for_user
    # Local synthetic accounts must never deliver receipts to external services.
    # Keep the in-app notice (including enrollment keys) available for QA.
    if local_demo(user):
        return
    from html import unescape
    body=unescape(log.email_content or '')
    phone=frappe.db.get_value('IL Verified Phone',{'user':user},'phone')
    for channel in ('email','sms'):
        key='il_account_receipt:'+notice+':'+channel
        with frappe.cache.lock(key,timeout=60):
            if frappe.cache.get_value(key):continue
            # Reserve before the network call. A worker crash or timeout requires review.
            frappe.cache.set_value(key,'Review',expires_in_sec=2592000)
            try:
                if channel=='email':
                    from email.message import EmailMessage
                    from email.utils import make_msgid
                    account=frappe.get_doc('Email Account','SISU Academy')
                    message=EmailMessage();message['From']='SISU Academy <noreply@sisuacademylk.com>'
                    message['To']=user;message['Subject']=log.subject;message['Message-ID']=make_msgid(domain='sisuacademylk.com');message.set_content(body)
                    add_email_design(message)
                    mail=frappe.get_doc({'doctype':'Email Queue','sender':message['From'],'email_account':account.name,
                        'message':message.as_string(),'message_id':message['Message-ID'],'status':'Not Sent',
                        'recipients':[{'recipient':user,'status':'Not Sent'}]}).insert(ignore_permissions=True)
                    frappe.db.commit()
                    mail.send(force_send=True)
                elif phone:
                    from .providers import sms
                    sms(phone,body[:400])
                else:continue
                frappe.cache.set_value(key,'Accepted',expires_in_sec=2592000)
            except Exception:
                # No credentials, numbers, codes or provider exception text in logs.
                frappe.log_error(title='Account confirmation needs review',message=notice+' '+channel)
