import frappe
from frappe.model.document import Document

class ILBankSlip(Document):
    def validate(self):
        if not self.flags.commercial_service:
            frappe.throw("Use the audited SISU billing service", frappe.PermissionError)
    def on_trash(self):
        frappe.throw("Financial records cannot be deleted; use a recorded reversal", frappe.PermissionError)
