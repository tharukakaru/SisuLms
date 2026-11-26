"""Private hosting-worker bridge. No method in this module is whitelisted."""
import frappe
from .saas import managed


def _organization(tenant, request_id):
    if getattr(frappe.local, 'request', None) or not frappe.conf.get('il_control_plane'):
        frappe.throw('Hosting worker context required', frappe.PermissionError)
    org = frappe.get_doc('IL Organization', tenant, for_update=True)
    if not request_id or org.get('removal_request_id') != request_id:
        frappe.throw('Removal request identity changed')
    from .owner_access import require_manager
    previous = frappe.session.user
    try:
        frappe.set_user(org.removal_requested_by)
        require_manager()
    finally:
        frappe.set_user(previous)
    return org


def pending():
    if getattr(frappe.local, 'request', None) or not frappe.conf.get('il_control_plane'):
        frappe.throw('Hosting worker context required', frappe.PermissionError)
    return frappe.get_all('IL Organization', filters={'removal_status': ['in', ['Requested', 'Running']]},
                         fields=['name', 'site_hostname', 'institute_code', 'removal_request_id'], limit_page_length=100)


def snapshot(tenant, request_id):
    org = _organization(tenant, request_id)
    if org.get('retired'):
        return {'completed': True}
    if org.enabled or org.provisioning_state == 'running' or org.get('custom_domain'):
        frappe.throw('Suspend the institute and resolve provisioning/custom-domain dependencies first')
    if frappe.db.count('IL Payment Attempt', {'tenant_id': tenant, 'status': ['in', ['created', 'pending']]}):
        frappe.throw('Unresolved control-plane payments')
    return {'tenant': org.name, 'hostname': org.site_hostname, 'code': org.institute_code,
            'request_id': org.removal_request_id, 'status': org.removal_status}


def progress(tenant, request_id, stage, failed=False):
    org = _organization(tenant, request_id)
    if org.get('retired'):
        return {'completed': True}
    allowed = {'validated', 'quiesced', 'backed_up', 'decommissioned', 'verified', 'starting', 'failed'}
    if stage not in allowed:
        frappe.throw('Invalid removal progress')
    org.removal_status = 'Failed' if failed else 'Running'
    org.removal_progress = stage
    managed(org)
    frappe.db.commit()
    return {'status': org.removal_status}


def complete(tenant, request_id, hostname, code):
    org = _organization(tenant, request_id)
    if org.get('retired'):
        return {'completed': True}
    from .tenant_retirement import retire_organization
    previous = frappe.session.user
    try:
        frappe.set_user(org.removal_requested_by)
        result = retire_organization(tenant, org.removal_request_reason, hostname, code, decommission_verified=True)
        frappe.db.commit()
        return result
    finally:
        frappe.set_user(previous)
