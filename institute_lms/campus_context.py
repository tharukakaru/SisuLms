"""Opt-in shared-campus context. Disabled until the full tenancy audit is complete.

An institute slug or client-selected role is never authorization. Every request
revalidates membership, so revocations apply to already-open sessions.
"""
import frappe

SESSION_KEY = 'il_active_institute'


def enabled():
    return frappe.conf.get('il_shared_campus_enabled') == 1 and not frappe.conf.get('il_control_plane')


def require_user():
    if not enabled():
        frappe.throw('Shared campus is not enabled.', frappe.PermissionError)
    user = frappe.session.user
    if user in ('Guest', 'Administrator') or not frappe.db.get_value('User', user, 'enabled'):
        frappe.throw('Sign in with an active campus account.', frappe.PermissionError)
    return user


def membership(institute):
    user = require_user()
    if not isinstance(institute, str) or not institute or len(institute) > 140:
        frappe.throw('Choose an institute you have joined.', frappe.PermissionError)
    member = frappe.db.get_value('IL Member', {
        'institute': institute, 'user': user, 'active': 1,
    }, ['name', 'role', 'institute'], as_dict=True)
    if not member or member.role not in ('Student', 'Teacher', 'Admin'):
        frappe.throw('This institute is not available to your account.', frappe.PermissionError)
    return member


def selected_institute():
    # Mobile tokens retain their own fixed, validated institute context.
    override = getattr(frappe.local, 'student_request_institute', None)
    if override:
        return override
    if getattr(frappe.local, 'il_mobile_session', None):
        return getattr(frappe.local, 'il_mobile_institute', None)
    return frappe.session.data.get(SESSION_KEY)


def save_selection(institute):
    mobile = getattr(frappe.local, 'il_mobile_session', None)
    if mobile:
        doc = frappe.get_doc('IL Mobile Session', mobile)
        if doc.user != frappe.session.user or doc.revoked:
            frappe.throw('Mobile session unavailable.', frappe.PermissionError)
        frappe.db.set_value('IL Mobile Session', mobile, 'institute', institute)
        frappe.local.il_mobile_institute = institute
    else:
        if institute:
            frappe.session.data[SESSION_KEY] = institute
        else:
            frappe.session.data.pop(SESSION_KEY, None)
        frappe.local.session_obj.update(force=True)


def current_institute():
    require_user()
    selected = getattr(frappe.local,'student_request_institute',None) or selected_institute()
    if not selected:
        frappe.throw('Choose an institute to continue.', frappe.PermissionError)
    membership(selected)
    return frappe.get_doc('IL Institute', selected)


@frappe.whitelist(methods=['GET'])
def choices():
    user = require_user()
    members = frappe.get_all('IL Member', filters={'user': user, 'active': 1},
                             fields=['name', 'institute', 'role'], limit_page_length=100)
    result = []
    for member in members:
        if member.role not in ('Student', 'Teacher', 'Admin'):
            continue
        title = frappe.db.get_value('IL Institute', member.institute, 'title')
        if title:
            result.append({'institute': member.institute, 'title': title, 'role': member.role, 'student_number': member.name if member.role=='Student' else None})
    selected = selected_institute()
    return {'institutes': result, 'selected': selected if any(r['institute'] == selected for r in result) else None}


@frappe.whitelist(methods=['POST'])
def clear():
    require_user()
    save_selection(None)
    return {'selected': None, 'reload_required': True}


@frappe.whitelist(methods=['POST'])
def select(institute):
    member = membership(institute)
    save_selection(member.institute)
    return {'selected': member.institute, 'role': member.role, 'reload_required': True}
