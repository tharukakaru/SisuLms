import frappe
from frappe.model.document import Document
class ILWorkspaceRecord(Document):
    def validate(self):
        if not self.flags.workspace_service:frappe.throw('Use the authorized workspace service',frappe.PermissionError)
    def on_trash(self):frappe.throw('Archive workspace records instead of deleting them')
