import frappe
from frappe.model.document import Document

class ILAccountSubscription(Document):
    def validate(self):
        if not self.flags.account_billing_service:
            frappe.throw('Use the SISU subscription service', frappe.PermissionError)
        previous=self.get_doc_before_save()
        if previous:
            fixed=('trial_started','trial_until','account_key','role')
            for key in fixed:
                if str(previous.get(key)) != str(self.get(key)):
                    frappe.throw('Issued subscription identity and invoice snapshots cannot be changed')
    def on_trash(self):
        frappe.throw('Subscription and financial records cannot be deleted', frappe.PermissionError)
