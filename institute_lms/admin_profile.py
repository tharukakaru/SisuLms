"""Self-service profile and password changes for platform administrators."""
import frappe


def require_admin():
    from .owner_access import is_owner
    if not frappe.conf.get('il_control_plane') or not is_owner(frappe.session.user):
        frappe.throw('Sign in as a platform administrator to manage your profile.', frappe.PermissionError)
    return frappe.session.user


@frappe.whitelist(methods=['GET'])
def current():
    user = require_admin()
    from .owner_access import access_level, mask_phone
    from .admin_mfa import required
    from frappe.twofactor import should_run_2fa
    doc = frappe.get_doc('User', user)
    return {'name': doc.full_name or doc.first_name or user, 'email': doc.email or user,
            'level': access_level(user), 'phone_hint': mask_phone(doc.mobile_no or doc.phone),
            'sms_mfa': bool(required(user) and should_run_2fa(user))}


@frappe.whitelist(methods=['POST'])
def change_password(current_password, new_password, confirm_password):
    # The target is always the authenticated user; no email/user argument is accepted.
    user = require_admin()
    from .admin_invites import throttle
    throttle('mfa-password-change:' + user, 900, 5)
    if not isinstance(current_password, str) or not current_password or len(current_password) > 128:
        frappe.throw('Enter your current password.')
    if not isinstance(new_password, str) or not 12 <= len(new_password) <= 128:
        frappe.throw('Use a new password with 12 to 128 characters.')
    if new_password != confirm_password:
        frappe.throw('The new passwords do not match.')
    from frappe.utils.password import check_password, update_password
    check_password(user, current_password, delete_tracker_cache=False)
    from frappe.core.doctype.user.user import test_password_strength, is_password_reused
    if is_password_reused(user, new_password):
        frappe.throw('Choose a different password from your current password.')
    result = test_password_strength(new_password) or {}
    feedback = result.get('feedback') or {}
    if feedback and not feedback.get('password_policy_validation_passed'):
        frappe.throw('Choose a stronger password. Use a longer, unique phrase and avoid names or common words.')
    frappe.get_doc('User', user).validate_reset_password()
    update_password(user, new_password, logout_all_sessions=True)
    from frappe.utils import today
    frappe.db.set_value('User', user, {'reset_password_key': '', 'last_password_reset_date': today()})
    # Do not call Frappe's web update_password endpoint: it logs in automatically,
    # which would bypass/reject the SMS challenge. Require a fresh normal MFA login.
    frappe.local.login_manager.logout()
    return {'redirect': '/login?redirect-to=/campus', 'changed': True}
