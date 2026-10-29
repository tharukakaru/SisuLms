"""Default Frappe storage with transactional quotas and replaceable private reader.

before_write_file runs before bytes are written. The subscription DB lock is held
until the enclosing transaction commits. File insert also checks deduplicated
copies, which may bypass Frappe's physical-write hook. No remote fetch fallback.
"""
from pathlib import Path
import frappe
from .saas import quota, managed
from .usage import used

def before_write(file_size):
    if frappe.flags.get('in_install') or frappe.flags.get('in_migrate'):return
    if frappe.conf.get('il_control_plane'):
        frappe.throw('File uploads are disabled on the control-plane site')
    if frappe.conf.get('il_storage_backend','frappe')!='frappe' and (not frappe.get_hooks('write_file') or not frappe.conf.get('il_storage_read_adapter')):
        frappe.throw('Install and verify the replacement Frappe storage adapter before enabling it')
    quota('storage_bytes',lambda:used('storage_bytes'),int(file_size))

def file_saved(doc, method=None):
    if doc.is_folder or frappe.flags.get('in_install') or frappe.flags.get('in_migrate'):return
    if frappe.conf.get('il_control_plane'):frappe.throw('Control-plane uploads disabled')
    size=int(doc.file_size or 0)
    quota('storage_bytes',lambda:max(0,used('storage_bytes')-size),size)
    record_metadata(doc)

def record_metadata(doc):
    from .api import institute
    inst=institute();room=None
    if doc.attached_to_doctype=='IL Classroom':room=doc.attached_to_name
    elif doc.attached_to_doctype=='IL Paper Attempt':
        paper=frappe.db.get_value('IL Paper Attempt',doc.attached_to_name,'paper')
        room=frappe.db.get_value('IL Paper',paper,'classroom') if paper else None
    if room and frappe.db.get_value('IL Classroom',room,'institute')!=inst.name:
        frappe.throw('Foreign storage owner',frappe.PermissionError)
    name=frappe.db.get_value('IL Stored Object',{'file':doc.name},'name')
    m=frappe.get_doc('IL Stored Object',name) if name else frappe.get_doc({'doctype':'IL Stored Object','file':doc.name,'status':'ACTIVE'})
    m.institute=inst.name;m.classroom=room;m.owner_user=doc.owner;m.bytes=int(doc.file_size or 0)
    m.course=frappe.db.get_value('IL Classroom',room,'lms_course') if room else (doc.attached_to_name if doc.attached_to_doctype=='LMS Course' else None)
    m.backend=frappe.conf.get('il_storage_backend','frappe');m.storage_key=doc.file_url
    managed(m)

def backfill():
    """Metadata only. Existing File rows already count toward the physical quota."""
    if frappe.conf.get('il_control_plane') or not frappe.conf.get('il_tenant_id'):return
    rows=frappe.db.sql('''SELECT f.name FROM `tabFile` f LEFT JOIN `tabIL Stored Object` s ON s.file=f.name
        WHERE f.is_folder=0 AND s.name IS NULL ORDER BY f.creation LIMIT 100''')
    for row in rows:record_metadata(frappe.get_doc('File',row[0]))

def file_deleted(doc, method=None):
    name=frappe.db.get_value('IL Stored Object',{'file':doc.name},'name')
    if name:
        m=frappe.get_doc('IL Stored Object',name);m.status='PURGED';m.file=None;managed(m)

class PrivateReader:
    def __init__(self,file,maximum):self.file=file;self.maximum=maximum
    def read_bytes(self):return read_private(self.file,self.maximum)

def read_private(file, maximum):
    """Configured trusted adapter must implement read_private(file, maximum).
    Authorize the associated resource before calling this function.
    """
    backend=frappe.conf.get('il_storage_backend','frappe')
    if backend!='frappe':
        adapter=frappe.conf.get('il_storage_read_adapter')
        if not adapter:frappe.throw('Storage adapter is not configured')
        raw=frappe.get_attr(adapter)(file=file,maximum=maximum)
    else:
        root=Path(frappe.get_site_path('private','files')).resolve()
        path=Path(file.get_full_path()).resolve()
        if root not in path.parents or not path.is_file() or path.stat().st_size>maximum:
            frappe.throw('Document unavailable',frappe.PermissionError)
        raw=path.read_bytes()
    if not isinstance(raw,bytes) or len(raw)>maximum:frappe.throw('Invalid storage response')
    return raw
