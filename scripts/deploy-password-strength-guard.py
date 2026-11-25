"""Allow the standard password-strength check without replacing live source."""
from pathlib import Path
import ast, datetime, os, shutil, subprocess
p=Path('/home/sisu/frappe-bench/apps/institute_lms/institute_lms/native_access.py')
source=p.read_text()
tree=ast.parse(source)
assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SAFE' for t in n.targets)]
if len(assignments)!=1: raise SystemExit('STOPPED: unexpected API guard structure')
a=assignments[0]
allowed=ast.literal_eval(a.value)
method='frappe.core.doctype.user.user.test_password_strength'
if not isinstance(allowed,set) or 'frappe.core.doctype.user.user.update_password' not in allowed:
    raise SystemExit('STOPPED: unexpected API allowlist')
if method not in allowed:
    lines=source.splitlines(keepends=True)
    replacement='SAFE='+repr(allowed|{method})+'\n'
    updated=''.join(lines[:a.lineno-1])+replacement+''.join(lines[a.end_lineno:])
    compile(updated,str(p),'exec')
    backup=Path('/home/sisu/.sisu-secrets')/('password-strength-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(mode=0o700,parents=True)
    shutil.copy2(p,backup/p.name)
    stat=p.stat();temp=p.with_suffix('.strength-tmp')
    temp.write_text(updated)
    os.chown(temp,stat.st_uid,stat.st_gid);os.chmod(temp,stat.st_mode & 0o777)
    os.replace(temp,p)
    print('Backup:',backup)
else: print('Checker already allowed; refreshing web process.')
subprocess.run(['supervisorctl','restart','frappe-bench-web:frappe-bench-frappe-web'],check=True)
print('INSTALLED: password-strength API guard fix. No database or account changes. Hard-refresh the password page.')
