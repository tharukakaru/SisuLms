import frappe
from frappe.model.document import Document


class ILClassroomQuiz(Document):
    def validate(self):
        if not self.flags.classroom_quiz_service:
            frappe.throw('Use the authorized classroom quiz service', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Assessment records must be retained', frappe.PermissionError)
