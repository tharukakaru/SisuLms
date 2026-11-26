"""Controlled retirement of decommissioned SaaS tenants."""

import uuid
import frappe
from frappe.utils import now_datetime
from .saas import managed, audit
from .platform import owner


def retire_organization(
    tenant,
    reason,
    expected_hostname,
    expected_code,
    decommission_verified=False
):
    owner()
    from .owner_access import require_manager
    require_manager()
    if getattr(frappe.local, 'request', None):
        frappe.throw('Retirement completion is restricted to the hosting worker', frappe.PermissionError)

    if decommission_verified is not True:
        frappe.throw("Site decommissioning must be verified")

    reason = str(reason or "").strip()

    if not 10 <= len(reason) <= 500:
        frappe.throw("Provide a retirement reason of 10-500 characters")

    org = frappe.get_doc(
        "IL Organization", tenant, for_update=True
    )

    if org.get("retired"):
        return {
            "tenant_id": org.name,
            "retired": True,
            "changed": False
        }

    if org.site_hostname != expected_hostname:
        frappe.throw("Organization hostname mismatch")

    if org.institute_code != expected_code:
        frappe.throw("Organization institute code mismatch")

    subscriptions = frappe.get_all(
        "IL Subscription",
        filters={"tenant_id": tenant},
        pluck="name"
    )

    if len(subscriptions) != 1:
        frappe.throw("Unexpected subscription count")

    subscription = frappe.get_doc(
        "IL Subscription",
        subscriptions[0],
        for_update=True
    )

    pending_payments = frappe.db.count(
        "IL Payment Attempt",
        {
            "tenant_id": tenant,
            "status": ["in", ["created", "pending"]]
        }
    )

    if pending_payments:
        frappe.throw(
            "Unresolved payment attempts require reconciliation"
        )

    old_hostname = org.site_hostname
    old_code = org.institute_code
    old_domain = org.custom_domain

    retired_hostname = org.name + ".invalid"
    retired_code = "RETIRED-" + org.name

    org.original_site_hostname = old_hostname
    org.original_institute_code = old_code

    org.removal_status = "Completed"
    org.retired = 1
    org.retired_at = now_datetime()
    org.retired_by = frappe.session.user
    org.retirement_reason = reason

    org.enabled = 0
    org.site_hostname = retired_hostname
    org.institute_code = retired_code
    org.custom_domain = None

    org.flags.tenant_retirement = True
    managed(org)

    subscription.enabled = 0
    subscription.state = "cancelled"
    subscription.grace_until = None
    managed(subscription)

    provisioning_jobs = frappe.get_all(
        "IL Provisioning Job",
        filters={"organization": tenant},
        pluck="name",
        order_by="name asc"
    )

    for job_name in provisioning_jobs:
        job = frappe.get_doc(
            "IL Provisioning Job",
            job_name,
            for_update=True
        )

        if job.status == "retired":
            continue

        previous_status = job.status
        job.status = "retired"
        managed(job)

        audit(
            "Retire provisioning job",
            tenant,
            "Job: " + job.name
            + "; Previous status: " + previous_status
        )

    delivery_name = frappe.db.get_value(
        "IL Policy Delivery",
        {"organization": tenant},
        "name"
    )

    if delivery_name:
        delivery = frappe.get_doc(
            "IL Policy Delivery",
            delivery_name,
            for_update=True
        )

        delivery.status = "Retired"
        delivery.next_attempt = None
        managed(delivery)

    audit(
        "Permanently retire organization",
        tenant,
        "Hostname: " + old_hostname
        + "; Code: " + old_code
        + "; Custom domain: " + str(old_domain or "")
        + "; Reason: " + reason
    )

    return {
        "tenant_id": tenant,
        "retired": True,
        "changed": True,
        "released_hostname": old_hostname,
        "released_code": old_code
    }


@frappe.whitelist(methods=["GET"])
def removal_preview(tenant):
    owner()
    from .owner_access import require_manager
    require_manager()

    org = frappe.get_doc("IL Organization", tenant)

    if org.get("retired"):
        frappe.throw("Organization is already retired")

    pending = frappe.db.count(
        "IL Payment Attempt",
        {
            "tenant_id": org.name,
            "status": ["in", ["created", "pending"]]
        }
    )

    transactions = frappe.db.count(
        "IL Payment Transaction",
        {"tenant_id": org.name}
    )

    blockers = []

    if pending:
        blockers.append("Unresolved payment attempts")

    if org.provisioning_state == "running":
        blockers.append("Website provisioning is running")

    if org.enabled:
        blockers.append("Institute must be suspended before removal")

    return {
        "tenant_id": org.name,
        "title": org.title,
        "code": org.institute_code,
        "hostname": org.site_hostname,
        "custom_domain": org.custom_domain,
        "admin_contact": org.admin_contact,
        "pending_payments": pending,
        "financial_records": transactions,
        "blockers": blockers,
        "hosting_verified": False,
        "removal_available": not blockers and org.get("removal_status") in (None, "", "Failed"),
        "removal_status": org.get("removal_status") or "",
        "progress": org.get("removal_progress") or ""
    }


@frappe.whitelist(methods=["POST"])
def request_removal(tenant, code, hostname, reason):
    owner()
    from .owner_access import require_manager
    require_manager()

    reason = str(reason or "").strip()

    if not 10 <= len(reason) <= 500:
        frappe.throw("Provide a reason of 10-500 characters")

    org = frappe.get_doc(
        "IL Organization", tenant, for_update=True
    )

    if org.get("retired"):
        frappe.throw("Organization already retired")

    if org.site_hostname != hostname:
        frappe.throw("Website identity mismatch")

    if org.institute_code != code:
        frappe.throw("Institute code mismatch")

    if org.enabled:
        frappe.throw("Suspend the institute first")

    if org.provisioning_state == "running":
        frappe.throw("Website provisioning is still running")

    protected = {
        "platform.sisuacademylk.com",
        "sisuacademylk.com",
        "www.sisuacademylk.com",
        "staging.sisuacademylk.com",
        frappe.local.site
    }

    if org.site_hostname.lower() in protected:
        frappe.throw("Protected website cannot be removed",
                     frappe.PermissionError)

    if frappe.db.count("IL Payment Attempt", {
        "tenant_id": tenant,
        "status": ["in", ["created", "pending"]]
    }):
        frappe.throw("Unresolved payments require reconciliation")

    if org.get("removal_status") in ("Requested", "Running"):
        return {"requested": True, "duplicate": True}

    if org.get("removal_status") == "Failed":
        org.removal_status = "Requested"
        managed(org)
        return {"requested": True, "status": "Requested", "retry": True}
    if org.get("removal_status"):
        frappe.throw("Existing removal requires review")

    org.removal_request_id = uuid.uuid4().hex
    org.removal_status = "Requested"
    org.removal_requested_at = now_datetime()
    org.removal_requested_by = frappe.session.user
    org.removal_request_reason = reason

    managed(org)

    audit(
        "Institute removal requested",
        org.name,
        "Website: " + hostname + "; Reason: " + reason
    )

    return {"requested": True, "status": "Requested"}


@frappe.whitelist(methods=['GET'])
def removal_status(tenant):
    owner()
    from .owner_access import require_manager
    require_manager()
    org = frappe.get_doc('IL Organization', tenant)
    return {'tenant_id': org.name, 'status': org.get('removal_status') or '',
            'retired': bool(org.get('retired')), 'progress': org.get('removal_progress') or '',
            'requested_at': org.get('removal_requested_at'),
            'completed_at': org.get('retired_at')}
