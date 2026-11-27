"""Google reCAPTCHA v2 checkbox verification for opening card checkout."""
from datetime import datetime,timezone
import requests
import frappe


def configuration():
    config=frappe.conf.get('il_checkout_recaptcha') or {}
    return config if isinstance(config,dict) else {}


def public_settings():
    config=configuration()
    enabled=config.get('enabled') is True
    ready=bool(config.get('site_key') and config.get('secret_key') and config.get('hostnames'))
    return dict(required=enabled,configured=enabled and ready,site_key=config.get('site_key','') if enabled and ready else '')


def verify(token):
    config=configuration()
    if config.get('enabled') is not True:return
    if not public_settings()['configured']:
        frappe.throw('Checkout verification is not configured. Please contact SISU support.')
    if not isinstance(token,str) or not 20<=len(token)<=8192:
        frappe.throw('Complete the “I’m not a robot” verification before opening checkout.')
    # Fixed HTTPS destination, bounded timeout, no redirects, no token logging.
    try:
        response=requests.post('https://www.google.com/recaptcha/api/siteverify',
            data={'secret':config['secret_key'],'response':token},timeout=(3,6),allow_redirects=False)
        response.raise_for_status()
        result=response.json()
        timestamp=datetime.fromisoformat(str(result.get('challenge_ts','')).replace('Z','+00:00'))
        age=(datetime.now(timezone.utc)-timestamp).total_seconds()
        hosts=config['hostnames']
        valid=(isinstance(hosts,list) and result.get('success') is True
               and result.get('hostname') in hosts and 0<=age<=120)
    except (requests.RequestException,ValueError,TypeError,AttributeError):
        frappe.throw('Verification could not be completed. Please retry the checkbox.')
    if not valid:
        frappe.throw('Verification expired or was rejected. Please complete the checkbox again.')
