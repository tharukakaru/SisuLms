from frappe.model.document import Document
import frappe

class ILProvisioningJob(Document):
    def validate(self):
        if not self.flags.saas_service:
            frappe.throw("Use the authorized SaaS service", frappe.PermissionError)

        previous = self.get_doc_before_save()

        if previous and previous.status == "retired":
            frappe.throw(
                "Retired provisioning jobs cannot be modified",
                frappe.PermissionError
            )

        if frappe.conf.get("il_control_plane") and self.organization:
            org = frappe.get_doc(
                "IL Organization", self.organization, for_update=True
            )

            if org.get("removal_status") and not org.get("retired"):
                frappe.throw("Website removal is pending; provisioning is locked", frappe.PermissionError)

            if org.get("retired"):
                if self.is_new() or self.status != "retired":
                    frappe.throw(
                        "Provisioning unavailable for retired organizations",
                        frappe.PermissionError
                    )
            elif self.status == "retired":
                frappe.throw(
                    "Organization must be retired first",
                    frappe.PermissionError
                )
    def on_trash(self):
        frappe.throw("SaaS records require reviewed retention; direct deletion disabled", frappe.PermissionError)
