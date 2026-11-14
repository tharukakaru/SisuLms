"""Guarded single-file mobile context deployment. Run as sisu."""
import hashlib, os, shutil
from datetime import datetime, timezone
from pathlib import Path
BEFORE='cc2ce3448c75922109388170832ba70279145cfd0c74ecf0ae33fb4f24f413a1'
AFTER='1397f57c692a8e76586c80f4f847c39802f7b1fafc619780043339a02ace1769'
APP=Path('/home/sisu/frappe-bench/apps/institute_lms')
def digest(b): return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
def main():
    if Path.home()!=Path('/home/sisu'): raise RuntimeError('Run as sisu')
    target=APP/'institute_lms/campus_context.py'
    source=Path('/tmp/campus_context.py')
    if target.is_symlink() or source.is_symlink(): raise RuntimeError('Unexpected symlink')
    data=source.read_bytes()
    if digest(data)!=AFTER: raise RuntimeError('Payload mismatch')
    if digest(target.read_bytes()) not in (BEFORE,AFTER): raise RuntimeError('Source conflict; do not overwrite')
    compile(data,str(target),'exec')
    root=Path.home()/'.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077: raise RuntimeError('Private backup directory required')
    backup=root/('mobile-campus-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700)
    shutil.copy2(target,backup/'campus_context.py')
    temporary=target.with_suffix('.py.mobile-new')
    temporary.write_bytes(data)
    temporary.chmod(0o644)
    temporary.replace(target)
    if digest(target.read_bytes())!=AFTER: raise RuntimeError('Installed hash mismatch')
    print('DEPLOYED: mobile campus selection, clear and choices. Source hash and syntax verified. Restart web/workers.')
    print('No schema, credentials, memberships or payment changes. Test mobile selection using the existing token.')
if __name__=='__main__': main()
