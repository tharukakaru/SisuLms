"""Complete a verified provider's own workspace; never join an institute by choice."""
import hashlib
import frappe


@frappe.whitelist(methods=['POST'])
def continue_to_workspace():
    from .campus_context import require_user, SESSION_KEY
    from .onboarding_navigation import workspace_registration
    user = require_user()
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE', (user,))
    name = frappe.db.get_value('IL Public Profile', {'user': user}, 'name')
    if not name:
        frappe.throw('Complete your profile first.')
    profile = frappe.get_doc('IL Public Profile', name)
    if profile.kind not in ('Teacher', 'Institute'):
        frappe.throw('Provider account required.', frappe.PermissionError)
    rows = frappe.get_all('IL Registration Request', filters={
        'email': user, 'status': 'Approved', 'email_verified': 1,
        'account_type': 'Institute' if profile.kind == 'Institute' else 'Individual Teacher',
    }, fields=['details'], order_by='creation desc', limit_page_length=10)
    phone = frappe.db.get_value('IL Verified Phone', {'user': user}, ['phone', 'verified_at'], as_dict=True)
    if (not workspace_registration(rows, user, profile.kind) or profile.status not in ('Pending', 'Verified')
            or not phone or not phone.phone or not phone.verified_at):
        frappe.throw('Complete your verified profile first.', frappe.PermissionError)
    if profile.kind == 'Institute' and profile.status != 'Verified':
        frappe.throw('This existing institute profile still requires review.', frappe.PermissionError)
    role = 'Admin' if profile.kind == 'Institute' else 'Teacher'
    if profile.workspace:
        inst = frappe.get_doc('IL Institute', profile.workspace)
        member = frappe.db.get_value('IL Member', {'institute': inst.name, 'user': user}, ['name', 'role', 'active'], as_dict=True)
        if not member or member.role != role or not member.active:
            frappe.throw('Your existing workspace requires administrator review.', frappe.PermissionError)
    else:
        from .campus_provisioning import institute_insert
        from .membership_write import authorized_insert
        from .profiles import write
        # Deterministic code and user lock prevent duplicate workspaces on retries.
        code = 'P' + hashlib.sha256(user.encode()).hexdigest()[:11].upper()
        if frappe.db.exists('IL Institute', {'code': code}):
            frappe.throw('Workspace setup needs administrator review.')
        inst = frappe.get_doc({'doctype': 'IL Institute', 'code': code,
            'title': profile.display_name, 'language': 'en', 'billing_day': 1})
        with institute_insert(inst):
            inst.insert(ignore_permissions=True)
        profile.workspace = inst.name
        write(profile)  # Preserve public endorsement status.
        member = frappe.get_doc({'doctype': 'IL Member', 'institute': inst.name,
            'user': user, 'full_name': profile.display_name, 'role': role, 'active': 1, 'language': 'en'})
        with authorized_insert(member):
            member.insert(ignore_permissions=True)
        from .account_billing import account, save
        subscription = account(inst, member, create=True, lock=True)
        subscription.onboarding_payment_required = 1
        save(subscription)  # No free access or trial activation from a browser action.
    frappe.session.data[SESSION_KEY] = inst.name
    frappe.local.session_obj.update(force=True)
    return {'ready': True}
