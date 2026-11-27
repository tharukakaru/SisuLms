"""Retryable, payment-only PDF emails; queue creation and marker commit together."""
from html import escape
import frappe
from .message_templates import sendmail, paragraph, details
from .subscription_receipt import render, date_label

DT = 'IL Account Invoice'


def payment_body(bill):
    return (paragraph(f'Hello {bill.billed_to},')
            + '<div style="padding:22px;background:#f3edf9;border-radius:12px;margin:22px 0">'
            + '<p style="margin:0 0 6px;color:#655871;font-size:13px">PAYMENT CONFIRMED</p>'
            + '<p style="margin:0;font-size:32px;font-weight:700;color:#572b91">'
            + escape(str(bill.currency)) + f' {int(bill.amount_minor)/100:,.2f}</p></div>'
            + paragraph('Thank you. Your subscription payment has been verified.')
            + details([('Plan', bill.plan), ('Subscription starts', date_label(bill.period_start)),
                       ('Subscription ends', date_label(bill.period_end)), ('Paid invoice', bill.receipt_number)])
            + paragraph('Your paid invoice is attached as a PDF. You can also download it from Subscription in your SISU account.')
            + paragraph('No automatic renewal charge has been set up.'))


def deliver(invoice):
    bill = frappe.get_doc(DT, invoice, for_update=True)
    if bill.status != 'Paid' or not bill.receipt_number or bill.receipt_email_status != 'Pending':
        return
    if not bill.billing_email:
        return
    pdf = render(bill)
    message = payment_body(bill)
    queued = sendmail(frappe, recipients=[bill.billing_email],
                    subject=f'Your SISU paid invoice - {bill.receipt_number}',
                    title='Your payment is confirmed', label='SUBSCRIPTION & BILLING',
                    preheader='Payment verified. Your paid invoice is attached as a PDF.',
                    # Frappe sends after the queue transaction commits. This worker
                    # must not wait for the site's periodic email flush to run.
                    message=message, delayed=True, now=True,
                    reference_doctype=DT, reference_name=bill.name,
                    attachments=[{'fname': bill.receipt_number + '.pdf', 'fcontent': pdf}])
    if not queued:
        raise RuntimeError('Invoice email could not be queued')
    bill.receipt_email_status = 'Queued'
    from .account_billing import save
    save(bill)


def dispatch():
    for name in frappe.get_all(DT, filters={'status': 'Paid', 'receipt_email_status': 'Pending'},
                               pluck='name', limit_page_length=20):
        frappe.enqueue('institute_lms.subscription_documents.deliver', invoice=name, queue='short')
