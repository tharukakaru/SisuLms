"""Server-authoritative delegated owner access; only the primary can manage it."""
import frappe


def primary_email():
    return str(frappe.conf.get('il_owner_email') or '').strip().lower()


def is_owner(user=None):
    user = user or frappe.session.user
    if not user or user == 'Guest' or not frappe.conf.get('il_owner_provisioned'):
        return False
    if not frappe.db.get_value('User', user, 'enabled'):
        return False
    if str(user).lower() == primary_email():
        return True
    return bool(frappe.db.exists('IL Owner Access', {'user': user, 'enabled': 1}))


def require_primary():
    if not is_owner() or frappe.session.user.lower() != primary_email():
        frappe.throw('Only the primary owner can manage Super Admin access', frappe.PermissionError)


@frappe.whitelist(methods=['GET'])
def access_list():
    from .registration import require_owner
    require_owner()
    return {'primary': primary_email(), 'can_manage': frappe.session.user.lower() == primary_email(),
            'members': frappe.get_all('IL Owner Access', fields=['user', 'enabled', 'granted_by', 'modified'], order_by='creation asc')}


@frappe.whitelist(methods=['POST'])
def add(email, reason):
    require_primary()
    from frappe.utils import validate_email_address
    from .wallet import audit
    email = str(email or '').strip().lower()
    validate_email_address(email, throw=True)
    if email == primary_email():
        frappe.throw('The primary owner already has access')
    if not str(reason or '').strip():
        frappe.throw('Enter a reason for granting access')
    # Serialize membership edits, including concurrent invitations for one address.
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE', (primary_email(),))
    if frappe.db.exists('IL Member', {'user': email}) or frappe.db.exists('IL Public Profile', {'user': email}):
        frappe.throw('Use a dedicated administrative account, separate from a learner/provider profile')
    if not frappe.db.exists('User', email):
        user = frappe.get_doc({'doctype': 'User', 'email': email, 'first_name': email.split('@')[0],
                              'enabled': 1, 'user_type': 'Website User', 'send_welcome_email': 0}).insert(ignore_permissions=True)
    else:
        user = frappe.get_doc('User', email)
        if not user.enabled:
            frappe.throw('This user is disabled. Ask the site operator to review the account first')
    name = frappe.db.get_value('IL Owner Access', {'user': email}, 'name')
    if name:
        doc = frappe.get_doc('IL Owner Access', name)
        if doc.enabled:
            return {'status': 'Already active'}
    else:
        doc = frappe.get_doc({'doctype': 'IL Owner Access', 'user': email})
    doc.enabled = 1
    doc.granted_by = frappe.session.user
    doc.reason = str(reason).strip()[:1000]
    doc.flags.owner_access_service = True
    doc.save(ignore_permissions=True)
    # Recipient must authenticate normally; email allowlisting never logs them in.
    user.reset_password(send_email=True)
    audit('Super Admin access granted', email, doc.reason)
    return {'status': 'Access granted; password setup email queued'}


@frappe.whitelist(methods=['POST'])
def remove(email, reason):
    require_primary()
    from .wallet import audit
    email = str(email or '').strip().lower()
    if email == primary_email():
        frappe.throw('The primary owner cannot be removed here')
    if not str(reason or '').strip():
        frappe.throw('Enter a reason for removing access')
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE', (primary_email(),))
    name = frappe.db.get_value('IL Owner Access', {'user': email}, 'name')
    if not name:
        frappe.throw('Super Admin access record not found')
    doc = frappe.get_doc('IL Owner Access', name)
    doc.enabled = 0
    doc.reason = str(reason).strip()[:1000]
    doc.flags.owner_access_service = True
    doc.save(ignore_permissions=True)
    # Every owner request rechecks the DB, so open sessions lose privilege immediately.
    audit('Super Admin access removed', email, doc.reason)
    return {'status': 'Super Admin access removed; user account preserved'}
