from frappe.model.document import Document
import frappe


class ILOrganization(Document):
    def validate(self):
        if not self.flags.saas_service:
            frappe.throw(
                "Use the authorized SaaS service",
                frappe.PermissionError
            )

        previous = self.get_doc_before_save()

        if previous and previous.get("retired"):
            frappe.throw(
                "Retired organizations cannot be modified or reactivated",
                frappe.PermissionError
            )

        if previous and previous.get("removal_status") and not self.flags.get("tenant_retirement"):
            if self.enabled or any(self.get(k) != previous.get(k) for k in
                    ("site_hostname", "institute_code", "custom_domain", "admin_contact", "plan")):
                frappe.throw("Removal is pending; organization identity and activation are locked", frappe.PermissionError)

        if self.get("retired"):
            if not previous or not self.flags.get("tenant_retirement"):
                frappe.throw(
                    "Use the authorized tenant retirement service",
                    frappe.PermissionError
                )

            if self.enabled:
                frappe.throw("Retired organizations must be disabled")

            for field in (
                "retired_at",
                "retired_by",
                "retirement_reason",
                "original_site_hostname",
                "original_institute_code"
            ):
                if not self.get(field):
                    frappe.throw("Missing retirement metadata: " + field)

    def on_trash(self):
        frappe.throw(
            "SaaS records require reviewed retention; direct deletion disabled",
            frappe.PermissionError
        )
