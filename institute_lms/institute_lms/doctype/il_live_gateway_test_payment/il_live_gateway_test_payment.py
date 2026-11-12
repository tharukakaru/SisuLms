import frappe
from frappe.model.document import Document
from institute_lms.live_gateway_test_rules import (
    TEST_USER, validate_amount
)


class ILLiveGatewayTestPayment(Document):
    def validate(self):
        if not self.flags.get("live_gateway_test_service"):
            frappe.throw(
                "Use the restricted gateway test service",
                frappe.PermissionError
            )

        if self.test_key != "live-cybersource-lkr50-v1":
            frappe.throw("Invalid gateway test identity")

        if self.customer != TEST_USER or not self.institute:
            frappe.throw("Invalid gateway test owner")

        validate_amount(self.amount_minor, self.currency)

        if self.status not in ("Unpaid", "Paid"):
            frappe.throw("Invalid gateway test status")

        old = self.get_doc_before_save()
        if old:
            immutable = (
                "test_key", "customer", "institute",
                "amount_minor", "currency"
            )
            if any(self.get(k) != old.get(k) for k in immutable):
                frappe.throw("Gateway test identity cannot change")

            if old.status == "Paid":
                if self.status != "Paid":
                    frappe.throw("Paid test cannot be reopened")
                protected = (
                    "transaction_id", "settlement_key", "paid_at"
                )
                if any(
                    self.get(k) != old.get(k)
                    for k in protected
                ):
                    frappe.throw(
                        "Verified test settlement evidence is immutable"
                    )

        if self.status == "Paid":
            if not self.transaction_id or not self.settlement_key:
                frappe.throw("Verified payment evidence required")
        elif self.transaction_id or self.settlement_key or self.paid_at:
            frappe.throw("Unpaid test cannot contain settlement evidence")

    def on_trash(self):
        frappe.throw(
            "Gateway test payment records cannot be deleted",
            frappe.PermissionError
        )
