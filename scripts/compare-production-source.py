"""Compare deployed application source against an explicit local manifest, read-only.
No site configs, credentials, database records or file contents are printed.
"""
import hashlib,json
from pathlib import Path
APP=Path('/home/sisu/frappe-bench/apps/institute_lms')
TEXT={'.py','.js','.mjs','.cjs','.vue','.css','.html','.json','.toml','.txt','.md','.svg','.yml','.yaml'}
def digest(path):
    b=path.read_bytes()
    if path.suffix.lower() in TEXT:b=b.replace(b'\r\n',b'\n')
    return hashlib.sha256(b).hexdigest()
def eligible(name):
    p=Path(name)
    return not p.is_absolute() and '..' not in p.parts and not any(x in p.parts for x in ('node_modules','__pycache__','.git','local-private')) and not p.name.startswith('.env') and p.name not in ('site_config.json','common_site_config.json') and (name.startswith(('institute_lms/','frontend/src/')) or name in ('frontend/package.json','frontend/package-lock.json','frontend/vite.config.js','pyproject.toml','setup.py','requirements.txt','package.json')) and not name.startswith('institute_lms/public/portal/') and name!='institute_lms/www/campus.html'
def main():
    manifest=json.loads(Path('/tmp/sisu-production-source-manifest.json').read_text())
    differences=[];matched=0
    for name,wanted in manifest.items():
        if not eligible(name):raise RuntimeError('Unexpected manifest path')
        p=APP/name
        if p.is_symlink() or not p.resolve().is_relative_to(APP.resolve()):raise RuntimeError('Unexpected source link')
        if not p.is_file():differences.append({'file':name,'status':'missing_on_server'})
        elif digest(p)!=wanted:differences.append({'file':name,'status':'different'})
        else:matched+=1
    extra=[]
    for root in ('institute_lms','frontend/src'):
        for p in (APP/root).rglob('*'):
            name=p.relative_to(APP).as_posix()
            if p.is_file() and not p.is_symlink() and eligible(name) and name not in manifest and p.suffix.lower() in TEXT:extra.append(name)
    print(json.dumps({'matched':matched,'differences':differences,'server_only_source_files':sorted(extra)},indent=2))
    print('READ ONLY: application source comparison. Runtime configuration, database data, uploads and retained build chunks are excluded. No changes made.')
if __name__=='__main__':main()
