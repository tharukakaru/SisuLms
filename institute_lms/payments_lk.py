"""Payments.lk adapter, disabled until per-site merchant settings are supplied.

Only hosted checkout is supported. No card data or automatic card debits.
Expired/ambiguous attempts require reconciliation before an operator resets them.
"""
import json
import uuid
from datetime import timedelta
import requests
import frappe
from frappe.utils import get_url, now_datetime, get_datetime
from .api import identity, scoped, institute
from .payments_lk_contract import amount_cents, hosted_url, verify_signature, valid_payment

BASE = "https://api.payments.lk/v1"


def config():
    key = frappe.conf.get("il_payments_lk_secret_key", "")
    secret = frappe.conf.get("il_payments_lk_webhook_secret", "")
    mode = frappe.conf.get("il_payments_lk_mode", "test")
    if mode not in ("test", "live") or not key.startswith(f"sk_{mode}_") or not secret.startswith("whsec_"):
        frappe.throw("payments.lk is not configured. Ask your institute administrator to complete merchant setup.")
    return key, secret, mode


def provider_request(method, path, key, body=None, idempotency=None):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if idempotency:
        headers["Idempotency-Key"] = idempotency
    try:
        response = requests.request(method, BASE + path, headers=headers, data=body, timeout=(5, 20), allow_redirects=False)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Invalid response")
        return result
    except (requests.RequestException, ValueError):
        # Do not log provider bodies or credentials. Preserve the recorded attempt.
        frappe.throw("The payment provider could not confirm this request. Your payment attempt was retained; retry later or ask your institute to reconcile it.")


def checkout(invoice):
    from .commercial import hnb_checkout
    if frappe.db.get_value('IL Invoice',invoice,'provider_account'):
        return hnb_checkout(invoice)
    inst, member = identity()
    doc = scoped("IL Invoice", invoice, inst)
    if member.role != "Student" or doc.student != member.name:
        frappe.throw("Only the invoiced student can initiate payment", frappe.PermissionError)
    key, _, mode = config()
    site_url = get_url()
    if not site_url.startswith("https://"):
        frappe.throw("payments.lk requires an HTTPS institute URL")
    cents = amount_cents(doc.amount)
    frappe.db.sql("SELECT name FROM `tabIL Invoice` WHERE name=%s FOR UPDATE", (doc.name,))
    doc.reload()
    if doc.status == "Paid":
        frappe.throw("This invoice is already paid")
    if doc.gateway_request:
        if doc.gateway_mode != mode:
            frappe.throw("An earlier attempt belongs to a different payment mode. Reconcile it before changing modes.")
        stored = json.loads(doc.gateway_request)
        if stored.get("amountCents") != cents:
            frappe.throw("This invoice changed after checkout started. Reconcile the existing attempt first.")
    else:
        body = {"amountCents": cents, "description": f"Class installment {doc.installment}",
                "reference": doc.name, "successUrl": get_url("/campus?payment=returned#payments"),
                "cancelUrl": get_url("/campus?payment=cancelled#payments"), "locale": "en"}
        doc.update({"gateway_request": json.dumps(body, separators=(",", ":")),
                    "gateway_request_key": "sisu-" + uuid.uuid4().hex,
                    "gateway_requested_at": now_datetime(), "gateway_mode": mode})
        doc.save(ignore_permissions=True)
    # Persist the exact request BEFORE an external side effect. A retry reuses it.
    frappe.db.commit()
    if doc.gateway_checkout_id:
        result = provider_request("GET", "/checkouts/" + doc.gateway_checkout_id, key)
    else:
        if get_datetime(doc.gateway_requested_at) < now_datetime() - timedelta(hours=23):
            frappe.throw("This unresolved attempt is too old to retry safely. Ask your institute to reconcile it before starting another checkout.")
        result = provider_request("POST", "/checkouts", key, doc.gateway_request, doc.gateway_request_key)
    if (result.get("mode") != mode or not hosted_url(result.get("url"))
            or result.get("payment", {}).get("reference") != doc.name
            or result.get("payment", {}).get("amountCents") != cents
            or result.get("payment", {}).get("currency") != "LKR"):
        frappe.throw("Unexpected payment provider response. Ask your institute to reconcile this attempt.")
    checkout_id = result.get("id", "")
    import re
    if not re.fullmatch(r"chk_[a-zA-Z0-9]{24}", checkout_id):
        frappe.throw("Unexpected checkout reference")
    frappe.db.set_value("IL Invoice", doc.name, "gateway_checkout_id", checkout_id)
    if result.get("status") != "open":
        frappe.db.commit()
        frappe.throw("This checkout is no longer open. Your institute must reconcile its verified payment status before another checkout is created.")
    return {"redirect_url": result["url"], "provider": "payments.lk"}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def notify(**kwargs):
    _, secret, mode = config()
    raw = frappe.request.get_data(cache=True)
    if len(raw) > 65536 or not verify_signature(raw, frappe.request.headers.get("Payments-Signature"), secret):
        frappe.throw("Invalid payment signature", frappe.PermissionError)
    try:
        event = json.loads(raw)
    except (ValueError, UnicodeError):
        frappe.throw("Invalid payment event", frappe.PermissionError)
    if not isinstance(event, dict) or event.get("mode") != mode:
        frappe.throw("Invalid payment mode", frappe.PermissionError)
    payment_data=event.get('data')
    if isinstance(payment_data,dict) and str(payment_data.get('reference','')).startswith('lesson-'):
        # One student-merchant webhook routes distinct business purposes safely.
        # The lesson service independently re-verifies the raw signature/binding.
        from .lectures import notify as lecture_notify
        return lecture_notify()
    if event.get("type") != "payment.succeeded":
        if event.get('type')=='payment.failed':
            payment=event.get('data')
            if isinstance(payment,dict) and isinstance(payment.get('reference'),str):
                rows=frappe.db.sql('SELECT name FROM `tabIL Invoice` WHERE name=%s FOR UPDATE',(payment['reference'],))
                if rows:
                    doc=frappe.get_doc('IL Invoice',rows[0][0],for_update=True)
                    binding=dict(payment,status='succeeded')
                    if payment.get('status')=='failed' and doc.gateway_mode==mode and valid_payment(binding,doc.as_dict(),mode) and doc.status!='Paid':
                        from .notification_service import emit
                        emit(doc.institute,doc.student,'payment.failed','payment-failed:'+payment['id'],'Payment failed. Please review your invoice.')
        return {"accepted": True, "settled": False}
    payment = event.get("data")
    if not isinstance(payment, dict) or not isinstance(payment.get("reference"), str):
        frappe.throw("Invalid payment data", frappe.PermissionError)
    rows = frappe.db.sql("SELECT name FROM `tabIL Invoice` WHERE name=%s FOR UPDATE", (payment["reference"],))
    if not rows:
        frappe.throw("Invoice unavailable", frappe.PermissionError)
    doc = scoped("IL Invoice", rows[0][0], institute())
    if doc.gateway_mode != mode or not valid_payment(payment, doc.as_dict(), mode):
        frappe.throw("Payment does not match its invoice and checkout", frappe.PermissionError)
    if doc.status == "Paid":
        if doc.payment_id != payment["id"]:
            frappe.throw("Invoice already settled with another payment", frappe.PermissionError)
        return {"accepted": True, "settled": True}
    if frappe.db.exists("IL Invoice", {"payment_id": payment["id"], "name": ["!=", doc.name]}):
        frappe.throw("Payment reference already used", frappe.PermissionError)
    doc.update({"status": "Paid", "payment_id": payment["id"], "paid_at": now_datetime(),
                "receipt_number": f"RC-{doc.name}", "gateway_status": "payments.lk:succeeded"})
    doc.save(ignore_permissions=True)
    from .commercial import account_for,configured_access,grant
    room=frappe.get_doc('IL Classroom',doc.classroom)
    if account_for(room,False):
        start,end=configured_access(room,now_datetime())
        grant(doc,room,start,end,'Card')
    from .wallet import record_earning
    record_earning(doc)
    from .notifications import queue
    queue(doc.institute, doc.student, f"payment:{doc.name}",
          f"Payment received: LKR {doc.amount:.2f}. Receipt {doc.receipt_number}.")
    return {"accepted": True, "settled": True}
