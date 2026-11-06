"""Close only the reviewed, expired staging test attempt via the billing service."""
import math
import os
import time
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')


def main():
    if Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.chdir(BENCH / 'sites')
    import frappe
    frappe.init(site='staging.sisuacademylk.com', sites_path=str(BENCH / 'sites'))
    frappe.connect()
    try:
        from institute_lms.owner_access import primary_email, is_owner
        owner = primary_email()
        if not is_owner(owner):
            raise RuntimeError('Configured staging owner unavailable')
        frappe.set_user(owner)
        attempt = frappe.get_doc('IL CyberSource Attempt', 'i574va110s')
        if (attempt.invoice != 'fm34oisjhc' or attempt.customer != 'sisu.student.test+hnb@gmail.com'
                or attempt.kind != 'subscription' or attempt.merchant_id != 'sisu_academy_1793191054'):
            raise RuntimeError('Test attempt identity mismatch')
        if attempt.status == 'cancelled' and not attempt.active_key:
            print('ALREADY CLOSED: hard-refresh staging and open the existing invoice.')
            return
        expires = float(attempt.session_expires or 0)
        if not expires:
            raise RuntimeError('Unknown expiry; manual investigation required')
        wait = math.ceil(expires + 300 - time.time())
        if wait > 0:
            print('WAIT: session expiry and reporting delay; retry this command in ' + str(wait) + ' seconds.')
            return
        from institute_lms.cybersource import settings, close_unpaid
        from institute_lms.cybersource_transport import request
        result = request(settings(attempt.merchant_scope), 'POST', '/tss/v2/searches',
            {'save': False, 'query': 'clientReferenceInformation.code:' + attempt.reference,
             'offset': 0, 'limit': 10, 'sort': 'submitTimeUtc:desc'})
        if result.get('totalCount') != 0:
            raise RuntimeError('Empty transaction report not confirmed; attempt retained')
        print('PASS: expired session; authenticated search reports zero transactions.')
        print('Review this reference in sandbox Business Center Transaction Management: ' + attempt.reference)
        answer = input('Only after confirming no payment there, type NO PAYMENT (otherwise press Enter): ').strip()
        if answer != 'NO PAYMENT':
            print('UNCHANGED: attempt retained.')
            return
        close_unpaid(attempt.name, 'Operator reviewed sandbox Business Center for reference ' + attempt.reference
                     + ' and confirmed no payment; authenticated search also empty after expiry and reporting delay.')
        frappe.db.commit()
        print('CLOSED: failed staging attempt retained as cancelled; invoice still unpaid.')
        print('NEXT: hard-refresh staging; click Pay online once on invoice fm34oisjhc.')
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        raise SystemExit('STOPPED: ' + type(exc).__name__ + '; attempt not cleared by this command.') from None
