import frappe
from frappe.model.document import Document

class ILStudentCountBill(Document):
    def validate(self):
        if not self.flags.student_count_service:
            frappe.throw("Use the student-count service.", frappe.PermissionError)
        old=self.get_doc_before_save()
        if old:
            for key in ("period_key","subscription","institute","month","quantity","unit_minor","amount_minor","student_snapshot"):
                if str(old.get(key))!=str(self.get(key)):
                    frappe.throw("Issued student counts and rates cannot be changed.")
    def on_trash(self):
        frappe.throw("Financial records cannot be deleted.",frappe.PermissionError)
