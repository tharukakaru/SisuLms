"""Public learning identifiers, distinct from private account and membership keys."""
from frappe.model.naming import make_autoname


def issue_lms_id(kind):
    prefix = {"Student": "ST", "Teacher": "TC", "Institute": "IN"}[kind]
    # Frappe's naming series allocator serializes concurrent allocations.
    return make_autoname("SISU-" + prefix + "-.######")
