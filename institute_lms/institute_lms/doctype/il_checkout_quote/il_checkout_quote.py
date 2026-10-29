import frappe
from frappe.model.document import Document

class ILCheckoutQuote(Document):
    def validate(self):
        if not self.flags.pricing_service: frappe.throw('Use the authorized service API', frappe.PermissionError)
        previous = self.get_doc_before_save()
        if previous and any(previous.get(k) != self.get(k) for k in ('customer', 'assignment', 'product', 'currency', 'period', 'total_minor', 'breakdown', 'tenant_id', 'plan_snapshot', 'expires_at')):
            frappe.throw('Payment identity and quote snapshots are immutable')
    def on_trash(self):
        frappe.throw('Financial and assessment records must be retained', frappe.PermissionError)
