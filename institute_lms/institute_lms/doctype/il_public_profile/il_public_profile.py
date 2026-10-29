from frappe.model.document import Document
import frappe

class ILPublicProfile(Document):
    def validate(self):
        if not self.flags.community_service: frappe.throw("Use the profile API", frappe.PermissionError)
        previous = self.get_doc_before_save()
        if previous and previous.get("lms_id"):
            if self.lms_id != previous.lms_id:
                frappe.throw("Your SISU LMS ID is permanent")
        else:
            from institute_lms.identity_numbers import issue_lms_id
            self.lms_id = issue_lms_id(self.kind)
