"""Content cleanup is separate from credit/payment audit retention."""
from datetime import timedelta
import frappe
from frappe.utils import now_datetime
from .ai_accounting import save

def sweep():
    if frappe.conf.get('il_control_plane'):return
    settings=frappe.get_single('IL SOUL Settings')
    now=now_datetime();days=max(1,min(int(settings.conversation_days or 90),3650))
    for name in frappe.get_all('IL AI Conversation',filters={'modified':['<',now-timedelta(days=days)],'status':'Active'},pluck='name',limit_page_length=100):
        d=frappe.get_doc('IL AI Conversation',name);d.status='Archived';d.archived_at=now;d.delete_after=now+timedelta(days=days);save(d)
    for name in frappe.get_all('IL AI Conversation',filters={'delete_after':['<=',now],'status':['in',['Archived','Deleted']]},pluck='name',limit_page_length=100):
        # Explicitly scoped content deletion; accounting/audit rows are untouched.
        frappe.db.delete('IL AI Message',{'conversation':name})
        d=frappe.get_doc('IL AI Conversation',name);d.status='Deleted';d.title='Deleted conversation';d.delete_after=None;save(d)
    detail_days=max(1,min(int(settings.usage_detail_days or 90),3650))
    frappe.db.sql('UPDATE `tabIL AI Usage` SET result=NULL WHERE creation<%s AND result IS NOT NULL',(now-timedelta(days=detail_days),))
    from .knowledge import disable_record,current
    from .retention import access_allowed
    for name in frappe.get_all('IL Knowledge Document',filters={'enabled':1},pluck='name',limit_page_length=500,order_by='modified asc'):
        d=frappe.get_doc('IL Knowledge Document',name)
        try:
            room=frappe.get_doc('IL Classroom',d.classroom)
            if not room.active or not access_allowed(room):disable_record(d)
            elif d.status=='Ready':current(d,room)
        except (ValueError,PermissionError,frappe.PermissionError,frappe.DoesNotExistError):disable_record(d)
    # Empty hosted indexes are deleted, not merely left billable forever.
    from .ai_provider import retrieval
    try:adapter=retrieval(cleanup=True)
    except Exception:return
    for name in frappe.get_all('IL Knowledge Index',filters={'status':'Ready'},pluck='name',limit_page_length=100):
        d=frappe.get_doc('IL Knowledge Index',name)
        if frappe.db.exists('IL Knowledge Document',{'index':name,'status':['not in',['Deleted','Unsupported']]}):continue
        try:adapter.delete_store(d.provider_store);d.status='Deleted';save(d)
        except Exception:d.error_code='store_cleanup_unconfirmed';save(d)
