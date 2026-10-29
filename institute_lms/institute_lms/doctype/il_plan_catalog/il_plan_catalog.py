import frappe
from frappe.model.document import Document
class ILPlanCatalog(Document):
    def validate(self):
        if not self.flags.plan_catalog_service or self.name!='current':frappe.throw('Use the owner plan editor',frappe.PermissionError)
    def on_trash(self):frappe.throw('Plan history cannot be deleted',frappe.PermissionError)
