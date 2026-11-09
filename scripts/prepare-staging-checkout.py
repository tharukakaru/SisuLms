"""Provision one staging-only teacher/invoice and enable sandbox checkout there."""
import getpass
import json
import os
import warnings
from datetime import datetime, timezone, timedelta
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
SITE = 'staging.sisuacademylk.com'
EMAIL = 'sisu.student.test+hnb@gmail.com'


def private_write(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        stream.write(data)


def main():
    if Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.chdir(BENCH / 'sites')
    config_path = BENCH / 'sites' / SITE / 'site_config.json'
    original = config_path.read_text()
    config = json.loads(original)
    gateway = config.get('il_cybersource') or {}
    merchant = (gateway.get('merchants') or {}).get('platform') or {}
    if gateway.get('mode') != 'sandbox' or gateway.get('origin') != 'https://' + SITE or merchant.get('merchant_id') != 'sisu_academy_1793191054':
        raise RuntimeError('Unexpected sandbox settings')
    import frappe
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    try:
        if frappe.conf.get('il_shared_campus_enabled') or frappe.conf.get('il_control_plane'):
            raise RuntimeError('Expected single-institute staging site')
        # Unpausing must not activate an unrelated configured gateway.
        if any(frappe.conf.get(k) for k in ('il_payments_lk_secret_key', 'il_payhere_secret')):
            raise RuntimeError('Another payment adapter is configured; review before enabling')
        institutes = frappe.get_all('IL Institute', pluck='name', limit_page_length=2)
        if len(institutes) != 1:
            raise RuntimeError('Expected exactly one staging institute')
        frappe.set_user('Administrator')
        from institute_lms.account_billing import account, save
        from institute_lms.account_billing_rules import VERSION
        marker = 'SISU HNB SANDBOX TEST ONLY'
        user_exists = bool(frappe.db.exists('User', EMAIL))
        if user_exists and frappe.db.get_value('User', EMAIL, 'first_name') != marker:
            raise RuntimeError('Existing non-fixture account; stopped')
        if not user_exists:
            with warnings.catch_warnings():
                warnings.simplefilter('error', getpass.GetPassWarning)
                password = getpass.getpass('New staging test teacher password (12+ characters, hidden): ')
                confirm = getpass.getpass('Confirm password (hidden): ')
            if len(password) < 12 or password != confirm:
                raise RuntimeError('Passwords must match and contain at least 12 characters')
            user = frappe.get_doc(dict(doctype='User', email=EMAIL, first_name=marker,
                enabled=1, user_type='Website User', send_welcome_email=0))
            user.insert(ignore_permissions=True)
            from frappe.utils.password import update_password
            update_password(EMAIL, password)
        member_name = frappe.db.get_value('IL Member', {'user': EMAIL, 'institute': institutes[0]}, 'name')
        if member_name:
            member = frappe.get_doc('IL Member', member_name)
            if member.role != 'Teacher' or not member.active:
                raise RuntimeError('Fixture membership changed')
        else:
            member = frappe.get_doc(dict(doctype='IL Member', institute=institutes[0], user=EMAIL,
                role='Teacher', full_name=marker, active=1, language='en')).insert(ignore_permissions=True)
        inst = frappe.get_doc('IL Institute', institutes[0])
        subscription = account(inst, member, create=True, lock=True)
        existing = frappe.db.get_value('IL Account Invoice', {'subscription': subscription.name}, 'name')
        if existing:
            bill = frappe.get_doc('IL Account Invoice', existing)
            if bill.billed_to != marker or bill.currency != 'LKR' or int(bill.amount_minor) != 100:
                raise RuntimeError('Existing invoice differs from fixture')
        else:
            from frappe.utils import now_datetime
            start = now_datetime()
            bill = save(frappe.get_doc(dict(doctype='IL Account Invoice', subscription=subscription.name,
                open_key=subscription.name, plan=subscription.plan, country='LK', currency='LKR',
                amount_minor=100, period_start=start, period_end=start + timedelta(days=30),
                anchor_day=start.day, status='Unpaid', version=VERSION, billed_to=marker, billing_email=EMAIL)))
        # Verify actual invoice authorization before publishing configuration.
        frappe.set_user(EMAIL)
        from institute_lms.cybersource import source
        _, _, scope, total, currency = source('subscription', bill.name, payable=bill.status == 'Unpaid')
        if (scope, total, currency) != ('platform', 100, 'LKR'):
            raise RuntimeError('Fixture invoice authorization failed')
        private = Path.home() / '.sisu-secrets' / 'hnb-checkout'
        private.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(private, 0o700)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        private_write(private / (stamp + '-site-config.json'), original)
        if config_path.read_text() != original:
            raise RuntimeError('Configuration changed concurrently')
        gateway['enabled'] = True
        config['il_payments_paused'] = False
        temporary = config_path.with_name('site_config.hnb-checkout.tmp')
        private_write(temporary, json.dumps(config, indent=2))
        # Commit fixture first: a later configuration failure leaves payments paused.
        frappe.db.commit()
        os.replace(temporary, config_path)
        print('PREPARED: staging sandbox teacher ' + EMAIL)
        print('TEST INVOICE: ' + bill.name + '; LKR 1.00; status ' + bill.status)
        print('ENABLED: Cybersource sandbox on staging only. Restart web before browser testing.')
        print('OPEN: https://' + SITE + '/campus#subscription')
        print('Public/Teen/platform settings unchanged. No payment submitted or notification requested.')
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Only this script's fixed RuntimeError messages are suitable for display.
        detail = str(exc) if type(exc) is RuntimeError and exc.__traceback__.tb_next and exc.__traceback__.tb_next.tb_next is None else type(exc).__name__
        raise SystemExit('STOPPED: ' + detail + '. No secrets displayed.') from None
