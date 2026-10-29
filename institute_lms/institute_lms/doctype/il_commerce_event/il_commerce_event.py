import frappe
from frappe.model.document import Document

class ILCommerceEvent(Document):
    def validate(self):
        if not self.flags.saas_service:frappe.throw("Use the authorized service",frappe.PermissionError)
    def on_trash(self):
        frappe.throw("Audit records cannot be deleted",frappe.PermissionError)
