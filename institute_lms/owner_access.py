"""Server-authoritative delegated owner access.

Levels: the primary owner (site config), the system Administrator account and
delegates with access_level "Administrator" have full authority and may manage
access. Delegates with access_level "Admin" can run the platform but can never
create, promote or remove administrators.
"""
import frappe
from .message_templates import sendmail


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


LEVELS = ('Admin', 'Administrator')


def access_level(user=None):
    """'Primary', 'Administrator', 'Admin' or None. Rechecked from the DB on every request."""
    user = user or frappe.session.user
    if not is_owner(user):
        return None
    if str(user).lower() == primary_email():
        return 'Primary'
    if user == 'Administrator':
        # The system superuser acts with primary-owner authority.
        return 'Primary'
    level = frappe.db.get_value('IL Owner Access', {'user': user, 'enabled': 1}, 'access_level')
    return 'Administrator' if level == 'Administrator' else 'Admin'


def can_manage(user=None):
    return access_level(user) in ('Primary', 'Administrator')


def require_manager():
    if not can_manage():
        frappe.throw('Only an Administrator can manage Platform admin access', frappe.PermissionError)


# Backwards-compatible name used by older callers.
require_primary = require_manager


def protected(email):
    return email == primary_email() or email == 'administrator'


def target_level(email):
    level = frappe.db.get_value('IL Owner Access', {'user': email}, 'access_level')
    return 'Administrator' if level == 'Administrator' else 'Admin'


def permissions_for(email, level=None):
    """What the signed-in manager may do to another account.
    Primary: delete anyone, promote and demote. Administrator: delete Admins and promote Admins only."""
    me = access_level()
    email = str(email or '').lower()
    if me not in ('Primary', 'Administrator') or protected(email) or email == frappe.session.user.lower():
        return {'can_remove': False, 'can_promote': False, 'can_demote': False}
    level = level or target_level(email)
    primary = me == 'Primary'
    return {'can_remove': primary or level == 'Admin',
            'can_promote': level == 'Admin',
            'can_demote': primary and level == 'Administrator'}


@frappe.whitelist(methods=['GET'])
def access_list():
    from .registration import require_owner
    require_owner()
    manage = can_manage()
    members = frappe.get_all('IL Owner Access', fields=['user', 'full_name', 'access_level', 'enabled', 'phone',
                             'granted_by', 'accepted_at', 'creation', 'modified'], order_by='creation asc')
    for m in members:
        m['access_level'] = m.get('access_level') or 'Admin'
        m['phone'] = mask_phone(m.get('phone')) if manage else None
        m['protected'] = protected(str(m['user']).lower())
        if m['protected']:
            m['access_level'] = 'Administrator'
        m.update(permissions_for(m['user'], m['access_level']) if m['enabled'] else
                 {'can_remove': False, 'can_promote': False, 'can_demote': False})
        m['is_me'] = m['user'] == frappe.session.user
    invites = []
    if manage:
        invites = frappe.get_all('IL Admin Invite', filters={'status': 'Pending'},
                                 fields=['name', 'full_name', 'email', 'access_level', 'expires_at', 'invited_by', 'creation'],
                                 order_by='creation desc')
        from frappe.utils import now_datetime, get_datetime
        for i in invites:
            i['expired'] = get_datetime(i['expires_at']) <= now_datetime()
    return {'primary': primary_email(), 'can_manage': manage, 'my_level': access_level(),
            'is_primary': access_level() == 'Primary',
            'me': frappe.session.user, 'members': members if manage else [], 'invites': invites}


def mask_phone(phone):
    phone = str(phone or '')
    return phone[:3] + '•' * max(0, len(phone) - 6) + phone[-3:] if len(phone) > 6 else phone


@frappe.whitelist(methods=['POST'])
def add(email, reason):
    require_manager()
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
    queue_setup_email(user)
    audit('Platform owner access granted', email, doc.reason)
    return {'status': 'Access granted; password setup email queued'}


@frappe.whitelist(methods=['POST'])
def remove(email, reason):
    require_manager()
    email = str(email or '').strip().lower()
    if protected(email):
        frappe.throw('The primary owner and the system Administrator cannot be removed here')
    if email == frappe.session.user.lower():
        frappe.throw('You cannot remove your own access. Ask another Administrator.')
    if not permissions_for(email)['can_remove']:
        frappe.throw('Only the primary owner can delete an Administrator. You can delete Admin accounts.', frappe.PermissionError)
    from .wallet import audit
    if not str(reason or '').strip():
        frappe.throw('Enter a reason for removing access')
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE', (primary_email(),))
    name = frappe.db.get_value('IL Owner Access', {'user': email}, 'name')
    if not name:
        frappe.throw('Platform owner access record not found')
    doc = frappe.get_doc('IL Owner Access', name)
    doc.enabled = 0
    doc.reason = str(reason).strip()[:1000]
    doc.flags.owner_access_service = True
    doc.save(ignore_permissions=True)
    # Every owner request rechecks the DB, so open sessions lose privilege immediately.
    audit('Platform owner access removed', email, doc.reason)
    return {'status': 'Admin deleted: access removed immediately (the login account is kept for the audit history)'}


@frappe.whitelist(methods=['POST'])
def set_level(email, level, reason=''):
    """Give or take back full authority (Administrator) separately from Admin access."""
    require_manager()
    email = str(email or '').strip().lower()
    if level not in LEVELS:
        frappe.throw('Choose Admin or Administrator')
    if protected(email) or email == frappe.session.user.lower():
        frappe.throw('The access level of this account cannot be changed here')
    allowed = permissions_for(email)
    if level == 'Administrator' and not allowed['can_promote'] or level == 'Admin' and not allowed['can_demote']:
        frappe.throw('Only the primary owner can take full authority away from an Administrator', frappe.PermissionError)
    name = frappe.db.get_value('IL Owner Access', {'user': email, 'enabled': 1}, 'name')
    if not name:
        frappe.throw('Active admin access not found')
    from .wallet import audit
    doc = frappe.get_doc('IL Owner Access', name)
    if doc.access_level == level:
        return {'status': 'No change'}
    doc.access_level = level
    doc.reason = (str(reason or '').strip() or f'Access level changed to {level}')[:1000]
    doc.flags.owner_access_service = True
    doc.save(ignore_permissions=True)
    audit('Platform access level changed', email, f'{level}: {doc.reason}')
    return {'status': 'Full authority granted' if level == 'Administrator' else 'Changed to Admin (no access management)'}


def queue_setup_email(user):
    """Queue with the configured sender; support both deployed Frappe APIs."""
    from html import escape
    if not frappe.db.exists('Email Account', {'enable_outgoing': 1}):
        frappe.throw('Configure outgoing email before inviting a Platform owner.')
    reset = getattr(user, '_reset_password', None) or getattr(user, 'reset_password', None)
    if not callable(reset):
        frappe.throw('Password setup is unavailable. Contact the hosting operator.')
    validate = getattr(user, 'validate_reset_password', None)
    if callable(validate): validate()
    link = reset(send_email=False).replace('/update-password?', '/sisu_password?', 1)
    sendmail(frappe, recipients=[user.name], subject='Your SISU Platform owner access',
        message='<p>You have been invited to manage SISU.</p><p><a href="'+escape(link, quote=True)+'">Set your password and sign in</a></p>',
        delayed=True, redact_message_after_send=True)
