import frappe
from frappe.model.document import Document


class ILOwnerAccess(Document):
    def validate(self):
        if not self.flags.get('owner_access_service'):
            frappe.throw('Use the primary-owner access management service', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Revoke access instead of deleting the audit record', frappe.PermissionError)
