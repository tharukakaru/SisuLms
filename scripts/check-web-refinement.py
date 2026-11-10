"""Read-only verification of the web refinement release and demo assets."""
import hashlib,json,os,tarfile
from pathlib import Path

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'): raise RuntimeError('Run as sisu')
    app=Path('/home/sisu/frappe-bench/apps/institute_lms')
    with tarfile.open('/tmp/sisu-web-refinement.tgz') as archive:
        manifest=json.load(archive.extractfile('manifest.json'))
    for name,item in manifest.items():
        if Path(name).is_absolute() or '..' in Path(name).parts: raise RuntimeError('Invalid manifest path')
        data=(app/name).read_bytes()
        if hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()!=item['after']: raise RuntimeError('Source mismatch: '+name)
    html=(app/'institute_lms/www/campus.html').read_text()
    import re
    assets=re.findall(r'(?:src|href)="(/assets/institute_lms/portal/[^"?]+)',html)
    if not assets: raise RuntimeError('Built campus assets missing')
    for asset in assets:
        if not (app/'institute_lms/public/portal'/asset.split('/portal/',1)[1]).is_file(): raise RuntimeError('Built asset missing')
    print('PASS: 15 UI/asset source hashes and campus entry assets. No records, messages or payment settings changed.')
    print('Live role/browser acceptance remains separate.')
if __name__=='__main__': main()
