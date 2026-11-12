"""Restricted, single-use production gateway test.

No card details or payment authorization are handled here.
"""

import frappe

from .live_gateway_test_rules import (
    TEST_USER,
    AMOUNT_MINOR,
    CURRENCY,
    eligible,
    validate_amount,
)

DT = "IL Live Gateway Test Payment"
TEST_KEY = "live-cybersource-lkr50-v1"


def require_test_access():
    if not eligible(frappe.session.user, frappe.conf):
        frappe.throw(
            "Live gateway test is not available",
            frappe.PermissionError,
        )


def public_record(doc):
    return {
        "name": doc.name,
        "status": doc.status,
        "amount_minor": doc.amount_minor,
        "currency": doc.currency,
        "transaction_id": doc.transaction_id,
    }


@frappe.whitelist(methods=["POST"])
def prepare():
    """Create or return the one permitted test-payment record.

    Does not contact CyberSource or initiate a transaction.
    """
    require_test_access()

    from .account_billing import account

    from .api import identity
    inst, member = identity()
    subscription = account(inst=inst, member=member, lock=True)

    if (
        member.role != "Admin"
        or not subscription
        or subscription.institute != inst.name
        or not subscription.enabled
    ):
        frappe.throw(
            "An active authorized billing account is required",
            frappe.PermissionError,
        )

    existing = frappe.db.get_value(
        DT, {"test_key": TEST_KEY}, "name"
    )

    if existing:
        doc = frappe.get_doc(DT, existing)

        if (
            doc.customer != TEST_USER
            or doc.institute != subscription.institute
        ):
            frappe.throw("Test payment ownership mismatch")

        validate_amount(doc.amount_minor, doc.currency)
        return public_record(doc)

    doc = frappe.get_doc({
        "doctype": DT,
        "test_key": TEST_KEY,
        "customer": TEST_USER,
        "institute": subscription.institute,
        "amount_minor": AMOUNT_MINOR,
        "currency": CURRENCY,
        "status": "Unpaid",
    })

    doc.flags.live_gateway_test_service = True
    doc.insert(ignore_permissions=True)

    return public_record(doc)


@frappe.whitelist(methods=["POST"])
def status():
    """Return the test record without exposing card information."""
    require_test_access()

    name = frappe.db.get_value(
        DT, {"test_key": TEST_KEY}, "name"
    )

    if not name:
        return {
            "status": "Not created",
            "amount_minor": AMOUNT_MINOR,
            "currency": CURRENCY,
        }

    doc = frappe.get_doc(DT, name)

    if doc.customer != frappe.session.user:
        frappe.throw(
            "Test payment belongs to another account",
            frappe.PermissionError,
        )

    validate_amount(doc.amount_minor, doc.currency)
    return public_record(doc)
