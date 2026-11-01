from frappe.model.document import Document
import frappe

class ILWhatsAppReceipt(Document):
    def validate(self):
        if not self.flags.whatsapp_service:
            frappe.throw("Use the authenticated webhook service", frappe.PermissionError)
