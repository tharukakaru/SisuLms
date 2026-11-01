"""Durable, manually dispatched transactional notices for allowlisted sandbox users."""
import hashlib
import frappe

def enabled():
    return getattr(frappe.local,'site',None)=='hnb-checkout.localhost' and frappe.conf.get('il_signup_notices_enabled')==1

def allowed(user):
    return user in set((frappe.conf.get('il_self_signup_role_emails') or {}).values())|{frappe.conf.get('il_self_signup_test_email')}

def reminder_days(end,today):
    days=(end.date()-today.date()).days
    return days if 1<=days<=10 else None

def queue(user,key,subject,body,sms=None):
    if not enabled() or not allowed(user):return
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(user,))
    digest=hashlib.sha256((user+':'+key).encode()).hexdigest()
    if frappe.db.exists('IL Sandbox Notice',{'notice_key':digest}):return
    notice=frappe.get_doc(dict(doctype='IL Sandbox Notice',notice_key=digest,user=user,subject=subject,
        body=body,sms_body=(sms or body)[:550],email_status='Pending',sms_status='Pending')).insert(ignore_permissions=True)
    frappe.enqueue('institute_lms.sandbox_notices.deliver',notice_name=notice.name,enqueue_after_commit=True,queue='short')
    member=frappe.db.get_value('IL Member',{'user':user,'active':1},['name','institute'],as_dict=True)
    if member:
        from .notification_service import emit
        emit(member.institute,member.name,'announcement','sandbox-notice:'+digest,body,channels=['IN_APP'])

def welcome(user,role):
    body=f'Your SISU {role} account was created successfully. Sign in at http://localhost:8001/campus using {user} and the password you chose, or your linked Google account. We will never include your password in a message. This address is for the sandbox computer only.'
    queue(user,'welcome','Welcome to SISU',body)

def observe(doc,method=None):
    if not enabled():return
    frappe.db.savepoint('sisu_notice')
    try:_observe(doc,method)
    except Exception:
        frappe.db.rollback(save_point='sisu_notice')
        frappe.log_error(title='Sandbox notice needs review',message='A transactional notice could not be queued. Payment and membership processing were preserved.')

def _observe(doc,method=None):
    old=doc.get_doc_before_save()
    if doc.doctype=='IL Account Invoice' and doc.status=='Paid' and (not old or old.status!='Paid'):
        account=frappe.get_doc('IL Account Subscription',doc.subscription)
        from .plan_catalog import plan_features
        features=', '.join(k.replace('_',' ') for k,v in plan_features(doc.plan).items() if v is True) if account.role!='Student' else 'Student learning access'
        body=f'Your SISU {doc.plan} subscription payment is confirmed. Features: {features}. Access expires on {doc.period_end}. Thank you. Review your receipt in Billing.'
        queue(account.user,'paid:'+doc.name,'SISU subscription activated',body,
            f'Your SISU {doc.plan} subscription is activated until {doc.period_end}. See your email and Billing for included features and receipt.')
    elif doc.doctype=='IL Usage Invoice' and doc.status in ('Estimate','Unpaid','Paid') and (not old or old.status!=doc.status):
        account=frappe.get_doc('IL Account Subscription',doc.subscription)
        label='estimate (not a final invoice)' if doc.status=='Estimate' else 'invoice'
        queue(account.user,'usage:'+doc.name+':'+doc.status,'SISU active-student '+label,
            f'Your active-student {label} is available in Billing. Amount: LKR {doc.amount_lkr}. Due date: {doc.due_at}. Status: {doc.status}. Review the document before payment.')
    elif doc.doctype=='IL Profile Relationship' and doc.kind=='Teacher membership' and doc.status=='Active' and old and old.status=='Pending':
        title=frappe.db.get_value('IL Public Profile',doc.profile,'display_name')
        queue(doc.user,'confirmed:'+doc.name,'Institute registration confirmed',
              f'{title} has confirmed your institute registration. Sign in to SISU to review your assigned classes. Membership does not bypass subscription or class-access requirements.')

def expiry():
    if not enabled():return
    from frappe.utils import now_datetime,get_datetime
    today=now_datetime()
    for row in frappe.get_all('IL Account Subscription',filters={'enabled':1,'paid_until':['is','set']},fields=['name','user','plan','paid_until']):
        days=reminder_days(get_datetime(row.paid_until),today)
        if days:
            queue(row.user,'expiry:'+row.name+':'+str(row.paid_until)+':'+today.date().isoformat(),
                'SISU subscription expiry reminder',f'Your SISU {row.plan} plan expires on {row.paid_until}, in {days} day(s). Open Billing to review renewal. No automatic charge is made.')

def deliver(limit=10,notice_name=None):
    if not enabled():raise ValueError('Sandbox notices disabled')
    from email.message import EmailMessage
    from email.utils import make_msgid
    from .providers import sms
    names=[notice_name] if notice_name else frappe.get_all('IL Sandbox Notice',or_filters={'email_status':'Pending','sms_status':'Pending'},pluck='name',limit_page_length=limit,order_by='creation asc')
    for name in names:
        with frappe.cache.lock('sandbox-notice:'+name,timeout=90):
            d=frappe.get_doc('IL Sandbox Notice',name)
            if not allowed(d.user):continue
            if d.email_status=='Pending':
                d.email_status='Review';d.save(ignore_permissions=True);frappe.db.commit()
                try:
                    m=EmailMessage();m['From']='SISU Academy <noreply@sisuacademylk.com>';m['To']=d.user;m['Subject']=d.subject;m['Message-ID']=make_msgid(domain='sisuacademylk.com');m.set_content(d.body)
                    q=frappe.get_doc(dict(doctype='Email Queue',email_account='SISU Academy',sender=m['From'],message=m.as_string(),message_id=m['Message-ID'],status='Not Sent',recipients=[dict(recipient=d.user,status='Not Sent')])).insert(ignore_permissions=True)
                    frappe.db.commit();q.send(force_send=True);q.reload()
                    if q.status=='Sent':d.email_status='Accepted'
                except Exception:pass  # Review is retained; never retry an uncertain send automatically.
                d.save(ignore_permissions=True);frappe.db.commit()
            if d.sms_status=='Pending':
                d.sms_status='Review';d.save(ignore_permissions=True);frappe.db.commit()
                try:
                    phone=frappe.db.get_value('IL Verified Phone',{'user':d.user},'phone')
                    if not phone or phone!=frappe.conf.get('il_self_signup_test_phone'):raise ValueError('Recipient changed')
                    sms(phone,d.sms_body,d.notice_key);d.sms_status='Accepted'
                except Exception:pass
                d.save(ignore_permissions=True);frappe.db.commit()
            print('Notice channels: email='+d.email_status+', SMS='+d.sms_status+' (acceptance is not delivery)')
