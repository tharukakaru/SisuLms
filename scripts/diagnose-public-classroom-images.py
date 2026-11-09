"""Read-only diagnosis of the public-site teacher classroom images."""
import json
import os
import stat
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE='sisuacademylk.com'
ORIGIN='https://www.sisuacademylk.com'
USER='sisu.student.test+hnb@gmail.com'

def main():
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise RuntimeError('Run as sisu')
    import frappe, requests
    from PIL import Image
    os.chdir('/home/sisu/frappe-bench/sites')
    frappe.init(site=SITE,sites_path='/home/sisu/frappe-bench/sites');frappe.connect()
    try:
        root=Path('/home/sisu/frappe-bench/sites')/SITE/'public'
        rooms=frappe.get_all('IL Classroom',filters={'owner_type':'Teacher'},fields=['name','profile_image','cover_image'],limit_page_length=10)
        print(json.dumps({'site':SITE,'sampled_teacher_classrooms':len(rooms)}))
        for room in rooms:
            for field in ('profile_image','cover_image'):
                value=room.get(field) or ''
                result={'classroom':room.name,'field':field,'saved_url_present':bool(value)}
                if not value:print(json.dumps(result));continue
                parsed=urlsplit(value)
                if parsed.scheme or parsed.netloc or not parsed.path.startswith('/files/') or parsed.query or parsed.fragment:
                    result['url_shape']='unexpected';print(json.dumps(result));continue
                path=(root/unquote(parsed.path).lstrip('/')).resolve()
                if root.resolve() not in path.parents:
                    result['path']='outside public directory';print(json.dumps(result));continue
                result['file_exists']=path.is_file()
                records=frappe.get_all('File',filters={'file_url':value},fields=['owner','is_private','file_size'],limit_page_length=20)
                result['file_records']=len(records)
                result['public_file_record']=any(not r.is_private for r in records)
                if path.is_file():
                    result['bytes']=path.stat().st_size
                    result['mode']=oct(stat.S_IMODE(path.stat().st_mode))
                    try:
                        with Image.open(path) as im:
                            result['format']=im.format;im.verify();result['valid_image']=True
                    except Exception:result['valid_image']=False
                    result['public_directory_modes']=[{'directory':parent.name,'mode':oct(stat.S_IMODE(parent.stat().st_mode))} for parent in [root,root/'files']]
                try:
                    with requests.get(ORIGIN+parsed.path,timeout=(5,15),allow_redirects=False,stream=True) as response:
                        result['http_status']=response.status_code
                        content_type=response.headers.get('Content-Type','').split(';')[0]
                        result['response_type']=content_type if content_type in ('image/webp','image/png','image/jpeg','text/html','application/json','application/octet-stream') else 'other'
                        result['content_matches_file']=False
                        if response.status_code==200 and path.is_file() and path.stat().st_size<=5*1024*1024:
                            body=response.raw.read(5*1024*1024+1)
                            result['content_matches_file']=body==path.read_bytes()
                except Exception as exc:result['http_error']=type(exc).__name__
                print(json.dumps(result))
        print('READ ONLY: no uploads, permissions, database records or configuration changed.')
    finally:
        frappe.db.rollback();frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:raise SystemExit('STOPPED: '+type(exc).__name__+'; no credentials displayed.') from None
