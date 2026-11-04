"""Explicit personal workspace scope; never infer ownership from a title."""
import frappe


def workspace(provider):
    target = getattr(provider, 'workspace', None)
    if provider.kind != 'Teacher' or provider.status != 'Verified' or not target:
        return None
    if frappe.db.exists('IL Public Profile', {'kind': 'Institute', 'workspace': target}):
        return None
    staff = frappe.get_all('IL Member', filters={'institute': target, 'active': 1,
        'role': ['in', ['Teacher', 'Admin']]}, fields=['user', 'role'], limit_page_length=0)
    if not staff or any(m.user != provider.user or m.role != 'Teacher' for m in staff):
        return None
    return target


def register_member(provider, student, phone, number):
    """Add a verified student to only the teacher's explicit personal workspace."""
    target = workspace(provider)
    if not target:
        frappe.throw('This teacher’s workspace needs review.', frappe.PermissionError)
    previous = frappe.db.get_value('IL Member', {'institute': target, 'user': student.user},
        ['name', 'role', 'active'], as_dict=True)
    if previous:
        if previous.role != 'Student' or not previous.active:
            frappe.throw('Your existing membership needs teacher review.', frappe.PermissionError)
        return previous.name
    member = frappe.get_doc({'doctype': 'IL Member', 'institute': target, 'user': student.user,
        'role': 'Student', 'full_name': student.display_name, 'phone': phone, 'language': 'en',
        'active': 1, 'whatsapp_opt_in': 0, 'email_opt_in': 0})
    from .membership_write import authorized_insert
    with authorized_insert(member):
        member.insert(ignore_permissions=True, set_name=number)
    return member.name
