import frappe
from frappe.model.document import Document

class ILStudentCountPolicy(Document):
    def validate(self):
        if not self.flags.student_count_service:
            frappe.throw("Use the student-count service.", frappe.PermissionError)
