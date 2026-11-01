import frappe
from frappe.model.document import Document

class ILCyberSourceAttempt(Document):
    def validate(self):
        if not self.flags.cybersource_service:
            frappe.throw('Use the CyberSource payment service', frappe.PermissionError)
        previous = self.get_doc_before_save()
        if previous:
            for key in ('reference','kind','invoice','institute','customer','merchant_scope','merchant_id','amount_minor','currency','request_snapshot'):
                if self.get(key) != previous.get(key):
                    frappe.throw('Payment attempt identity is immutable')
            if previous.status == 'succeeded' and self.status != 'succeeded':
                frappe.throw('Successful payments cannot be downgraded')
    def on_trash(self):
        frappe.throw('Payment records cannot be deleted', frappe.PermissionError)
