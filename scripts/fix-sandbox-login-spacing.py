"""Apply only login-button CSS to the named local sandbox, preserving its build."""
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

CSS = '''
/* SISU login action spacing */
.sisu-entry .entry-card .entry-primary {
 display:flex;align-items:center;justify-content:center;box-sizing:border-box;
 width:100%;min-height:52px;padding:14px 18px;border-radius:13px;
 font-family:inherit;font-weight:600;font-size:14px;line-height:1.4;text-decoration:none;
}
.sisu-entry .entry-card .entry-primary + button.entry-primary,
.sisu-entry .entry-card .entry-primary + .entry-google {
 margin-top:16px !important;
}
.sisu-entry .entry-card .entry-primary + button.entry-primary,
.sisu-entry .entry-card .entry-google {
 background:#fff !important;color:#443153 !important;
 border:1px solid #c4bbd5 !important;box-shadow:none !important;
}
.sisu-entry .entry-card .entry-login-actions {display:grid;gap:16px;margin-top:18px}
.sisu-entry .entry-card .entry-login-actions .entry-primary {margin:0 !important}
'''
MARKER='sisu-login-spacing-fix'

def main():
    bench=Path.home()/'sisu-hnb-sandbox-bench'
    if os.name!='posix' or Path.cwd().resolve()!=bench.resolve():
        raise RuntimeError('Run from the local Ubuntu sandbox bench')
    if not (bench/'sites/hnb-checkout.localhost/site_config.json').is_file():
        raise RuntimeError('Named sandbox missing')
    app=bench/'apps/institute_lms'
    # Patch the served entry only: this sandbox uses an older Google button
    # with entry-primary, not the newer entry-google class.
    targets=[app/'institute_lms/www/campus.html']
    changes=[]
    for path in targets:
        if path.is_symlink():raise RuntimeError('Unexpected symlink')
        old=path.read_text()
        if MARKER in old:continue
        if path.suffix=='.html':
            if old.count('</head>')!=1:raise RuntimeError('Unexpected campus entry')
            new=old.replace('</head>','<style id="'+MARKER+'">'+CSS+'</style></head>')
        else:
            if 'entry-google' not in old or 'entry-primary' not in old:raise RuntimeError('Unexpected login source')
            new=old+'\n<style scoped>/* '+MARKER+' */\n'+CSS+'\n</style>\n'
        changes.append((path,old,new))
    backup=Path.home()/'.sisu-secrets'/('login-spacing-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True,mode=0o700)
    for path,old,new in changes:
        saved=backup/path.name
        saved.write_text(old);saved.chmod(0o600)
        path.write_text(new);path.chmod(0o644)
    subprocess.run(['bench','--site','hnb-checkout.localhost','clear-website-cache'],cwd=bench,check=True)
    print('APPLIED: 16px button gap and white Google button. Hard-refresh /campus.')
    print('CSS only; existing JavaScript, accounts and Google settings preserved.')
    print('Temporary entry patch; the permanent layout fix is in the newer frontend source.')

if __name__=='__main__':
    main()
