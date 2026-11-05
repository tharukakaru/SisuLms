"""Exact source patch: preserve shared-campus classification; require affiliation on tenant sites."""
import os,ast
from pathlib import Path
from datetime import datetime,timezone
OLD = '    member["institute_teacher"] = bool(member.get("role") == "Teacher" and\n        frappe.db.exists("IL Public Profile", {"workspace": inst.name, "kind": "Institute"}))'
NEW = '    institute_profile = frappe.db.get_value("IL Public Profile",\n        {"workspace": inst.name, "kind": "Institute"}, "name")\n    from .campus_context import enabled as shared_campus\n    member["institute_teacher"] = bool(member.get("role") == "Teacher" and institute_profile and\n        (shared_campus() or frappe.db.exists("IL Profile Relationship", {\n            "profile": institute_profile, "user": frappe.session.user,\n            "kind": "Teacher membership", "status": "Active"})))'

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    p=Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms/api.py')
    s=p.read_text(encoding='utf-8')
    if NEW in s:
        print('ALREADY APPLIED: teacher navigation classification.');return
    if s.count(OLD)!=1:raise RuntimeError('Source differs; no changes made')
    updated=s.replace(OLD,NEW);ast.parse(updated)
    root=Path.home()/'.sisu-secrets'
    if not root.is_dir() or root.is_symlink() or root.stat().st_mode&0o077:raise RuntimeError('Private backup directory required')
    backup=root/('teacher-navigation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.py')
    with backup.open('x',encoding='utf-8') as f:f.write(s)
    backup.chmod(0o600)
    p.write_text(updated,encoding='utf-8')
    print('DEPLOYED: tenant teacher navigation now requires an active institute affiliation. Shared public workspace classification unchanged.')
    print('Restart web and workers. No invoices, payment settings, accounts or messages changed.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED:',type(exc).__name__,str(exc) if isinstance(exc,RuntimeError) else 'Patch failed; inspect private backup.')
        raise SystemExit(1) from None
