import frappe
from frappe.model.document import Document


class ILAdminInvite(Document):
    def validate(self):
        if not self.flags.get('admin_invite_service'):
            frappe.throw('Use the Admin access invitation service', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Cancel the invitation instead of deleting the audit record', frappe.PermissionError)
