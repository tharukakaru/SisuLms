"""Confirmed provider usage policy; pure rules, not a payment settlement endpoint.

All datetimes must use one consistent billing timezone. Periods are half-open.
Rates must be snapshotted on issuance; later catalog edits cannot rewrite invoices.
"""
from datetime import timedelta
from decimal import Decimal

VERSION = "provider-lkr-2026-10-27"
PLANS = {
    "Individual": {"monthly_lkr": 2500, "active_student_lkr": 100},
    "Silver": {"monthly_lkr": 5000, "active_student_lkr": 50},
    "Gold": {"monthly_lkr": 15000, "active_student_lkr": 50},
    "Platinum": {"monthly_lkr": 22000, "active_student_lkr": 50},
}

def chargeable_start(trial_until, paid_service_start):
    """paid_service_start is authoritative verified-payment coverage, never a slip date."""
    if paid_service_start is None:
        return None
    return max(trial_until, paid_service_start)

def usage_quote(provider, plan, start, end, trial_until, paid_service_start, attendance):
    """Input rows are provider-scoped session attendance with stable student IDs.

    present_at is session time, NOT the time a teacher edited attendance.
    Caller must select only verified paid coverage, persist invoice snapshots,
    and handle later attendance corrections through auditable adjustments.
    """
    if not provider or plan not in PLANS or end <= start:
        raise ValueError("A provider, valid plan and increasing period are required")
    eligible = chargeable_start(trial_until, paid_service_start)
    students = set()
    if eligible is not None:
        begin = max(start, eligible)
        for row in attendance:
            if (row.get("provider") == provider and row.get("present") is True
                and row.get("student") and begin <= row["present_at"] < end):
                students.add(row["student"])
    rate = PLANS[plan]["active_student_lkr"]
    return {"provider": provider, "plan": plan, "currency": "LKR",
            "quantity": len(students), "unit_rate": rate,
            "amount": int(Decimal(len(students)) * Decimal(rate)),
            "student_ids": sorted(students), "period_start": start,
            "period_end": end, "estimate_at": end - timedelta(days=5),
            "issue_at": end, "due_at": end + timedelta(days=10),
            "policy_version": VERSION}

def usage_access_blocked(now, invoices, suspension_recorded=False):
    """A recorded suspension persists until explicit authorized reactivation.

    Settled invoices must be verified by a trusted service. Browser requests
    cannot set settled or clear suspension_recorded.
    """
    return suspension_recorded or any(
        not invoice.get("settled", False) and now >= invoice["due_at"]
        for invoice in invoices
    )
