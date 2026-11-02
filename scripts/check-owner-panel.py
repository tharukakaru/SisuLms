"""Read-only Frappe acceptance checks for the deployed control-plane owner panel."""
import logging
import os
from pathlib import Path
BENCH=Path('/home/sisu/frappe-bench')
SITE='platform.sisuacademylk.com'
USER='gro4celk@gmail.com'

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):
        raise RuntimeError('Run as sisu on the SISU server')
    logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH/'sites')
    frappe.init(site=SITE,sites_path=str(BENCH/'sites'))
    try:
        frappe.connect()
        from institute_lms import release,platform,owner_access,premium,subscription_payments
        frappe.set_user(USER)
        if not frappe.conf.get('il_control_plane') or not owner_access.is_owner():
            raise RuntimeError('Requested account lacks control-plane owner access')
        if not frappe.conf.get('il_payments_paused'):
            raise RuntimeError('Payment pause must remain enabled')
        data=release.control_room()
        assert isinstance(data['organizations'],list) and isinstance(data['plans'],list)
        print('PASS: owner registry, plans and provisioning read APIs.')
        for org in data['organizations']:
            summary=premium.summary(org['name'])
            assert 'offer' in summary and 'receipts' in summary
        for job in data['jobs']:
            spec=platform.provisioning_spec(job['name'])
            assert spec['job']==job['name']
        print('PASS: visible organization summaries, receipts and provisioning specs.')
        assert release.billing()['payments_paused'] is True
        assert isinstance(platform.audit_log(),list)
        access=owner_access.access_list()
        assert access['can_manage']==(USER==owner_access.primary_email())
        print('PASS: billing pause, audit history and primary-owner access boundary.')
        try:subscription_payments.config()
        except Exception as exc:
            if str(exc)!='Payments are paused':raise RuntimeError('Unexpected payment guard response') from None
        else:raise RuntimeError('Paused subscription checkout was not blocked')
        frappe.set_user('Guest')
        for endpoint in (release.control_room,platform.audit_log,owner_access.access_list):
            try:endpoint()
            except frappe.PermissionError:pass
            else:raise RuntimeError('Guest access was not denied')
        print('PASS: guest cannot read owner registry, audit history or administrator list.')
        print('READ ONLY: no records saved, emails/SMS sent, policy issued or configuration changed.')
        print('Browser Google login and real mutation/delivery acceptance remain separate checks.')
    finally:
        frappe.db.rollback()
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__)+'. No credentials or raw records displayed.')
        raise SystemExit(1) from None
