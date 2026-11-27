"""Opt-in personal teacher workspaces; affiliation and endorsement stay separate."""
import hashlib
import frappe


def enabled():
    from .signup_environment import unified_teacher_enabled
    return unified_teacher_enabled(getattr(frappe,'conf',{}))


def eligible(user):
    from .teacher_identity import eligible as identity_verified
    from .onboarding_navigation import profile_pending
    rows = frappe.get_all('IL Registration Request', filters={
        'email': user, 'account_type': 'Individual Teacher', 'status': 'Approved', 'email_verified': 1},
        fields=['details'], order_by='creation desc', limit_page_length=10)
    return bool(identity_verified(user) and rows and not profile_pending(rows))


def ensure(user):
    """No client-supplied role/workspace, no reactivation, no trial reset."""
    if not enabled() or user != frappe.session.user or user in ('Guest', 'Administrator'):
        frappe.throw('Teacher workspace unavailable.', frappe.PermissionError)
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE', (user,))
    if not eligible(user):
        frappe.throw('Complete your teacher profile and email/mobile verification first.', frappe.PermissionError)
    name = frappe.db.get_value('IL Public Profile', {'user': user, 'kind': 'Teacher'}, 'name')
    profile = frappe.get_doc('IL Public Profile', name)
    if profile.status not in ('Pending', 'Verified'):
        frappe.throw('Your profile needs administrator review.', frappe.PermissionError)
    if profile.workspace:
        # Preserve an existing workspace and all subscriptions. Never adopt an institute.
        if frappe.db.exists('IL Public Profile', {'kind': 'Institute', 'workspace': profile.workspace}):
            frappe.throw('Your personal workspace needs administrator review.', frappe.PermissionError)
        member = frappe.db.get_value('IL Member', {'institute': profile.workspace, 'user': user},
                                     ['name', 'role', 'active'], as_dict=True)
        staff = frappe.get_all('IL Member', filters={'institute': profile.workspace, 'active': 1,
            'role': ['in', ['Teacher', 'Admin']]}, fields=['user', 'role'])
        if (not member or member.role != 'Teacher' or not member.active
                or any(m.user != user or m.role != 'Teacher' for m in staff)):
            frappe.throw('Your existing workspace needs administrator review.', frappe.PermissionError)
        return profile.workspace
    code = 'T' + hashlib.sha256(user.encode()).hexdigest()[:11].upper()
    if frappe.db.exists('IL Institute', {'code': code}):
        frappe.throw('Workspace setup needs administrator review.', frappe.PermissionError)
    from .campus_provisioning import institute_insert
    from .membership_write import authorized_insert
    from .profiles import write
    institute = frappe.get_doc({'doctype': 'IL Institute', 'code': code,
        'title': profile.display_name + ' · My teaching space', 'language': 'en', 'billing_day': 1})
    with institute_insert(institute):
        institute.insert(ignore_permissions=True)
    member = frappe.get_doc({'doctype': 'IL Member', 'institute': institute.name,
        'user': user, 'role': 'Teacher', 'active': 1, 'full_name': profile.display_name,
        'phone': frappe.db.get_value('IL Verified Phone', {'user': user}, 'phone'),
        'language': 'en', 'email_opt_in': 0, 'whatsapp_opt_in': 0})
    with authorized_insert(member):
        member.insert(ignore_permissions=True)
    profile.workspace = institute.name
    write(profile)  # Keep Pending/Verified exactly as reviewed; never issue a badge/code.
    from .account_billing import account
    account(institute, member, create=True)  # Existing account is reused, including trial dates.
    return institute.name


@frappe.whitelist(methods=['POST'])
def open_workspace():
    from .campus_context import select
    workspace = ensure(frappe.session.user)
    return select(workspace)


def billing_context(inst, member):
    """The selected workspace pays for its own access; never borrow another plan."""
    from .account_billing import account, state
    from frappe.utils import get_datetime, now_datetime
    provider = frappe.db.get_value('IL Public Profile', {'workspace': inst.name, 'kind': 'Institute'},
                                   ['name', 'display_name'], as_dict=True)
    if provider:
        from .institute_coverage import sponsor
        coverage = sponsor(inst.name, member.user)
        name = frappe.db.get_value('IL Account Subscription', {'account_key': 'Institute:' + inst.name, 'role': 'Institute', 'institute': inst.name}, 'name')
        a = frappe.get_doc('IL Account Subscription', name) if name else None
        return {'kind': 'Institute', 'title': provider.display_name, 'plan': a.plan if a else '',
                'state': state(a)['state'] if a else 'Plan required', 'available': bool(coverage),
                'remaining_ms': None,
                'message': '' if coverage else 'Your institute’s plan is unavailable. Ask its administrator to renew, or switch to Personal.'}
    a = account(inst, member)
    s = state(a)
    remaining = max(0, int((get_datetime(a.trial_until) - now_datetime()).total_seconds() * 1000)) if s['state'] == 'Trial' else None
    return {'kind': 'Personal', 'title': 'Personal', 'plan': a.plan, **s, 'remaining_ms': remaining,
            'message': '' if s['available'] else 'Your trial period or paid plan has ended. Pay for a subscription to continue personal teaching.'}


@frappe.whitelist(methods=['GET'])
def summary():
    from .api import identity
    from .campus_context import require_user
    user = require_user()
    if not enabled():frappe.throw('Teacher workspaces are unavailable.', frappe.PermissionError)
    inst, member = identity()
    if member.role != 'Teacher':frappe.throw('Teacher account required.', frappe.PermissionError)
    personal = frappe.db.get_value('IL Public Profile', {'user': user, 'kind': 'Teacher'}, 'workspace')
    choices = []
    if personal and frappe.db.exists('IL Member', {'user': user, 'institute': personal, 'role': 'Teacher', 'active': 1}):
        choices.append({'institute': personal, 'title': 'Personal', 'kind': 'Personal', 'status': 'Active', 'locked': False})
    links = frappe.get_all('IL Profile Relationship', filters={'user': user, 'kind': 'Teacher membership',
        'status': ['in', ['Pending', 'Active']]}, fields=['name', 'profile', 'status'], order_by='creation asc', limit_page_length=100)
    for link in links:
        p = frappe.db.get_value('IL Public Profile', {'name': link.profile, 'kind': 'Institute'},
                               ['workspace', 'display_name', 'profile_image', 'status'], as_dict=True)
        if not p or not p.workspace:continue
        accepted = link.status == 'Active' and p.status == 'Verified' and bool(frappe.db.exists('IL Member',
            {'user': user, 'institute': p.workspace, 'role': 'Teacher', 'active': 1}))
        choices.append({'institute': p.workspace, 'title': p.display_name, 'image': p.profile_image, 'request': link.name if link.status == 'Pending' else None,
                        'kind': 'Institute', 'status': link.status if accepted or link.status == 'Pending' else 'Unavailable', 'locked': not accepted})
    return {'selected': inst.name, 'choices': choices, 'billing': billing_context(inst, member)}


@frappe.whitelist(methods=['POST'])
def cancel_request(request):
    """Withdraw only the caller's pending application, never an accepted membership."""
    from .campus_context import require_user
    from .profiles import write
    user = require_user()
    if not enabled() or not isinstance(request, str) or not frappe.db.exists('IL Profile Relationship',
        {'name': request, 'user': user, 'kind': 'Teacher membership'}):
        frappe.throw('Institute request unavailable.', frappe.PermissionError)
    # Same row lock as administrator acceptance; do not revoke a concurrent approval.
    frappe.db.sql('SELECT name FROM `tabIL Profile Relationship` WHERE name=%s FOR UPDATE', (request,))
    doc = frappe.get_doc('IL Profile Relationship', request)
    if doc.user != user or doc.kind != 'Teacher membership':
        frappe.throw('Institute request unavailable.', frappe.PermissionError)
    if doc.status == 'Left':return {'status': 'Cancelled'}
    if doc.status != 'Pending':
        frappe.throw('This request is no longer pending. Refresh your workspaces before continuing.')
    doc.status = 'Left'
    doc.reason = 'Application withdrawn by teacher'
    doc.reviewed_by = user
    write(doc)
    return {'status': 'Cancelled'}


RECOVERY_METHODS = frozenset({
    'institute_lms.invitations.list_invitations', 'institute_lms.invitations.respond',
    'institute_lms.api.bootstrap', 'institute_lms.full_api.capabilities',
    'institute_lms.teacher_workspace.summary', 'institute_lms.teacher_workspace.open_workspace', 'institute_lms.teacher_workspace.cancel_request',
    'institute_lms.campus_context.select', 'institute_lms.campus_context.choices', 'institute_lms.campus_context.clear',
    'institute_lms.portal_session.current', 'institute_lms.portal_policy.public',
    'institute_lms.classroom_handover.institute_plan', 'institute_lms.plan_catalog.public_catalog',
    'login', 'logout', 'frappe.auth.get_logged_user',
})


def enforce_request(method):
    """Keep shell/switching/billing usable, but block expired teaching APIs."""
    if not enabled() or frappe.session.user in ('Guest', 'Administrator'):return False
    from .campus_context import selected_institute
    selected = selected_institute()
    if not selected:
        selected = frappe.db.get_value('IL Public Profile', {'user': frappe.session.user, 'kind': 'Teacher'}, 'workspace')
    if not selected:return False
    member = frappe.db.get_value('IL Member', {'institute': selected, 'user': frappe.session.user, 'active': 1}, '*', as_dict=True)
    if not member or member.role != 'Teacher':return False
    if method in RECOVERY_METHODS:return True
    if method.startswith('frappe.integrations.oauth2_logins.') or 'reset_password' in method or 'update_password' in method:return True
    # Non-API page and asset requests do not execute teaching operations.
    if not method:
        path = getattr(getattr(frappe.local, 'request', None), 'path', '')
        if not path.startswith(('/api/', '/private/files/', '/lms')):return False
    context = billing_context(frappe.get_doc('IL Institute', selected), member)
    module = method.split('.')[1] if method.startswith('institute_lms.') else ''
    if module in ('account_billing', 'cybersource', 'subscription_payments', 'usage_billing'):
        if context['kind'] == 'Personal' or method in ('institute_lms.account_billing.status', 'institute_lms.account_billing.teacher_trial'):
            return True
        frappe.throw('Switch to Personal to manage your own subscription. Your institute manages its plan.', frappe.PermissionError)
    if not context['available']:
        frappe.throw(context['message'], frappe.PermissionError)
    return True
