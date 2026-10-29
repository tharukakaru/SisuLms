import frappe
from frappe.model.document import Document

class ILDeliveryOffer(Document):
    def validate(self):
        if not self.flags.delivery_service:
            frappe.throw("Use the SISU delivery service", frappe.PermissionError)
    def on_trash(self):
        frappe.throw("Delivery records cannot be deleted", frappe.PermissionError)
