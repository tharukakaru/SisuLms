"""Read-only readiness check for the existing local sandbox, never production."""
import hashlib
import logging
import os
from pathlib import Path

SITE = 'hnb-checkout.localhost'
FILES = ('campus_context.py', 'campus_join.py', 'campus_teachers.py',
         'membership_write.py', 'saas.py', 'account_billing.py', 'native_access.py')
stage = 'local sandbox preflight'


def main():
    global stage
    bench = Path.cwd().resolve()
    if os.name != 'posix' or bench.name != 'sisu-hnb-sandbox-bench':
        print('BLOCKED: run from ~/sisu-hnb-sandbox-bench in Ubuntu.')
        return 1
    if not (bench / 'sites' / SITE / 'site_config.json').is_file():
        print('BLOCKED: expected local sandbox site not found.')
        return 1
    logging.disable(logging.CRITICAL)
    stage = 'loading installed applications'
    import frappe
    import institute_lms
    source = Path(__file__).resolve().parents[1] / 'institute_lms'
    installed = Path(institute_lms.__file__).resolve().parent
    # Frappe resolves some log/config paths relative to the sites directory,
    # even when sites_path is passed explicitly (same setup as existing scripts).
    os.chdir(bench / 'sites')
    try:
        stage = 'initializing sandbox site'
        frappe.init(site=SITE, sites_path=str(bench / 'sites'))
        stage = 'connecting sandbox database'
        frappe.connect()
        # Prevent a mistakenly added database write in this inspection.
        stage = 'setting read-only inspection transaction'
        frappe.db.rollback()
        frappe.db.sql('SET SESSION TRANSACTION READ ONLY')
        print('PASS: connected to the named local sandbox; transaction is read-only.')
        stage = 'checking schema and fixture counts'
        for doctype in ('IL Institute', 'IL Member', 'IL Public Profile', 'IL Verified Phone', 'IL Account Subscription'):
            print(f'SCHEMA: {doctype}: {bool(frappe.db.exists("DocType", doctype))}')
        if frappe.db.exists('DocType', 'IL Public Profile'):
            for kind in ('Student', 'Teacher', 'Institute'):
                count = frappe.db.count('IL Public Profile', {'kind': kind, 'status': 'Verified'})
                print(f'FIXTURES: verified {kind} profiles: {count}')
        print('SHARED MODE:', bool(frappe.conf.get('il_shared_campus_enabled')))
        print('CONTROL PLANE:', bool(frappe.conf.get('il_control_plane')))
        stage = 'comparing installed source files'
        for name in FILES:
            expected, actual = source / name, installed / name
            if not expected.is_file():
                state = 'local reference missing'
            elif not actual.is_file():
                state = 'not installed'
            else:
                state = 'matches local source' if hashlib.sha256(expected.read_bytes()).digest() == hashlib.sha256(actual.read_bytes()).digest() else 'update needed'
            print(f'SOURCE: {name}: {state}')
        print('Inspection only. No records, settings, messages or service restarts changed.')
        return 0
    finally:
        # Cleanup must not replace the original failure with a second error.
        try:
            if getattr(frappe.local, 'db', None):
                frappe.db.rollback()
        finally:
            frappe.destroy()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'BLOCKED at {stage} [{type(error).__name__}]. No credentials displayed.')
        raise SystemExit(1)
