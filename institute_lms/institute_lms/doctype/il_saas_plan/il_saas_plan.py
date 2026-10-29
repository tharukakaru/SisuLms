from frappe.model.document import Document
import frappe

class ILSaaSPlan(Document):
    def validate(self):
        if not self.flags.saas_service: frappe.throw("Use the authorized SaaS service", frappe.PermissionError)
    def on_trash(self):
        frappe.throw("SaaS records require reviewed retention; direct deletion disabled", frappe.PermissionError)
