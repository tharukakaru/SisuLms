"""Bounded, server-only personal-image context; never grants classroom storage."""
from contextlib import contextmanager
from contextvars import ContextVar
import frappe

_profile=ContextVar('sisu_personal_image',default=None)

@contextmanager
def personal_upload(profile):
    from .campus_context import enabled,require_user
    if not enabled():
        yield
        return
    if profile.user!=require_user():frappe.throw('Upload only to your own profile.',frappe.PermissionError)
    if frappe.conf.get('il_storage_backend','frappe')!='frappe':frappe.throw('Personal photo storage requires the configured Frappe file backend.')
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(profile.user,))
    rows=frappe.get_all('File',filters={'attached_to_doctype':'IL Public Profile','attached_to_name':profile.name},fields=['file_size'],limit_page_length=0)
    if len(rows)>=40 or sum(int(r.file_size or 0) for r in rows)>20*1024*1024:
        frappe.throw('Your profile photo storage is full. Contact support to remove older uploads.')
    token=_profile.set(profile.name)
    try:yield
    finally:_profile.reset(token)

def bounded(size,doc=None):
    name=_profile.get()
    if not name:return False
    if not 0<int(size)<=1024*1024:frappe.throw('Choose a smaller photo; the saved image must be under 1 MB.')
    if doc is not None and (doc.attached_to_doctype!='IL Public Profile' or doc.attached_to_name!=name or doc.is_private):
        frappe.throw('Invalid personal photo attachment.',frappe.PermissionError)
    return True
