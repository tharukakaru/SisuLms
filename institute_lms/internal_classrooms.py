"""Internal classroom creation still requires real local membership and teacher consent."""
import frappe
from .api import scoped


def validate_admin(inst):
    user = frappe.session.user
    if user == 'Guest' or not frappe.db.get_value('User', user, 'enabled') or not frappe.db.exists(
        'IL Member', {'institute': inst.name, 'user': user, 'role': 'Admin', 'active': 1}):
        frappe.throw('Active institute administrator membership required', frappe.PermissionError)


def validate_request(inst, data):
    validate_admin(inst)
    if data.get('name'):
        frappe.throw('Use classroom management to edit an existing classroom')
    if data.get('published') not in (None, False, 0, '0') or data.get('public_provider'):
        frappe.throw('Internal classrooms cannot publish under a public provider', frappe.PermissionError)
    for field in ('institute', 'administrator', 'owner_user', 'owner_type', 'user'):
        if field in data:
            frappe.throw('Classroom ownership is resolved from your session', frappe.PermissionError)


def teacher_for(inst, name):
    teacher = scoped('IL Member', name, inst)
    if teacher.role != 'Teacher' or not teacher.active:
        frappe.throw('Select an active teacher in this institute', frappe.PermissionError)
    # A directory-backed institute's teacher approval is consent, not a publishing
    # entitlement for the administrator. Retain it without linking the classroom.
    if not teacher_affiliated(inst.name, teacher.user):
        frappe.throw('The assigned teacher needs approved institute membership', frappe.PermissionError)
    return teacher


def teacher_affiliated(institute, user):
    profiles = frappe.get_all('IL Public Profile', filters={'workspace': institute,
        'kind': 'Institute'}, pluck='name')
    # Sites without directory profiles use their existing active local IL Member.
    return not profiles or bool(frappe.db.exists('IL Profile Relationship', {'profile': ['in', profiles],
        'user': user, 'kind': 'Teacher membership', 'status': 'Active'}))
