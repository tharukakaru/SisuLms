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
    return send_config(config,phone,message)


def send_config(config,phone,message):
    if not all(config.get(k) for k in ('user_id', 'api_key', 'sender_id')):
        frappe.throw('SMS provider is not configured')
    if config['sender_id'].lower() == 'notifydemo':
        frappe.throw('Configure an approved sender before enabling SMS verification')
    number = str(phone).lstrip('+')
    if not re.fullmatch(r'94\d{9}', number):
        frappe.throw('Notify SMS requires a Sri Lankan phone number')
    from institute_lms.message_templates import format_sms
    text = format_sms(message)
    if len(text) > 621:
        frappe.throw('SMS is too long')
    payload = {k:config[k] for k in ('user_id','api_key','sender_id')}
    payload.update(to=number,message=text)
    if not text.isascii():
        payload['type'] = 'unicode'
    try:
        response = requests.post('https://app.notify.lk/api/v1/send', data=payload,
                                 timeout=(5, 15), allow_redirects=False)
        value = response.json()
        confirmed = response.ok and isinstance(value,dict) and value.get('status') == 'success' and value.get('data') == 'Sent'
    except (requests.RequestException, ValueError) as exc:
        log_failure(exc, locals().get('response'), config)
        try:
            if getattr(frappe.local,'site',None)=='sisuacademylk.com':
                response_value=locals().get('response')
                frappe.cache.set_value('il_public_sms_last_failure',{'error_type':type(exc).__name__,
                    'http_status':getattr(response_value,'status_code',None)},expires_in_sec=3600)
        except Exception:
            pass
        frappe.throw('SMS acceptance is uncertain; reconcile before retrying')
    if not confirmed:
        log_failure(None, response, config)
        frappe.throw('SMS provider did not confirm acceptance')
    return {'accepted':True, 'provider':'notify.lk', 'provider_id':None}


def log_failure(exc, response, config):
    """Record what Notify returned (never the API key) so failures can be diagnosed."""
    try:
        body = str(getattr(response, 'text', '') or '')[:500].replace(str(config.get('api_key') or '~'), '***')
        detail = {'site': getattr(frappe.local, 'site', None), 'error': type(exc).__name__ if exc else None,
                  'error_text': str(exc)[:300].replace(str(config.get('api_key') or '~'), '***') if exc else None,
                  'http_status': getattr(response, 'status_code', None),
                  'content_type': getattr(response, 'headers', {}).get('content-type') if response is not None else None,
                  'body': body}
        frappe.cache.set_value('il_sms_last_failure', detail, expires_in_sec=86400)
        frappe.logger('notify_sms').warning(detail)
    except Exception:
        pass
