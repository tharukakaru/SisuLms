"""Customer-initiated CyberSource checkout, isolated from Payments.lk and bank review.

Browser completion/cancellation is only a hint. Only authenticated CyberSource
reports can settle an invoice. No scheduled charging, saved card or MIT endpoint.
"""
import hashlib
import hmac
import json
import time
import uuid
from urllib.parse import urlsplit, urlencode
import frappe
from frappe.utils import now_datetime, get_datetime, get_url
from .cybersource_contract import minor, origin, session_request, verify_transaction, authentication_only
from .cybersource_transport import request, ProviderUnavailable, SessionRejected
from .checkout_captcha import verify as verify_checkout, public_settings as captcha_settings

DT = 'IL CyberSource Attempt'
KINDS = {'tuition': 'IL Invoice', 'subscription': 'IL Account Invoice', 'platform': 'IL Provider Invoice', 'usage': 'IL Usage Invoice'}
ACTIVE = ('creating', 'pending', 'review')
RECONCILE_INTERVAL = 15


def attempt_environment(attempt):
    try:
        value = json.loads(attempt.evidence or '{}')
    except (TypeError, ValueError):
        frappe.throw('Invalid stored payment environment')
    mode = value.get('environment', 'sandbox')
    if mode not in ('sandbox', 'live'):
        frappe.throw('Unknown stored payment environment')
    return mode


def assert_no_active(kind, invoice):
    """Called under the invoice lock by alternative settlement paths."""
    root = frappe.conf.get('il_cybersource')
    if not isinstance(root, dict) or not root.get('enabled'): return
    if frappe.db.exists(DT, {'active_key': kind + ':' + invoice}):
        frappe.throw('Reconcile the pending CyberSource checkout before using another payment method')


def save(doc):
    doc.flags.cybersource_service = True
    return doc.save(ignore_permissions=True)


def payment_paused():
    # The global administrative pause always takes precedence.
    if frappe.conf.get('il_payments_paused'):
        return True
    testers = frappe.conf.get('il_cybersource_test_users')
    if testers is not None:
        return frappe.session.user not in testers
    return False


def settings(scope, for_reconciliation=False):
    root = frappe.conf.get('il_cybersource') or {}
    if not isinstance(root, dict) or root.get('enabled') is not True or root.get('mode') not in ('sandbox', 'live'):
        frappe.throw('CyberSource is not configured')
    mode = root['mode']
    if mode == 'live' and not for_reconciliation and root.get('live_checkout_approved') is not True:
        frappe.throw('Live CyberSource checkout requires an explicit production approval flag')
    c = (root.get('merchants') or {}).get(scope)
    if not isinstance(c, dict) or not all(c.get(k) for k in ('merchant_id', 'key_id')) or not (
            c.get('p12_path') and c.get('p12_password') or c.get('shared_secret')):
        frappe.throw('CyberSource credentials are not configured for this payment recipient')
    if not isinstance(c.get('methods'), list) or not c['methods']:
        frappe.throw('No payment methods have been activated')
    local_checkout = frappe.conf.get('il_local_card_test') is True
    if local_checkout and (
            urlsplit(get_url()).hostname not in ('127.0.0.1', 'localhost')
            or not isinstance(frappe.conf.get('il_cybersource_test_users'), list)
            or not frappe.conf.get('il_cybersource_test_users')):
        frappe.throw('Local card testing requires a loopback site and approved test accounts')
    configured = origin(root.get('origin', ''))
    if local_checkout and urlsplit(configured).hostname != 'checkout.localhost':
        frappe.throw('Local card testing requires an HTTPS checkout.localhost origin')
    current_origin = get_url().rstrip('/')
    if local_checkout:
        request_context = getattr(frappe.local, 'request', None)
        current_origin = str(getattr(request_context, 'host_url', '')).rstrip('/')
    if current_origin != configured and not (local_checkout and for_reconciliation):
        frappe.throw('Open the configured HTTPS checkout site to pay')
    return dict(c, mode=mode, origin=configured)


def source(kind, invoice, payable=True):
    if payable and frappe.conf.get('il_cybersource_test_users') is not None:
        if frappe.session.user not in frappe.conf.get('il_cybersource_test_users') or kind != 'subscription':
            frappe.throw('Checkout is restricted to approved subscription test accounts', frappe.PermissionError)
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
    if payable and doc.status not in (('Draft', 'Unpaid', 'Overdue') if kind == 'subscription' else ('Unpaid', 'Overdue')):
        frappe.throw('This invoice is not payable')
    if payable and frappe.conf.get('il_local_card_test') is True and (
            kind != 'subscription' or total != 500 or currency != 'LKR'):
        frappe.throw('Local card testing is limited to a LKR 5 subscription invoice')
    return doc, inst, scope, total, currency


def lock_invoice(kind, invoice, for_reconciliation=False):
    if not for_reconciliation and frappe.conf.get('il_cybersource_test_users') is not None:
        if frappe.session.user not in frappe.conf.get('il_cybersource_test_users') or kind != 'subscription':
            frappe.throw('Checkout is restricted to approved subscription test accounts', frappe.PermissionError)
    if kind not in KINDS: frappe.throw('Unsupported invoice type')
    frappe.db.sql('SELECT name FROM `tab' + KINDS[kind] + '` WHERE name=%s FOR UPDATE', (invoice,))


def accessible(name):
    a = frappe.get_doc(DT, name)
    source(a.kind, a.invoice, payable=False)
    if a.customer != frappe.session.user:
        frappe.throw('This checkout belongs to another customer', frappe.PermissionError)
    return a


def public(a):
    result = {k: a.get(k) for k in ('name', 'status', 'invoice', 'kind', 'amount_minor', 'currency',
                                 'transaction_id', 'browser_event', 'last_checked', 'session_expires')}
    result['retry_allowed'] = a.status == 'cancelled'
    result['session_unavailable'] = bool(json.loads(a.evidence or '{}').get('session_creation_failed'))
    result['resume_allowed'] = resumable(a)
    if a.status == 'pending' and a.last_checked:
        remaining = max(0, RECONCILE_INTERVAL - (now_datetime() - get_datetime(a.last_checked)).total_seconds())
        result['next_check_after'] = time.time() + remaining
    if a.status == 'failed' and any(
            app.get('name') == 'ics_arc' and str(app.get('reasonCode')) == '491'
            for app in json.loads(a.evidence or '{}').get('applications', [])):
        result['message'] = ('Payment was rejected by the acquiring bank or processor (code 491). '
                             'Your paid plan was not activated. Contact SISU support before retrying.')
    if a.status in ACTIVE and a.session_expires and not result['resume_allowed']:
        result['retry_after'] = float(a.session_expires) + 300
    return result


def unsubmitted(a):
    return (a.status == 'pending' and not a.transaction_id and not a.settlement_key
            and a.browser_event not in ('processing', 'completed'))


def undelivered_session(a):
    # A completed session-creation error never delivered a capture context to
    # the browser. Creating a context cannot itself authorize/capture a card.
    # Do not include 'creating': a provider request may still be in flight.
    return (a.status == 'review' and not a.session_token and not a.session_expires
            and not a.browser_event and not a.transaction_id and not a.settlement_key)


def resumable(a):
    return bool(unsubmitted(a) and a.session_token and float(a.session_expires or 0) > time.time())


def checkout_access(a, mode):
    """Resume one unsubmitted provider session, with one current submission grant.

    Rotating the grant invalidates older tabs. The processing endpoint consumes
    it atomically before the browser may call the provider's complete method.
    Neither a refresh nor a close creates a second provider payment session.
    """
    if not resumable(a):
        frappe.throw('This checkout cannot resume. Check its payment status.')
    evidence = json.loads(a.evidence or '{}')
    grant = uuid.uuid4().hex + uuid.uuid4().hex
    evidence.update(guarded_checkout=True, checkout_grant_hash=hashlib.sha256(grant.encode()).hexdigest())
    a.evidence = json.dumps(evidence)
    save(a)
    return dict(public(a), session=a.get_password('session_token'), mode=mode, submission_grant=grant)


def expired_unsubmitted(a):
    """A browser close is only a hint; never release a usable payment context."""
    expires = float(a.session_expires or 0)
    return (a.status == 'pending' and not a.transaction_id and not a.settlement_key
            and a.browser_event not in ('processing', 'completed') and expires > 0
            and expires + 300 <= time.time() <= expires + 6 * 86400)


def release_expired_empty(a, report):
    # A missing/malformed report, delayed result, or any transaction fails closed.
    if not expired_unsubmitted(a) or type(report.get('totalCount')) is not int or report['totalCount'] != 0:
        return False
    embedded = report.get('_embedded', {})
    if not isinstance(embedded, dict) or embedded.get('transactionSummaries'):
        return False
    lock_invoice(a.kind, a.invoice, for_reconciliation=True)
    a = frappe.get_doc(DT, a.name, for_update=True)
    if not expired_unsubmitted(a):
        return False
    a.status = 'cancelled'; a.active_key = None; save(a)
    from .saas import audit
    audit('Expired checkout cleared', a.name,
          'Session expired, reporting delay passed, and authenticated transaction search returned zero transactions. No payment recorded.')
    return True


@frappe.whitelist(methods=['POST'])
def availability(kind, invoice):
    _, _, scope, _, _ = source(kind, invoice, payable=False)
    root = frappe.conf.get('il_cybersource') or {}
    configured = (isinstance(root, dict) and root.get('enabled') is True
                  and root.get('mode') in ('sandbox', 'live')
                  and (root.get('mode') == 'sandbox' or root.get('live_checkout_approved') is True))
    result = {'captcha': captcha_settings(), 'paused': payment_paused(),
            'available': bool(not payment_paused() and configured and scope in (root.get('merchants') or {})),
            'mode': root.get('mode') if configured else 'unavailable'}
    if result['available'] and kind == 'subscription' and frappe.conf.get('il_local_card_test') is True:
        checkout_origin = settings(scope, for_reconciliation=True)['origin']
        current = str(getattr(getattr(frappe.local, 'request', None), 'host_url', '')).rstrip('/')
        if current != checkout_origin:
            result['checkout_url'] = checkout_origin + '/campus?' + urlencode({'checkout_invoice': invoice}) + '#subscription'
    return result


@frappe.whitelist(methods=['POST'])
def start(kind, invoice, captcha_token=None):
    if payment_paused():
        frappe.throw("Payment gateway isn't connected yet. Please try again later.")
    # Source invoice lock serializes creation across tabs and requests.
    lock_invoice(kind, invoice)
    doc, inst, scope, total, currency = source(kind, invoice)
    c = settings(scope)
    if currency != 'LKR':
        frappe.throw('SISU CyberSource checkout accepts LKR only')
    if currency not in c.get('currencies', ['LKR']):
        frappe.throw('This invoice currency has not been enabled for the merchant')
    active_key = kind + ':' + invoice
    existing = frappe.db.get_value(DT, {'active_key': active_key}, 'name')
    if existing:
        a = accessible(existing)
        a = frappe.get_doc(DT, a.name, for_update=True)
        if (a.merchant_id != c['merchant_id'] or attempt_environment(a) != c['mode']
                or a.amount_minor != total or a.currency != currency):
            frappe.throw('Checkout changed; reconcile the retained payment first')
        if undelivered_session(a):
            a.status = 'cancelled'; a.active_key = None; save(a)
            return dict(public(a), mode=c['mode'])
        if resumable(a):
            verify_checkout(captcha_token)
            return checkout_access(a, c['mode'])
        # A guarded session with no consumed submission grant was never sent for
        # processing by this integration. Once its context expires, renew it.
        if (unsubmitted(a) and 0 < float(a.session_expires or 0) <= time.time()
                and json.loads(a.evidence or '{}').get('guarded_checkout')):
            a.status = 'cancelled'; a.active_key = None; save(a)
            return dict(public(a), mode=c['mode'])
        # Legacy or uncertain sessions still require provider reconciliation.
        if expired_unsubmitted(a):
            return dict(reconcile(a.name), mode=c['mode'])
        return dict(public(a), mode=c['mode'])
    if kind == 'subscription' and frappe.db.exists(DT, {
            'customer': frappe.session.user, 'kind': 'subscription',
            'status': ['in', list(ACTIVE)], 'invoice': ['!=', invoice]}):
        frappe.throw('Your earlier subscription checkout still needs verification. Check its payment status before opening another checkout.')
    # Reopening/checking the retained attempt must not spend the session-creation
    # quota. Count only requests that can actually create a new gateway session.
    from .registration import limit
    try:
        limit('cybersource-start:' + frappe.session.user)
    except frappe.ValidationError:
        frappe.throw('Too many new payment sessions. Wait before opening another checkout; you can still check an existing payment.')
    verify_checkout(captcha_token)
    reference = 'sisu-' + uuid.uuid4().hex
    body = session_request(reference, total, currency, c['origin'], c['methods'])
    a = save(frappe.get_doc(dict(doctype=DT, reference=reference, active_key=active_key,
        kind=kind, invoice=invoice, institute=inst.name, customer=frappe.session.user,
        merchant_scope=scope, merchant_id=c['merchant_id'], amount_minor=total, currency=currency,
        status='creating', evidence=json.dumps({'environment': c['mode']}), request_snapshot=json.dumps(body))))
    # An ambiguous crash can never silently create a second active checkout.
    frappe.db.commit()
    try:
        token, claims = request(c, 'POST', '/uc/v1/sessions', body, token=True)
    except SessionRejected:
        a.status = 'failed'; a.active_key = None
        a.evidence = json.dumps({'environment': c['mode'], 'session_rejected': True})
        save(a); frappe.db.commit()
        return dict(public(a), session_rejected=True,
                    message='Checkout configuration was rejected. No payment session was opened. Contact SISU support.')
    except ProviderUnavailable as exc:
        # No verified context was saved or returned, so this attempt cannot have
        # submitted a payment. Explicit retries still use the session rate limit.
        a.status = 'failed'; a.active_key = None
        a.evidence = json.dumps({'environment': c['mode'], 'session_creation_failed': True,
                                'failure_code': getattr(exc, 'reason_code', 'provider_unavailable')})
        save(a); frappe.db.commit()
        return dict(public(a), message='Secure checkout could not connect. No payment was submitted. Please retry opening checkout.')
    a = frappe.get_doc(DT, a.name, for_update=True)
    a.session_token = token
    a.session_expires = claims['exp']
    a.status = 'pending'; save(a)
    return checkout_access(a, c['mode'])


@frappe.whitelist(methods=['POST'])
def browser_event(attempt, event, submission_grant=None):
    a = accessible(attempt)
    if event not in ('processing', 'completed', 'cancelled', 'failed'): frappe.throw('Invalid checkout event')
    a = frappe.get_doc(DT, a.name, for_update=True)
    if event == 'processing':
        evidence = json.loads(a.evidence or '{}')
        expected = evidence.get('checkout_grant_hash')
        supplied = hashlib.sha256(str(submission_grant or '').encode()).hexdigest()
        if not resumable(a) or not expected or not hmac.compare_digest(expected, supplied):
            frappe.throw('This checkout was reopened elsewhere or already submitted. Return to your latest checkout or check payment status.')
        evidence.pop('checkout_grant_hash', None)
        a.evidence = json.dumps(evidence)
    # A late close/error event cannot erase the fact that payment was submitted.
    if a.browser_event != 'completed' and not (a.browser_event == 'processing' and event != 'completed'):
        a.browser_event = event; save(a)
    # Client failure/cancel cannot mark a financial transaction failed or free its key.
    return public(a)


@frappe.whitelist(methods=['POST'])
def status(attempt):
    return public(accessible(attempt))


@frappe.whitelist(methods=['POST'])
def reconcile(attempt):
    a = accessible(attempt)
    c = settings(a.merchant_scope, for_reconciliation=True)
    if a.merchant_id != c['merchant_id'] or attempt_environment(a) != c['mode']:
        frappe.throw('Merchant or environment changed; restore the original payment configuration')
    # Lock before checking the cooldown; concurrent polls must not multiply provider requests.
    a = frappe.get_doc(DT, a.name, for_update=True)
    if a.status in ('succeeded', 'failed', 'cancelled'): return public(a)
    if a.last_checked and (now_datetime() - get_datetime(a.last_checked)).total_seconds() < RECONCILE_INTERVAL:
        return dict(public(a), message='Payment confirmation is still pending. Check again shortly; do not pay again.')
    a.last_checked = now_datetime(); save(a); frappe.db.commit()
    try:
        result = request(c, 'POST', '/tss/v2/searches', {
            'save': False, 'query': 'clientReferenceInformation.code:' + a.reference,
            'offset': 0, 'limit': 10, 'sort': 'submitTimeUtc:desc'})
        if release_expired_empty(a, result):
            return dict(public(frappe.get_doc(DT, a.name)),
                        message='Checkout closed without a recorded payment. You can open a new checkout safely.')
        embedded = result.get('_embedded', {})
        if not isinstance(embedded, dict):
            raise ValueError('Invalid transaction report')
        summaries = embedded.get('transactionSummaries', [])
        if (not isinstance(summaries, list) or not summaries or len(summaries) > 10
                or ('totalCount' in result and (type(result['totalCount']) is not int
                                               or result['totalCount'] != len(summaries)))):
            return dict(public(a), message='Awaiting an unambiguous CyberSource transaction report; do not pay again.')
        candidates = []; seen = set()
        for summary in summaries:
            transaction_id = str(summary.get('id', ''))
            if transaction_id in seen:
                raise ValueError('Duplicate transaction report')
            seen.add(transaction_id)
            data = request(c, 'GET', '/tss/v2/transactions/' + transaction_id)
            if (str(data.get('id')) != transaction_id or data.get('merchantId') != a.merchant_id
                    or data.get('clientReferenceInformation', {}).get('code') != a.reference):
                raise ValueError('Transaction lookup binding mismatch')
            if not authentication_only(data):
                candidates.append(data)
        # A single checkout legitimately includes setup and challenge records.
        # Still require exactly one financial record; never pick a success from
        # multiple charges, reversals or unrelated/malformed records.
        if len(candidates) != 1:
            return dict(public(a), message='Awaiting an unambiguous CyberSource payment report; do not pay again.')
        data = candidates[0]; transaction_id = str(data['id'])
        outcome = verify_transaction(data, {'merchant_id': a.merchant_id, 'reference': a.reference,
                                            'currency': a.currency, 'amount_minor': a.amount_minor})
    except (ProviderUnavailable, ValueError, TypeError, KeyError):
        return dict(public(a), message='Payment verification is pending. No access has been activated.')
    lock_invoice(a.kind, a.invoice, for_reconciliation=True)
    a = frappe.get_doc(DT, a.name, for_update=True)
    if a.status == 'succeeded': return public(a)
    a.transaction_id = transaction_id
    a.evidence = json.dumps({'environment': c['mode'], 'id': transaction_id, 'merchantId': data.get('merchantId'),
        'clientReferenceInformation': data.get('clientReferenceInformation'),
        'applications': data.get('applicationInformation', {}).get('applications'),
        'paymentSolution': data.get('processingInformation', {}).get('paymentSolution')})
    if outcome == 'succeeded':
        # Save the unique merchant+transaction identity before financial effects.
        a.settlement_key = hashlib.sha256((a.merchant_id + ':' + transaction_id).encode()).hexdigest()
        save(a)
        doc, _, _, total, currency = source(a.kind, a.invoice, payable=False)
        payable_states = ('Draft', 'Unpaid', 'Overdue') if a.kind == 'subscription' else ('Unpaid', 'Overdue')
        if total != a.amount_minor or currency != a.currency or doc.status not in payable_states:
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
    mode = attempt_environment(a)
    reference = ('cybs-live:' if mode == 'live' else 'cybs-sandbox:') + a.settlement_key
    if a.kind == 'subscription':
        from .account_billing import record_verified_payment
        record_verified_payment(a.invoice, reference, a.amount_minor, a.currency, 'CyberSource ' + mode)
    elif a.kind == 'usage':
        from .usage_billing import record_verified_payment
        record_verified_payment(a.invoice, reference, doc.amount_lkr, 'CyberSource ' + mode + ' authorization and capture verified', remote_reviewer='CyberSource ' + mode)
    elif a.kind == 'platform':
        from .commercial import save as provider_save
        doc.update(dict(status='Paid', payment_reference=reference, settlement_key=a.settlement_key,
                   paid_at=now_datetime(), receipt_number='RC-' + doc.name, payment_channel='CyberSource ' + mode))
        provider_save(doc)
    else:
        doc.update(dict(status='Paid', payment_id=reference, paid_at=now_datetime(),
                   receipt_number='RC-' + doc.name, gateway_status='cybersource:' + mode + ':captured'))
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
    c = settings(a.merchant_scope, for_reconciliation=True)
    if c['merchant_id'] != a.merchant_id or attempt_environment(a) != c['mode']:
        frappe.throw('Restore the original merchant environment')
    result = request(c, 'POST', '/tss/v2/searches', {
        'save': False, 'query': 'clientReferenceInformation.code:' + a.reference,
        'offset': 0, 'limit': 10, 'sort': 'submitTimeUtc:desc'})
    if result.get('totalCount') != 0:
        frappe.throw('Cannot confirm an empty transaction report; reconcile this attempt')
    lock_invoice(a.kind, a.invoice, for_reconciliation=True)
    a = frappe.get_doc(DT, attempt, for_update=True)
    if a.status not in ACTIVE or a.transaction_id or a.settlement_key:
        frappe.throw('Attempt changed; review its latest status')
    a.status = 'cancelled'; a.active_key = None; save(a)
    audit('Close unpaid CyberSource attempt', a.name, reason.strip()[:1000])
    return public(a)
