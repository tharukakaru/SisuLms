"""Connect live Bench sites to the existing owner's catalogue without repricing records."""
import json,os,shutil
from pathlib import Path
from datetime import datetime,timezone
BENCH=Path('/home/sisu/frappe-bench');SITES=BENCH/'sites'
SOURCE='platform.sisuacademylk.com'
TARGETS=(SOURCE,'sisuacademylk.com','teen.sisuacademylk.com')
def main():
    if Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    os.umask(0o077)
    os.chdir(SITES)
    import frappe
    from institute_lms.plan_catalog_rules import defaults,validate
    def local_value(site):
        frappe.init(site=site);frappe.connect()
        try:
            row=frappe.db.get_value('IL Plan Catalog','current',['payload','revision'],as_dict=True)
            return {'plans':validate(json.loads(row.payload)) if row else defaults(),'revision':int(row.revision) if row else 0}
        finally:frappe.destroy()
    snapshots={site:local_value(site) for site in TARGETS}
    already_shared=all(json.loads((SITES/site/'site_config.json').read_text()).get('il_plan_catalog_source_site')==SOURCE for site in TARGETS)
    source=snapshots[SOURCE];public=snapshots['sisuacademylk.com']
    # Preserve the public prices/access that existing subscribers already use.
    if not already_shared and source['revision'] and source['plans']!=public['plans']:
        raise RuntimeError('Owner and public catalogues differ. Review them before choosing a shared version.')
    selected=public if not source['revision'] else source
    teen=snapshots['teen.sisuacademylk.com']
    if not already_shared and teen['revision'] and teen['plans']!=selected['plans']:
        raise RuntimeError('Teen institute has a different catalogue. Review before switching it.')
    root=Path.home()/'.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:raise RuntimeError('Private backup directory required')
    backup=root/('shared-plans-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));backup.mkdir(mode=0o700)
    old={}
    for site in TARGETS:
        path=SITES/site/'site_config.json'
        if path.is_symlink():raise RuntimeError('Unexpected configuration symlink')
        old[site]=path.read_bytes();(backup/(site+'.json')).write_bytes(old[site]);(backup/(site+'.json')).chmod(0o600)
    if not source['revision'] and public['revision']:
        frappe.init(site=SOURCE);frappe.connect()
        try:
            frappe.db.sql('SELECT name FROM `tabDocType` WHERE name=%s FOR UPDATE',('IL Plan Catalog',))
            if frappe.db.exists('IL Plan Catalog','current'):raise RuntimeError('Catalogue changed during activation. Retry after review.')
            doc=frappe.get_doc(dict(doctype='IL Plan Catalog',name='current',payload=json.dumps(public['plans']),revision=public['revision'],change_reason='Preserve published public catalogue as shared owner catalogue'))
            doc.flags.plan_catalog_service=True;doc.insert(ignore_permissions=True);frappe.db.commit()
        finally:frappe.destroy()
    try:
        for site in TARGETS:
            config=json.loads(old[site]);config['il_plan_catalog_source_site']=SOURCE
            path=SITES/site/'site_config.json';temp=path.with_suffix('.catalog-tmp');temp.write_text(json.dumps(config,indent=2));temp.chmod(0o600);os.replace(temp,path)
        from institute_lms.plan_catalog import current
        for site in TARGETS:
            frappe.init(site=site);frappe.connect()
            try:
                value=current()
                if value['plans']!=selected['plans']:raise RuntimeError('Shared catalogue verification failed')
                frappe.clear_cache();print('PASS: shared catalogue on '+site+'; revision '+str(value['revision']))
            finally:frappe.destroy()
    except Exception:
        for site,content in old.items():(SITES/site/'site_config.json').write_bytes(content)
        print('RESTORED: previous site configuration. Catalogue copy, if created, retains original public prices.')
        raise
    print('ACTIVATED: one catalogue across live owner/public/Teen sites. No invoice, subscription dates, payment or message changed. Staging remains isolated.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED: '+(str(exc) if isinstance(exc,RuntimeError) else type(exc).__name__))
        raise SystemExit(1) from None
