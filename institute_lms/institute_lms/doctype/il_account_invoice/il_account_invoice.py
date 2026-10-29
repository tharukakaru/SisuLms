import frappe
from frappe.model.document import Document

class ILAccountInvoice(Document):
    def validate(self):
        if not self.flags.account_billing_service:
            frappe.throw('Use the SISU subscription service', frappe.PermissionError)
        previous=self.get_doc_before_save()
        if previous:
            fixed=('subscription','plan','country','currency','amount_minor','period_start','period_end','anchor_day','billed_to','billing_email')
            for key in fixed:
                if str(previous.get(key)) != str(self.get(key)):
                    frappe.throw('Issued subscription identity and invoice snapshots cannot be changed')
    def on_trash(self):
        frappe.throw('Subscription and financial records cannot be deleted', frappe.PermissionError)
