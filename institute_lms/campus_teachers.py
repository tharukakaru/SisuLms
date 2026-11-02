"""Membership synchronization after an authorized teacher affiliation decision."""
import frappe
from frappe.model.naming import make_autoname
from .campus_context import enabled


def sync(relationship, institute, status):
    if not enabled() or status not in ('Active', 'Left', 'Removed'):
        return
    # Serialize against student registration and another teacher approval.
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE', (relationship.user,))
    row = frappe.db.get_value('IL Member', {'user': relationship.user, 'institute': institute},
                              ['name', 'role'], as_dict=True)
    if row:
        if row.role != 'Teacher':
            frappe.throw('This account has a different role in the institute. Ask an administrator to review it.', frappe.PermissionError)
        member = frappe.get_doc('IL Member', row.name)
        member.active = int(status == 'Active')
        member.save(ignore_permissions=True)
        return
    if status != 'Active':
        return
    profile = frappe.db.get_value('IL Public Profile',
        {'user': relationship.user, 'kind': 'Teacher', 'status': 'Verified'}, 'display_name')
    if not profile:
        from .teacher_identity import eligible
        if eligible(relationship.user):
            profile=frappe.db.get_value('IL Public Profile',{'user':relationship.user,'kind':'Teacher'},'display_name')
    if not profile or not frappe.db.get_value('User', relationship.user, 'enabled'):
        frappe.throw('An active, verified teacher account is required.', frappe.PermissionError)
    code = str(frappe.db.get_value('IL Institute', institute, 'code') or '')
    if not code or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-' for c in code):
        frappe.throw('Institute setup needs administrator review.', frappe.PermissionError)
    member = frappe.get_doc({'doctype': 'IL Member', 'institute': institute,
        'user': relationship.user, 'role': 'Teacher', 'full_name': profile,
        'active': 1, 'language': 'en', 'email_opt_in': 0, 'whatsapp_opt_in': 0})
    member.insert(ignore_permissions=True, set_name=make_autoname('TC-' + code + '-.####'))
    # Same request transaction as the relationship. Never changes global User roles,
    # password, subscription, other memberships or previously revoked assignments.
