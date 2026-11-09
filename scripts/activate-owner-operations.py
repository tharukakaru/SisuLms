import os,json
from pathlib import Path
from datetime import datetime,timezone
BENCH=Path('/home/sisu/frappe-bench');SITE='platform.sisuacademylk.com'
def main():
    if Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    os.umask(0o077);os.chdir(BENCH/'sites')
    config_path=BENCH/'sites'/SITE/'site_config.json'
    if config_path.is_symlink():raise RuntimeError('Unexpected configuration symlink')
    old=config_path.read_bytes();config=json.loads(old)
    if not config.get('il_control_plane'):raise RuntimeError('Expected owner site')
    configured=['sisuacademylk.com','teen.sisuacademylk.com']
    existing=config.get('il_owner_reporting_sites')
    if existing and existing!=configured:raise RuntimeError('Review existing reporting configuration before replacing it')
    root=Path.home()/'.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:raise RuntimeError('Private backup directory required')
    backup=root/('owner-reporting-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    backup.write_bytes(old);backup.chmod(0o600)
    import frappe
    from institute_lms import owner_operations
    # Verify both sources before enabling the persistent configuration.
    frappe.init(site=SITE);frappe.connect()
    try:
        frappe.set_user('sisu.student.test+platform.owner@gmail.com')
        frappe.conf['il_owner_reporting_sites']=configured
        for site in configured:
            report=owner_operations.billing(site=site)
            assert report['configured'] and report['site']==site
        config['il_owner_reporting_sites']=configured
        temporary=config_path.with_suffix('.owner-report-tmp');temporary.write_text(json.dumps(config,indent=2));temporary.chmod(0o600);os.replace(temporary,config_path)
        frappe.clear_cache()
    except Exception:
        config_path.write_bytes(old);config_path.chmod(0o600)
        raise
    finally:frappe.db.rollback();frappe.destroy()
    print('ACTIVATED: owner-only read-only public and Teen campus billing reports. No invoice, account, payment or message changed.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__))
        raise SystemExit(1) from None
