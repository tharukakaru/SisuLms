"""Explicit infrastructure allocation for standalone account-billing sites."""
import frappe
from .saas_rules import check_capacity

def configured():
    return (not frappe.conf.get('il_tenant_id') and not frappe.conf.get('il_control_plane')
            and bool(frappe.conf.get('il_usage_billing_enabled'))
            and type(frappe.conf.get('il_account_storage_bytes')) is int
            and 0 < frappe.conf.il_account_storage_bytes <= 1024**4)

def capacity(current,requested):
    if not configured():frappe.throw('Account storage allocation is not configured')
    from .api import institute
    inst=institute()
    frappe.db.sql('SELECT name FROM `tabIL Institute` WHERE name=%s FOR UPDATE',(inst.name,))
    try:return check_capacity(current(),requested,frappe.conf.il_account_storage_bytes)
    except ValueError as exc:frappe.throw(str(exc))

def workspace():
    from .api import identity
    from .account_billing import policy
    from .usage import used
    identity()
    n=used('storage_bytes');limit=frappe.conf.il_account_storage_bytes
    return dict(subscription=policy(),storage_backend=frappe.conf.get('il_storage_backend','frappe'),
                billing_url=None,usage=None,storage=dict(used=n,limit=limit,remaining=max(0,limit-n)))
