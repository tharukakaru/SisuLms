import frappe
from frappe.model.document import Document
class ILUsageInvoice(Document):
    def validate(self):
        if not self.flags.usage_service:
            frappe.throw('Use the usage billing service',frappe.PermissionError)
        old=self.get_doc_before_save()
        if old and old.issued_at:
            for key in ('subscription','source_invoice','period_key','period_start','period_end','due_at','plan','unit_rate','quantity','amount_lkr','student_snapshot','issued_at'):
                if str(old.get(key)) != str(self.get(key)):
                    frappe.throw('Issued invoice snapshots are immutable; use an audited adjustment')
    def on_trash(self):
        frappe.throw('Financial records cannot be deleted',frappe.PermissionError)
