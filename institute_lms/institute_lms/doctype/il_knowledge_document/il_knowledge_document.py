from frappe.model.document import Document
import frappe

class ILKnowledgeDocument(Document):
    def validate(self):
        if not self.flags.ai_service:frappe.throw("Use the authorized AI service",frappe.PermissionError)
    def on_trash(self):
        if not self.flags.ai_retention:frappe.throw("Use AI retention services",frappe.PermissionError)
