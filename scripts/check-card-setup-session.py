"""Probe sandbox Sessions acceptance only; never authorizes a card or starts a trial.

Run as the bench user. The short-lived session token is deliberately not printed
or persisted. A passing result is NOT evidence of card verification/TMS activation.
"""
import json
import os
import uuid

os.chdir('/home/sisu/frappe-bench/sites')
import frappe
from institute_lms.cybersource_contract import session_request
from institute_lms.cybersource_transport import request, ProviderUnavailable


def main():
    frappe.init(site='sisuacademylk.com')
    frappe.connect()
    try:
        root = frappe.conf.get('il_cybersource') or {}
        merchant = (root.get('merchants') or {}).get('platform') or {}
        if root.get('mode') != 'sandbox' or root.get('enabled') is not True:
            raise RuntimeError('Enabled sandbox configuration required')
        if not all(merchant.get(k) for k in ('merchant_id', 'key_id', 'p12_path', 'p12_password')):
            raise RuntimeError('Sandbox credentials are incomplete')
        if 'PANENTRY' not in merchant.get('methods', []):
            raise RuntimeError('PANENTRY must be enabled')
        body = session_request('sisu-' + uuid.uuid4().hex, 1, 'LKR', root['origin'], ['PANENTRY'])
        body['data']['orderInformation']['amountDetails']['totalAmount'] = '0.00'
        body['captureMandate']['requestSaveCredentials'] = True
        body['completeMandate'] = {
            'type': 'AUTH', 'consumerAuthentication': '3DS',
            'tms': {'tokenCreate': True,
                    'tokenTypes': ['customer', 'paymentInstrument', 'instrumentIdentifier']},
        }
        config = dict(merchant, mode='sandbox', origin=root['origin'])
        try:
            token, claims = request(config, 'POST', '/uc/v1/sessions', body, token=True)
        except ProviderUnavailable:
            print('NOT CONFIRMED: sandbox did not return a valid card-setup session. No trial activated.')
            return 2
        del token, claims
        print('PASS: sandbox accepted a zero-value AUTH session requesting consent and TMS tokens.')
        print('PENDING: actual card authorization, saved-token verification, trial activation and reminder delivery still require implementation/testing.')
        print('No card submitted, charge made, token stored, trial started, account changed or message sent.')
        return 0
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    raise SystemExit(main())
