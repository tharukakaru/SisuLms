"""Customer-initiated sandbox checkout, isolated from Payments.lk and bank review.

Browser completion/cancellation is only a hint. Only authenticated CyberSource
reports can settle an invoice. No scheduled charging, saved card or MIT endpoint.
"""
import hashlib
import json
import time
import uuid
import frappe
from frappe.utils import now_datetime, get_datetime, get_url
from .cybersource_contract import minor, origin, session_request, verify_transaction
from .cybersource_transport import request, ProviderUnavailable

DT = 'IL CyberSource Attempt'
KINDS = {'tuition': 'IL Invoice', 'subscription': 'IL Account Invoice', 'platform': 'IL Provider Invoice', 'usage': 'IL Usage Invoice'}
ACTIVE = ('creating', 'pending', 'review')


def assert_no_active(kind, invoice):
    """Called under the invoice lock by alternative settlement paths."""
    root = frappe.conf.get('il_cybersource')
    if not isinstance(root, dict) or not root.get('enabled'): return
    if frappe.db.exists(DT, {'active_key': kind + ':' + invoice}):
        frappe.throw('Reconcile the pending CyberSource checkout before using another payment method')


def save(doc):
    doc.flags.cybersource_service = True
    return doc.save(ignore_permissions=True)


def settings(scope):
    root = frappe.conf.get('il_cybersource') or {}
    if not isinstance(root, dict) or root.get('enabled') is not True or root.get('mode') != 'sandbox':
        frappe.throw('CyberSource sandbox is not configured')
    c = (root.get('merchants') or {}).get(scope)
    if not isinstance(c, dict) or not all(c.get(k) for k in ('merchant_id', 'key_id', 'p12_path', 'p12_password')):
        frappe.throw('CyberSource sandbox credentials are not configured for this payment recipient')
    if not isinstance(c.get('methods'), list) or not c['methods']:
        frappe.throw('No sandbox payment methods have been activated')
    configured = origin(root.get('origin', ''))
    if get_url().rstrip('/') != configured:
        frappe.throw('Open the configured HTTPS sandbox site to pay')
    return dict(c, mode='sandbox', origin=configured)


def source(kind, invoice, payable=True):
    if kind not in KINDS: frappe.throw('Unsupported invoice type')
    if frappe.session.user == 'Guest': frappe.throw('Sign in to pay', frappe.PermissionError)
    from .api import identity, scoped
    inst, member = identity()
    if kind == 'tuition':
        doc = scoped('IL Invoice', invoice, inst)
        if member.role != 'Student' or doc.student != member.name:
            frappe.throw('Only the invoiced student can pay', frappe.PermissionError)
        scope = 'tuition:' + (doc.provider_account or inst.name)
        total, currency = minor(doc.amount), doc.currency or 'LKR'
        if payable and doc.get('gateway_request'):
            frappe.throw('Reconcile the existing payment provider attempt first')
        if payable and frappe.db.exists('IL Bank Slip', {'invoice': invoice, 'status': 'Pending'}):
            frappe.throw('Your bank slip is awaiting review; do not pay twice')
    elif kind == 'subscription':
        from .account_billing import account
        a = account(lock=True)
        doc = frappe.get_doc('IL Account Invoice', invoice, for_update=True)
        if a.role == 'Student' or doc.subscription != a.name or a.institute != inst.name:
            frappe.throw('This subscription invoice is not yours', frappe.PermissionError)
        if payable and (not a.enabled or get_datetime(doc.period_end) <= now_datetime()):
            frappe.throw('Subscription invoice is suspended or expired')
        scope, total, currency = 'platform', int(doc.amount_minor), doc.currency
    elif kind == 'usage':
        from .usage_billing import own_invoice
        doc = own_invoice(invoice)
        if member.role not in ('Teacher', 'Admin'):
            frappe.throw('Provider billing access required', frappe.PermissionError)
        if payable and not doc.issued_at: frappe.throw('An estimate is not payable')
        scope, total, currency = 'platform', minor(doc.amount_lkr), 'LKR'
    else:
        from .commercial import account_access
        doc = frappe.get_doc('IL Provider Invoice', invoice, for_update=True)
        account_access(frappe.get_doc('IL Provider Account', doc.provider_account))
        if payable and doc.get('collection_status') == 'Pending':
            frappe.throw('Reconcile the earlier collection first')
        scope, total, currency = 'platform', int(doc.total_minor), 'LKR'
    if payable and doc.status not in ('Unpaid', 'Overdue'):
        frappe.throw('This invoice is not payable')
    return doc, inst, scope, total, currency


def lock_invoice(kind, invoice):
    if kind not in KINDS: frappe.throw('Unsupported invoice type')
    frappe.db.sql('SELECT name FROM `tab' + KINDS[kind] + '` WHERE name=%s FOR UPDATE', (invoice,))


def accessible(name):
    a = frappe.get_doc(DT, name)
    source(a.kind, a.invoice, payable=False)
    if a.customer != frappe.session.user:
        frappe.throw('This checkout belongs to another customer', frappe.PermissionError)
    return a


def public(a):
    return {k: a.get(k) for k in ('name', 'status', 'invoice', 'kind', 'amount_minor', 'currency',
                                 'transaction_id', 'browser_event', 'last_checked')}


@frappe.whitelist(methods=['POST'])
def availability(kind, invoice):
    _, _, scope, _, _ = source(kind, invoice, payable=False)
    root = frappe.conf.get('il_cybersource') or {}
    configured = isinstance(root, dict) and root.get('enabled') is True and root.get('mode') == 'sandbox'
    return {'paused': bool(frappe.conf.get('il_payments_paused')), 'available': bool(not frappe.conf.get('il_payments_paused') and configured and scope in (root.get('merchants') or {})), 'mode': 'sandbox'}


@frappe.whitelist(methods=['POST'])
def start(kind, invoice):
    if frappe.conf.get('il_payments_paused'):
        frappe.throw("Payment gateway isn't connected yet. Please try again later.")
    from .registration import limit
    limit('cybersource-start:' + frappe.session.user)
    # Source invoice lock serializes creation across tabs and requests.
    lock_invoice(kind, invoice)
    doc, inst, scope, total, currency = source(kind, invoice)
    c = settings(scope)
    if currency not in c.get('currencies', ['LKR']):
        frappe.throw('This invoice currency has not been enabled for the sandbox merchant')
    active_key = kind + ':' + invoice
    existing = frappe.db.get_value(DT, {'active_key': active_key}, 'name')
    if existing:
        a = accessible(existing)
        if (a.merchant_id != c['merchant_id'] or a.amount_minor != total or a.currency != currency):
            frappe.throw('Checkout changed; reconcile the retained payment first')
        # Never hand the same capture context to a second tab/request. A lost
        # response is retained for reconciliation rather than risking two payments.
        return dict(public(a), mode='sandbox')
    reference = 'sisu-' + uuid.uuid4().hex
    body = session_request(reference, total, currency, c['origin'], c['methods'])
    a = save(frappe.get_doc(dict(doctype=DT, reference=reference, active_key=active_key,
        kind=kind, invoice=invoice, institute=inst.name, customer=frappe.session.user,
        merchant_scope=scope, merchant_id=c['merchant_id'], amount_minor=total, currency=currency,
        status='creating', request_snapshot=json.dumps(body))))
    # An ambiguous crash can never silently create a second active checkout.
    frappe.db.commit()
    try:
        token, claims = request(c, 'POST', '/uc/v1/sessions', body, token=True)
    except ProviderUnavailable:
        a.status = 'review'; save(a); frappe.db.commit()
        return dict(public(a), message='Session creation could not be confirmed. Contact SISU support before retrying.')
    a = frappe.get_doc(DT, a.name, for_update=True)
    a.session_token = token
    a.session_expires = claims['exp']
    a.status = 'pending'; save(a)
    return dict(public(a), session=token, mode='sandbox')


@frappe.whitelist(methods=['POST'])
def browser_event(attempt, event):
    a = accessible(attempt)
    if event not in ('completed', 'cancelled', 'failed'): frappe.throw('Invalid checkout event')
    a = frappe.get_doc(DT, a.name, for_update=True)
    a.browser_event = event; save(a)
    # Client failure/cancel cannot mark a financial transaction failed or free its key.
    return public(a)


@frappe.whitelist(methods=['POST'])
def status(attempt):
    return public(accessible(attempt))


@frappe.whitelist(methods=['POST'])
def reconcile(attempt):
    a = accessible(attempt)
    c = settings(a.merchant_scope)
    if a.merchant_id != c['merchant_id']: frappe.throw('Merchant changed; restore the original sandbox configuration')
    # Lock before checking the cooldown; concurrent polls must not multiply provider requests.
    a = frappe.get_doc(DT, a.name, for_update=True)
    if a.status in ('succeeded', 'failed'): return public(a)
    if a.last_checked and (now_datetime() - get_datetime(a.last_checked)).total_seconds() < 300:
        return dict(public(a), message='Verification is pending. Check again in five minutes.')
    a.last_checked = now_datetime(); save(a); frappe.db.commit()
    try:
        result = request(c, 'POST', '/tss/v2/searches', {
            'save': False, 'query': 'clientReferenceInformation.code:' + a.reference,
            'offset': 0, 'limit': 10, 'sort': 'submitTimeUtc:desc'})
        summaries = result.get('_embedded', {}).get('transactionSummaries', [])
        if not isinstance(summaries, list) or len(summaries) != 1:
            return dict(public(a), message='Awaiting an unambiguous CyberSource transaction report; do not pay again.')
        transaction_id = str(summaries[0].get('id', ''))
        data = request(c, 'GET', '/tss/v2/transactions/' + transaction_id)
        if str(data.get('id')) != transaction_id:
            raise ValueError('Transaction lookup mismatch')
        outcome = verify_transaction(data, {'merchant_id': a.merchant_id, 'reference': a.reference,
                                            'currency': a.currency, 'amount_minor': a.amount_minor})
    except (ProviderUnavailable, ValueError, TypeError, KeyError):
        return dict(public(a), message='Payment verification is pending. No access has been activated.')
    lock_invoice(a.kind, a.invoice)
    a = frappe.get_doc(DT, a.name, for_update=True)
    if a.status == 'succeeded': return public(a)
    a.transaction_id = transaction_id
    a.evidence = json.dumps({'id': transaction_id, 'merchantId': data.get('merchantId'),
        'clientReferenceInformation': data.get('clientReferenceInformation'),
        'applications': data.get('applicationInformation', {}).get('applications'),
        'paymentSolution': data.get('processingInformation', {}).get('paymentSolution')})
    if outcome == 'succeeded':
        # Save the unique merchant+transaction identity before financial effects.
        a.settlement_key = hashlib.sha256((a.merchant_id + ':' + transaction_id).encode()).hexdigest()
        save(a)
        doc, _, _, total, currency = source(a.kind, a.invoice, payable=False)
        if total != a.amount_minor or currency != a.currency or doc.status not in ('Unpaid', 'Overdue'):
            a.status = 'review'; save(a)
            return dict(public(a), message='Payment received but invoice requires manual allocation review.')
        frappe.db.savepoint('cybs_allocation')
        try:
            settle(a, doc)
        except frappe.ValidationError:
            frappe.db.rollback(save_point='cybs_allocation')
            a.status = 'review'; save(a)
            return dict(public(a), message='Payment verified; invoice allocation needs review. Do not pay again.')
        a.status = 'succeeded'; a.active_key = None
    elif outcome == 'failed':
        a.status = 'failed'; a.active_key = None
    else: a.status = outcome
    save(a)
    return public(a)


def settle(a, doc):
    """Private, invoked only after authenticated, exact-bound report verification."""
    reference = 'cybs-sandbox:' + a.settlement_key
    if a.kind == 'subscription':
        from .account_billing import record_verified_payment
        record_verified_payment(a.invoice, reference, a.amount_minor, a.currency, 'CyberSource sandbox')
    elif a.kind == 'usage':
        from .usage_billing import record_verified_payment
        record_verified_payment(a.invoice, reference, doc.amount_lkr, 'CyberSource sandbox authorization and capture verified', remote_reviewer='CyberSource sandbox')
    elif a.kind == 'platform':
        from .commercial import save as provider_save
        doc.update(dict(status='Paid', payment_reference=reference, settlement_key=a.settlement_key,
                   paid_at=now_datetime(), receipt_number='RC-' + doc.name, payment_channel='CyberSource sandbox'))
        provider_save(doc)
    else:
        doc.update(dict(status='Paid', payment_id=reference, paid_at=now_datetime(),
                   receipt_number='RC-' + doc.name, gateway_status='cybersource:sandbox:captured'))
        doc.save(ignore_permissions=True)
        from .commercial import account_for, configured_access, grant, notify_people
        room = frappe.get_doc('IL Classroom', doc.classroom)
        if account_for(room, False):
            start, end = configured_access(room, now_datetime())
            grant(doc, room, start, end, 'Card')
        else:
            from .wallet import record_earning
            record_earning(doc)
        notify_people(room, 'payment.received', 'payment:' + doc.name,
                      'Payment verified. Receipt ' + doc.receipt_number, student=doc.student)


@frappe.whitelist(methods=['POST'])
def review_queue():
    from .registration import require_owner
    require_owner()
    return frappe.get_all(DT, filters={'status': ['in', list(ACTIVE)]},
        fields=['name', 'kind', 'invoice', 'reference', 'merchant_scope', 'amount_minor', 'currency',
                'status', 'browser_event', 'last_checked', 'transaction_id'], limit_page_length=100)


@frappe.whitelist(methods=['POST'])
def close_unpaid(attempt, reason):
    """Owner records a Transaction Management review; absence alone is not payment proof."""
    from .registration import require_owner
    from .saas import audit
    require_owner()
    if not isinstance(reason, str) or len(reason.strip()) < 30:
        frappe.throw('Record your Transaction Management review confirming that no payment was processed')
    a = frappe.get_doc(DT, attempt)
    if a.status not in ACTIVE or a.transaction_id or a.settlement_key:
        frappe.throw('A recorded transaction must be reconciled, not discarded')
    # Allow the issued context, network timeouts and report indexing to expire.
    expires = float(a.session_expires or 0)
    if not expires or time.time() < expires + 300:
        frappe.throw('Wait until the session expiry and reporting delay have passed; uncertain sessions need support review')
    if time.time() > expires + 6 * 86400:
        frappe.throw('This attempt is outside the default reporting window; support must reconcile archived transactions')
    c = settings(a.merchant_scope)
    if c['merchant_id'] != a.merchant_id: frappe.throw('Restore the original merchant configuration')
    result = request(c, 'POST', '/tss/v2/searches', {
        'save': False, 'query': 'clientReferenceInformation.code:' + a.reference,
        'offset': 0, 'limit': 10, 'sort': 'submitTimeUtc:desc'})
    if result.get('totalCount') != 0:
        frappe.throw('Cannot confirm an empty transaction report; reconcile this attempt')
    lock_invoice(a.kind, a.invoice)
    a = frappe.get_doc(DT, attempt, for_update=True)
    if a.status not in ACTIVE or a.transaction_id or a.settlement_key:
        frappe.throw('Attempt changed; review its latest status')
    a.status = 'cancelled'; a.active_key = None; save(a)
    audit('Close unpaid CyberSource sandbox attempt', a.name, reason.strip()[:1000])
    return public(a)
