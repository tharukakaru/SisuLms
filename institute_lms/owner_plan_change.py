"""Private campus worker for owner-requested institute plan changes."""
from html import escape
import frappe
from frappe.utils import get_datetime, now_datetime
from .account_billing_rules import PLANS


def apply(profile, user, subscription, plan, expected_modified, reason, reviewer):
    if getattr(frappe.local, 'request', None) or frappe.session.user != 'Administrator':
        frappe.throw('Background administrator context required.', frappe.PermissionError)
    if frappe.conf.get('il_control_plane'):
        frappe.throw('Plan changes must run on the selected campus.')
    reason = str(reason or '').strip()
    if plan not in PLANS or not reason or len(reason) > 500 or not reviewer:
        frappe.throw('Choose a valid plan and audit reason.')
    from .account_billing import ACCOUNT, save, void_open
    p = frappe.get_doc('IL Public Profile', profile, for_update=True)
    if p.user != user or p.kind != 'Institute' or p.status != 'Verified' or not p.workspace:
        frappe.throw('This profile is not a verified institute.')
    if not frappe.db.get_value('User', user, 'enabled') or not frappe.db.exists('IL Member', {
        'user': user, 'institute': p.workspace, 'role': 'Admin', 'active': 1
    }):
        frappe.throw('The institute administrator must have an active account and membership.')
    a = frappe.get_doc(ACCOUNT, subscription, for_update=True)
    if a.role != 'Institute' or a.institute != p.workspace or not a.enabled:
        frappe.throw('Subscription does not belong to this active institute.')
    if not expected_modified or get_datetime(a.modified) != get_datetime(expected_modified):
        frappe.throw('Subscription changed since you opened it. Refresh and review the current plan.')
    if a.cancel_at_end:
        frappe.throw('Resolve the scheduled cancellation before changing plans.')
    dates = (a.trial_started, a.trial_until, a.paid_until)
    before = (a.plan, a.next_plan or None)
    scheduled = bool(a.paid_until and get_datetime(a.paid_until) > now_datetime())
    if scheduled:
        a.next_plan = plan if plan != a.plan else None
    else:
        a.plan, a.next_plan = plan, None
    if before == (a.plan, a.next_plan or None):
        return {'ok': True, 'message': 'The subscription already has this plan selection.'}
    # Existing billing service refuses active payment attempts. The background
    # job rolls back all writes on any exception, including provider sync.
    void_open(a)
    save(a)
    if dates != (a.trial_started, a.trial_until, a.paid_until):
        frappe.throw('Subscription dates changed unexpectedly; change rolled back.')
    a.add_comment('Comment', text=escape(
        f'Platform owner {reviewer}: plan {before[0]} (next {before[1] or "none"}) -> '
        f'{a.plan} (next {a.next_plan or "none"}). Reason: {reason}'))
    return {'ok': True, 'message': ('Plan selection saved for the next billing period.' if scheduled else
        'Plan updated. Trial and paid-through dates preserved.')}
