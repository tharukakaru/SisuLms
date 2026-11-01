"""Authenticated Meta ingress. Acknowledgement means durably received, not sent."""
import hashlib
import hmac
import json
import frappe
from werkzeug.wrappers import Response

MAX_BODY = 262144
RANK = {'Accepted': 0, 'Failed': 1, 'Delivered': 2, 'Read': 3}
STATES = {'sent': 'Accepted', 'failed': 'Failed', 'delivered': 'Delivered', 'read': 'Read'}


def valid_signature(raw, secret, signature):
    if not isinstance(secret, str) or not secret or len(raw) > MAX_BODY:
        return False
    expected = 'sha256=' + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return isinstance(signature, str) and hmac.compare_digest(expected.encode(), signature.encode())


def events(data, waba, phone):
    if not isinstance(data, dict) or data.get('object') != 'whatsapp_business_account':
        raise ValueError('Invalid webhook object')
    for entry in data.get('entry', []):
        if str(entry.get('id')) != waba:
            continue
        for change in entry.get('changes', []):
            value = change.get('value', {})
            if change.get('field') != 'messages' or value.get('messaging_product') != 'whatsapp':
                continue
            if str(value.get('metadata', {}).get('phone_number_id')) != phone:
                continue
            for kind in ('statuses', 'messages'):
                for row in value.get(kind, []):
                    if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'] or len(row['id']) > 255:
                        raise ValueError('Invalid message ID')
                    if kind == 'statuses' and row.get('status') not in STATES:
                        continue
                    # Never persist arbitrary attachment URLs or download incoming media.
                    clean = {k: row[k] for k in ('id', 'timestamp', 'status', 'type', 'from', 'recipient_id') if k in row}
                    if kind == 'messages' and row.get('type') == 'text':
                        clean['text'] = str(row.get('text', {}).get('body', ''))[:4096]
                    identity = [waba, phone, kind, row['id'], row.get('status', '') if kind == 'statuses' else '']
                    key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
                    yield key, kind, clean


def handle():
    request = frappe.request
    if request.method == 'GET':
        token = frappe.conf.get('il_whatsapp_verify_token')
        supplied = request.args.get('hub.verify_token', '')
        challenge = request.args.get('hub.challenge', '')
        if not isinstance(token, str) or not token or not hmac.compare_digest(token.encode(), supplied.encode()):
            return Response('Forbidden', status=403)
        if request.args.get('hub.mode') != 'subscribe' or not challenge or len(challenge) > 512:
            return Response('Invalid challenge', status=400)
        return Response(challenge, mimetype='text/plain')
    if request.method != 'POST':
        return Response('Method not allowed', status=405)
    if request.content_length and request.content_length > MAX_BODY:
        return Response('Payload too large', status=413)
    raw = request.get_data(cache=True)
    if not valid_signature(raw, frappe.conf.get('il_whatsapp_app_secret'), request.headers.get('X-Hub-Signature-256')):
        return Response('Forbidden', status=403)
    waba = str(frappe.conf.get('il_whatsapp_waba_id') or '')
    phone = str(frappe.conf.get('il_whatsapp_phone_id') or '')
    if not waba or not phone:
        return Response('Webhook not configured', status=503)
    try:
        batch = list(events(json.loads(raw), waba, phone))
    except (ValueError, TypeError, AttributeError):
        return Response('Invalid payload', status=400)
    if not batch:
        return Response('EVENT_RECEIVED', mimetype='text/plain')
    from .api import institute
    inst = institute()  # Exactly one institute per Frappe site; never trust payload tenant IDs.
    for key, kind, payload in batch:
        doc = frappe.get_doc(dict(doctype='IL WhatsApp Receipt', name=key,
            institute=inst.name, kind=kind, payload=json.dumps(payload),
            state='Pending' if kind == 'statuses' else 'Received'))
        doc.flags.whatsapp_service = True
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
        if kind == 'statuses':
            process_status(key)
    # Explicit durable acknowledgement. Failures before here propagate and Meta can retry.
    frappe.db.commit()
    return Response('EVENT_RECEIVED', mimetype='text/plain')


def process_status(name):
    receipt = frappe.get_doc('IL WhatsApp Receipt', name, for_update=True)
    if receipt.state != 'Pending':
        return
    row = json.loads(receipt.payload)
    names = frappe.get_all('IL Notification', filters={'channel': 'WhatsApp',
        'provider_id': row['id'], 'institute': receipt.institute}, pluck='name', limit_page_length=2)
    # A callback can arrive before the sender commits provider_id. Retain and retry.
    if len(names) != 1:
        return
    delivery = frappe.get_doc('IL Notification', names[0], for_update=True)
    if delivery.institute != receipt.institute or delivery.provider_id != row['id'] or delivery.channel != 'WhatsApp':
        return
    member = frappe.get_doc('IL Member', delivery.recipient)
    if member.institute != receipt.institute or str(member.phone or '').lstrip('+') != str(row.get('recipient_id', '')):
        return
    target = STATES[row['status']]
    if RANK.get(target, -1) > RANK.get(delivery.status, -1):
        delivery.status = target
        delivery.save(ignore_permissions=True)
    receipt.state = 'Processed'
    receipt.flags.whatsapp_service = True
    receipt.save(ignore_permissions=True)


def reconcile():
    for name in frappe.get_all('IL WhatsApp Receipt', filters={'kind': 'statuses', 'state': 'Pending'},
                              pluck='name', limit_page_length=100, order_by='modified asc'):
        process_status(name)
