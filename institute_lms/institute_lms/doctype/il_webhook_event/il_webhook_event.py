from frappe.model.document import Document
import frappe

class ILWebhookEvent(Document):
    def validate(self):
        if not self.flags.saas_service: frappe.throw("Use the authorized SaaS service", frappe.PermissionError)
        if not self.is_new(): frappe.throw("Immutable audit/ledger record")
    def on_trash(self):
        frappe.throw("SaaS records require reviewed retention; direct deletion disabled", frappe.PermissionError)
