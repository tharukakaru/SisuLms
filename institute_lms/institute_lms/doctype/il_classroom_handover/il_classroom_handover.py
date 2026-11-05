import frappe
from frappe.model.document import Document


class ILClassroomHandover(Document):
    def validate(self):
        if not self.flags.classroom_handover_service:
            frappe.throw('Use the classroom handover service', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Handover decisions must be retained', frappe.PermissionError)
