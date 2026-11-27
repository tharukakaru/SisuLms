from frappe.model.document import Document
import frappe

class ILSubscription(Document):
    def validate(self):
        if not self.flags.saas_service:
            frappe.throw("Use the authorized SaaS service", frappe.PermissionError)

        if frappe.conf.get("il_control_plane") and self.tenant_id:
            org = frappe.get_doc(
                "IL Organization", self.tenant_id, for_update=True
            )

            if org.get("retired"):
                if self.enabled or self.state != "cancelled":
                    frappe.throw(
                        "Retired subscriptions must remain cancelled and disabled",
                        frappe.PermissionError
                    )
    def on_trash(self):
        frappe.throw("SaaS records require reviewed retention; direct deletion disabled", frappe.PermissionError)
