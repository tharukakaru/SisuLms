import frappe
from frappe.model.document import Document

class ILAccountInvoice(Document):
    def validate(self):
        if not self.flags.account_billing_service:
            frappe.throw('Use the SISU subscription service', frappe.PermissionError)
        if self.receipt_number and self.status != 'Paid':
            frappe.throw('Only verified payments can have an invoice number')
        previous=self.get_doc_before_save()
        if previous:
            if previous.receipt_number and previous.receipt_number != self.receipt_number:
                frappe.throw('An issued invoice number cannot be changed')
            fixed=('subscription','plan','country','currency','amount_minor','period_start','period_end','anchor_day','billed_to','billing_email')
            for key in fixed:
                if str(previous.get(key)) != str(self.get(key)):
                    frappe.throw('Issued subscription identity and invoice snapshots cannot be changed')
    def on_trash(self):
        frappe.throw('Subscription and financial records cannot be deleted', frappe.PermissionError)
