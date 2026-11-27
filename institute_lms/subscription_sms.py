"""Durable payment SMS outbox. Uncertain sends require review, never blind retries."""
import hashlib
import frappe
from .subscription_receipt import date_label

DT = 'IL Subscription SMS'


def customer_user(account):
    """Institute subscriptions belong to a workspace, not a User record."""
    if account.get('role') != 'Institute':
        return account.user
    admins = frappe.get_all('IL Member', filters={
        'institute': account.institute, 'role': 'Admin', 'active': 1,
    }, pluck='user', order_by='creation asc, name asc')
    if account.billing_email in admins:
        return account.billing_email
    return admins[0] if admins else None


def queue_paid(bill, account):
    if bill.status != 'Paid' or not frappe.conf.get('il_subscription_sms_enabled'):
        return
    if 'sandbox' in str(bill.payment_channel or '').lower():
        return
    user = customer_user(account)
    if not user:
        return
    profile = frappe.db.get_value('IL Public Profile', {'user': user}, ['username','display_name','lms_id'], as_dict=True) or {}
    user_id = profile.get('lms_id')
    label = (account.display_name if account.get('role') == 'Institute' else profile.get('display_name')) or account.display_name or user
    label = label[:70]
    username = profile.get('username') or user
    identity = label + ' (@' + username.lstrip('@') + ')' + ((' '+user_id) if user_id else '')
    amount = f'{bill.currency} {int(bill.amount_minor)/100:,.2f}'
    teacher_phone = frappe.db.get_value('IL Verified Phone', {'user':user}, 'phone')
    admin_phone = frappe.conf.get('il_subscription_admin_sms_phone')
    rows = [('teacher',teacher_phone,f'Payment confirmed: {amount}\nPlan: {bill.plan}\nActive until: {date_label(bill.period_end)}\nInvoice: {bill.receipt_number}\nYour PDF invoice will arrive by email. Also available in Subscription.'),
            ('admin',admin_phone,f'New plan payment\n{identity}\nPlan: {bill.plan} | {amount}\nInvoice: {bill.receipt_number}\nActive until: {date_label(bill.period_end)}')]
    for recipient,phone,body in rows:
        if not phone:
            continue
        key = hashlib.sha256((bill.name+':'+recipient).encode()).hexdigest()
        if frappe.db.exists(DT, {'notice_key':key}):
            continue
        notice = frappe.get_doc(dict(doctype=DT,notice_key=key,invoice=bill.name,user=user,
            recipient=recipient,phone=phone,body=body,status='Queued')).insert(ignore_permissions=True)
        frappe.enqueue('institute_lms.subscription_sms.deliver',notice=notice.name,enqueue_after_commit=True,queue='short')


def deliver(notice):
    if not frappe.conf.get('il_subscription_sms_enabled'):
        return
    with frappe.cache.lock('subscription-sms:'+notice,timeout=90):
        row = frappe.get_doc(DT,notice,for_update=True)
        if row.status != 'Queued':
            return
        if frappe.db.get_value('IL Account Invoice',row.invoice,'status') != 'Paid':
            row.status='Skipped';row.save(ignore_permissions=True);frappe.db.commit();return
        phone = (frappe.db.get_value('IL Verified Phone',{'user':row.user},'phone') if row.recipient=='teacher'
                 else frappe.conf.get('il_subscription_admin_sms_phone'))
        if not phone or phone != row.phone:
            row.status='Skipped';row.save(ignore_permissions=True);frappe.db.commit();return
        row.status='Review';row.save(ignore_permissions=True);frappe.db.commit()
        try:
            from .providers import sms
            result=sms(phone,row.body,row.notice_key)
            row.status='Accepted';row.provider_id=result.get('provider_id')
        except Exception:
            row.last_error='SMS acceptance is uncertain. Check Notify.lk before retrying.'
        row.save(ignore_permissions=True);frappe.db.commit()


def dispatch():
    if not frappe.conf.get('il_subscription_sms_enabled'):
        return
    for name in frappe.get_all(DT,filters={'status':'Queued'},pluck='name',limit_page_length=20):
        deliver(name)
