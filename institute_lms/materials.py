"""Private document uploads and authorization on every read/download."""
import secrets
from datetime import timedelta
from pathlib import Path
import frappe
from frappe.utils import now_datetime
from .api import classroom_for, accessible_room, scoped
from .material_contract import MAX_BYTES, TYPES, PAPER_INLINE, validate_file, require_download, require_preview


@frappe.whitelist(methods=['POST'])
def upload(classroom, purpose='original'):
    _,member,room=classroom_for(classroom,write=True)
    if purpose not in ('original','preview'):frappe.throw('Invalid upload purpose')
    return store_upload(room, preview=purpose=='preview')


def store_upload(room, preview=False, paper=False):
    """Shared private storage, size validation and upload rate limit."""
    item=frappe.request.files.get('file')
    if not item:frappe.throw('Choose a document')
    content=item.stream.read(MAX_BYTES+1)
    try:suffix,_=validate_file(item.filename,content,preview=preview,paper=paper)
    except ValueError as exc:frappe.throw(str(exc))
    # Bound bulk storage abuse; configure reverse-proxy and per-site quotas as well.
    if frappe.db.count('File',{'owner':frappe.session.user,'attached_to_doctype':'IL Classroom','creation':['>',now_datetime()-timedelta(hours=1)]})>=40:
        frappe.throw('Upload limit reached. Please try again later')
    from frappe.utils.file_manager import save_file
    file=save_file('material-'+secrets.token_hex(12)+'.'+suffix,content,'IL Classroom',room.name,is_private=1)
    return {'file_id':file.name,'filename':item.filename,'file_type':suffix,'file_size':len(content)}


@frappe.whitelist(methods=['POST'])
def upload_paper(classroom, title, request_id, description=''):
    """Publish a downloadable classroom document, without creating an assignment."""
    import hashlib
    import re
    from .teaching import require
    inst, member, room = accessible_room(classroom)
    require(room, member, 'edit')
    if not isinstance(title, str) or not title.strip() or len(title)>120:
        frappe.throw('Enter a paper title of at most 120 characters')
    if not isinstance(description, str) or len(description)>1000:
        frappe.throw('Instructions must be at most 1,000 characters')
    if not isinstance(request_id, str) or not re.fullmatch(r'[a-fA-F0-9-]{36}',request_id):
        frappe.throw('Invalid upload request ID')
    name='paper-upload-'+hashlib.sha256((room.name+':'+frappe.session.user+':'+request_id).encode()).hexdigest()
    frappe.db.sql('SELECT name FROM `tabIL Classroom` WHERE name=%s FOR UPDATE',(room.name,))
    existing=frappe.db.sql('SELECT name FROM `tabIL Material` WHERE name=%s FOR UPDATE',(name,))
    if existing:return {'name':name,'uploaded':True}
    file=store_upload(room,paper=True)
    frappe.get_doc({'doctype':'IL Material','institute':inst.name,'classroom':room.name,
        'title':title.strip(),'description':description.strip(),'kind':'Document',
        'download_policy':'Downloadable','url':'',**file}).insert(ignore_permissions=True,set_name=name)
    return {'name':name,'uploaded':True}


@frappe.whitelist()
def paper_listing(classroom, page=0):
    inst, member, room=accessible_room(classroom)
    filters={'institute':inst.name,'classroom':room.name,'kind':'Document','name':['like','paper-upload-%']}
    rows=frappe.get_all('IL Material',filters=filters,
        fields=['name','classroom','title','description','filename','file_type','file_size','download_policy','expires_at'],
        start=max(0,min(int(page),10000))*30,limit_page_length=30,order_by='creation desc')
    from .material_availability import require_available
    if member.role=='Student':
        visible=[]
        for row in rows:
            try:require_available(row.get('expires_at'),member.role,now_datetime())
            except PermissionError:continue
            visible.append(row)
        return visible
    return rows


def checked_file(name,room,require_owner=False):
    file=frappe.get_doc('File',name)
    if not file.is_private or file.attached_to_doctype!='IL Classroom' or file.attached_to_name!=room.name:
        frappe.throw('Document unavailable',frappe.PermissionError)
    if require_owner and file.owner!=frappe.session.user:
        frappe.throw('Upload your own copy of the document',frappe.PermissionError)
    if getattr(frappe,'conf',{}).get('il_storage_backend','frappe')!='frappe':
        from .storage import PrivateReader
        return file,PrivateReader(file,MAX_BYTES)
    # Do not fetch a client-controlled URL.
    private=Path(frappe.get_site_path('private','files')).resolve()
    path=Path(file.get_full_path()).resolve()
    if private not in path.parents or not path.is_file() or path.stat().st_size>MAX_BYTES:
        frappe.throw('Document unavailable',frappe.PermissionError)
    return file,path


def attachment_fields(data,room):
    file,path=checked_file(data.file_id,room,require_owner=True)
    content=path.read_bytes()
    try:suffix,_=validate_file(file.file_name,content)
    except ValueError as exc:frappe.throw(str(exc))
    preview=data.get('preview_file_id')
    if preview:
        pdf,pdf_path=checked_file(preview,room,require_owner=True)
        try:validate_file(pdf.file_name,pdf_path.read_bytes(),preview=True)
        except ValueError as exc:frappe.throw(str(exc))
    policy=data.get('download_policy') or 'View only'
    try:require_preview(suffix,preview,policy)
    except ValueError as exc:frappe.throw(str(exc))
    # Friendly name is display metadata only; the server chooses file paths.
    filename=str(data.get('filename') or file.file_name)
    if any(c in filename for c in '/\\\r\n\x00') or len(filename)>180:frappe.throw('Invalid display filename')
    return {'file_id':file.name,'preview_file_id':preview,'filename':filename,'file_type':suffix,
            'file_size':len(content),'download_policy':policy,'url':''}


@frappe.whitelist(methods=['GET'])
def content(material, action='view'):
    doc=frappe.get_doc('IL Material',material)
    inst,member,room=accessible_room(doc.classroom)
    scoped('IL Material',material,inst)
    from .material_availability import require_available
    try:require_available(doc.get('expires_at'),member.role,now_datetime())
    except PermissionError as exc:frappe.throw(str(exc),frappe.PermissionError)
    if action not in ('view','download'):frappe.throw('Invalid document action')
    paper_inline=str(doc.name).startswith('paper-upload-') and doc.file_type in PAPER_INLINE
    if action=='download':
        try:require_download(doc.download_policy,member.role)
        except PermissionError as exc:frappe.throw(str(exc),frappe.PermissionError)
        file_id=doc.file_id;filename=doc.filename
    else:
        file_id=doc.file_id if doc.file_type=='pdf' or paper_inline else doc.preview_file_id
        filename=doc.filename if paper_inline else 'preview.pdf'
    if not file_id:frappe.throw('No PDF preview has been uploaded for this material')
    file,path=checked_file(file_id,room)
    raw=path.read_bytes()
    try:suffix,mime=validate_file(file.file_name,raw,preview=action=='view' and not paper_inline,paper=str(doc.name).startswith('paper-upload-'))
    except ValueError as exc:frappe.throw(str(exc))
    from .workspace import consume_view,settings_for
    from .commercial import account_for
    account=account_for(room,False)
    if member.role=='Student' and suffix=='pdf' and account and account.plan=='Platinum' and settings_for(account)['pdf_watermark']:
        from .pdf_watermark import watermark
        try:raw=watermark(raw,'SISU | '+member.name+' | '+str(now_datetime().date()))
        except ValueError as exc:frappe.throw(str(exc))
    consume_view(room,member,'material:'+doc.name,'document')
    frappe.local.response.update({'type':'download','filename':filename or 'document.'+suffix,
        'filecontent':raw,'content_type':mime,'display_content_as':'inline' if action=='view' else 'attachment'})
    frappe.local.response_headers.update({'Cache-Control':'no-store, private','X-Content-Type-Options':'nosniff'})


@frappe.whitelist(methods=['POST'])
def update_availability(material, availability_days=None):
    doc=frappe.get_doc('IL Material',material)
    inst,member,room=classroom_for(doc.classroom,write=True)
    scoped('IL Material',material,inst)
    from .material_availability import deadline
    try:doc.expires_at=deadline(availability_days,now_datetime())
    except ValueError as exc:frappe.throw(str(exc))
    doc.save(ignore_permissions=True)
    return {'name':doc.name,'expires_at':doc.expires_at,'permanent':not doc.expires_at}
