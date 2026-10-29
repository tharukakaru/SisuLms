from frappe.model.document import Document
import frappe

class ILPaymentAttempt(Document):
    def validate(self):
        if not self.flags.saas_service: frappe.throw("Use the authorized SaaS service", frappe.PermissionError)
        previous = self.get_doc_before_save()
        if previous and any(previous.get(k) != self.get(k) for k in ('attempt_id', 'quote', 'tenant_id', 'amount_minor', 'currency', 'mode', 'request_key', 'request', 'snapshot')):
            frappe.throw('Payment identity and quote snapshots are immutable')
    def on_trash(self):
        frappe.throw("SaaS records require reviewed retention; direct deletion disabled", frappe.PermissionError)
