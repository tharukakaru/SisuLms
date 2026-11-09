from frappe.model.document import Document
import frappe

class ILProgrammeProgress(Document):
    def validate(self):
        if not self.flags.programme_service:
            frappe.throw("Use programme completion", frappe.PermissionError)
