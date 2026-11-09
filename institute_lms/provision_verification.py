"""Validate operator-issued provisioning evidence. No cross-site DB access."""
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import frappe

ACTION = "Verified tenant installation"
MAX_AGE = timedelta(minutes=15)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def signature(evidence, key):
    return hmac.new(
        key.encode("utf-8"),
        canonical(evidence).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def valid_record(record, job, org, key, now=None):
    if not isinstance(key, str) or len(key) < 32:
        return False
    try:
        envelope = json.loads(record)
        evidence = envelope["evidence"]
        mac = envelope["signature"]
        if not isinstance(evidence, dict) or not isinstance(mac, str):
            return False
        if set(evidence) != {
            "job", "tenant_id", "hostname", "code",
            "admin_contact", "verified_at", "checks"
        }:
            return False
        if evidence["job"] != job.name:
            return False
        if evidence["tenant_id"] != org.name:
            return False
        if evidence["hostname"] != org.site_hostname:
            return False
        if evidence["code"] != org.institute_code:
            return False
        if evidence["admin_contact"] != org.admin_contact:
            return False
        required = {
            "tenant_identity", "installed_apps", "database",
            "institute", "admin", "signing_keys"
        }
        checks = evidence["checks"]
        if not isinstance(checks, dict) or set(checks) != required:
            return False
        if any(checks[k] is not True for k in required):
            return False
        issued = datetime.fromisoformat(evidence["verified_at"])
        if issued.tzinfo is None:
            return False
        current = now or datetime.now(timezone.utc)
        age = current - issued.astimezone(timezone.utc)
        if not timedelta(0) <= age <= MAX_AGE:
            return False
        return hmac.compare_digest(signature(evidence, key), mac)
    except (ValueError, TypeError, KeyError, AttributeError):
        return False


def require_verified(job, org):
    key = frappe.conf.get("il_provision_attestation_key")
    if not isinstance(key, str) or len(key) < 32:
        frappe.throw("Provisioning verification is not configured")

    rows = frappe.get_all(
        "IL SaaS Audit",
        filters={"action": ACTION, "reference": job.name},
        fields=["details"],
        order_by="creation desc",
        limit_page_length=10,
    )
    if not any(valid_record(row.details, job, org, key) for row in rows):
        frappe.throw("A recent verified tenant installation is required")
