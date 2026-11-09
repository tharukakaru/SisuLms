"""Enable only heartbeat and approved owner invitations on the owner site."""
import os,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
BENCH=Path('/home/sisu/frappe-bench');APP=BENCH/'apps/institute_lms';SITE='platform.sisuacademylk.com'
METHOD='institute_lms.owner_invitation_delivery.dispatch'
ALLOWED={'institute_lms.health.heartbeat',METHOD}
HOOK="scheduler_events['cron'].setdefault('*/1 * * * *', []).append('institute_lms.owner_invitation_delivery.dispatch')"

def main():
    if Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    os.umask(0o077);os.chdir(BENCH/'sites')
    source=Path('/tmp/owner_invitation_delivery.py').read_bytes()
    if hashlib.sha256(source.replace(b'\r\n',b'\n')).hexdigest()!='7e29c4f725192d9b44bb47e3e54ab3245ecb3ef5411c3cdc79b3c0bd498022b0':raise RuntimeError('Invitation service payload mismatch')
    import frappe
    frappe.init(site=SITE);frappe.connect()
    target=APP/'institute_lms/owner_invitation_delivery.py';hooks=APP/'institute_lms/hooks.py';configpath=BENCH/'sites'/SITE/'site_config.json'
    if any(p.is_symlink() for p in (target,hooks,configpath)):raise RuntimeError('Unexpected symlink')
    oldconfig=configpath.read_bytes();config=json.loads(oldconfig);oldhooks=hooks.read_bytes();oldmodule=target.read_bytes() if target.exists() else None
    committed=False
    try:
        if not config.get('il_control_plane') or not config.get('il_payments_paused'):raise RuntimeError('Expected owner site with payment hold')
        if config.get('pause_scheduler') or config.get('disable_scheduler') or config.get('maintenance_mode'):raise RuntimeError('Owner site has another operator hold; review before enabling')
        if not frappe.db.get_default('suspend_email_queue'):raise RuntimeError('General mail hold must remain enabled')
        if oldmodule is not None and oldmodule.replace(b'\r\n',b'\n')!=source.replace(b'\r\n',b'\n'):raise RuntimeError('Existing invitation delivery source differs; review first')
        rows=frappe.get_all('Scheduled Job Type',fields=['name','method','stopped'])
        if not any(r.method=='institute_lms.health.heartbeat' for r in rows):raise RuntimeError('Heartbeat job is not registered')
        root=Path.home()/'.sisu-secrets'
        if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:raise RuntimeError('Private backup directory required')
        backup=root/('owner-invitation-service-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));backup.mkdir(mode=0o700)
        (backup/'site_config.json').write_bytes(oldconfig);(backup/'hooks.py').write_bytes(oldhooks)
        (backup/'scheduler.json').write_text(json.dumps({'enable_scheduler':frappe.db.get_single_value('System Settings','enable_scheduler'),'jobs':rows},default=str))
        if oldmodule is not None:(backup/'owner_invitation_delivery.py').write_bytes(oldmodule)
        target.write_bytes(source);target.chmod(0o644)
        text=oldhooks.decode('utf-8-sig')
        if HOOK not in text:hooks.write_text(text+'\n# Scoped owner invitations; dispatcher is a no-op on campus sites.\n'+HOOK+'\n');hooks.chmod(0o644)
        name=frappe.db.get_value('Scheduled Job Type',{'method':METHOD},'name')
        if not name:
            frappe.get_doc({'doctype':'Scheduled Job Type','method':METHOD,'frequency':'Cron','cron_format':'*/1 * * * *','stopped':0}).insert(ignore_permissions=True)
        for row in frappe.get_all('Scheduled Job Type',fields=['name','method']):
            frappe.db.set_value('Scheduled Job Type',row.name,'stopped',0 if row.method in ALLOWED else 1,update_modified=False)
        config['il_owner_invitation_delivery_enabled']=1
        temporary=configpath.with_suffix('.invitation-tmp');temporary.write_text(json.dumps(config,indent=2));temporary.chmod(0o600);os.replace(temporary,configpath)
        frappe.db.set_single_value('System Settings','enable_scheduler',1)
        frappe.clear_cache();frappe.db.commit();committed=True
        print('ENABLED: owner-site heartbeat and fresh access-invitation delivery only.')
        print('HELD: general email queue, all other owner scheduled jobs, public/Teen scheduling and all payment settings unchanged.')
        print('No email sent by this installer. The scheduled invitation worker may deliver fresh authorized invitations after restart. Old invitations are skipped; request a fresh one in the UI.')
        print('Private backup:',str(backup))
    except Exception:
        if committed:raise
        frappe.db.rollback();configpath.write_bytes(oldconfig);hooks.write_bytes(oldhooks)
        if oldmodule is not None:target.write_bytes(oldmodule)
        elif target.exists():target.unlink()
        raise
    finally:frappe.destroy()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__))
        raise SystemExit(1) from None
