"""Assign permanent IDs to existing profiles after the schema is synced."""
import frappe
from institute_lms.identity_numbers import issue_lms_id


def execute():
    for row in frappe.get_all("IL Public Profile", fields=["name", "kind", "lms_id"], order_by="creation asc"):
        if not row.lms_id:
            frappe.db.set_value("IL Public Profile", row.name, "lms_id", issue_lms_id(row.kind), update_modified=False)
