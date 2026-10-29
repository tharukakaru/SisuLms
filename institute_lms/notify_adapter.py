"""Notify.lk acceptance adapter; acceptance is not a delivery receipt.

Notify's API returns no message ID and has no documented idempotency support.
The notification outbox commits Review before calling us and never retries an
ambiguous send automatically.
"""
import re
import requests
import frappe


def send(phone, message, idempotency_key=None):
    config = frappe.conf.get('il_notify') or {}
    if not all(config.get(k) for k in ('user_id', 'api_key', 'sender_id')):
        frappe.throw('SMS provider is not configured')
    if config['sender_id'].lower() == 'notifydemo':
        frappe.throw('Configure an approved sender before enabling SMS verification')
    number = str(phone).lstrip('+')
    if not re.fullmatch(r'94\d{9}', number):
        frappe.throw('Notify SMS requires a Sri Lankan phone number')
    text = 'SISU: ' + str(message)
    if len(text) > 621:
        frappe.throw('SMS is too long')
    payload = {**config, 'to':number, 'message':text}
    if not text.isascii():
        payload['type'] = 'unicode'
    try:
        response = requests.post('https://app.notify.lk/api/v1/send', data=payload,
                                 timeout=(5, 15), allow_redirects=False)
        value = response.json()
        confirmed = response.ok and value.get('status') == 'success' and value.get('data') == 'Sent'
    except (requests.RequestException, ValueError):
        frappe.throw('SMS acceptance is uncertain; reconcile before retrying')
    if not confirmed:
        frappe.throw('SMS provider did not confirm acceptance')
    return {'accepted':True, 'provider':'notify.lk', 'provider_id':None}
