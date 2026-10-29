from frappe.model.document import Document
import frappe

class ILPaperGenerationJob(Document):
    def validate(self):
        if not self.flags.saas_service: frappe.throw("Use the authorized SISU service", frappe.PermissionError)
    def on_trash(self):
        frappe.throw("Use reviewed retention; direct removal is disabled", frappe.PermissionError)
