"""Thirty-day promotional retention; never deletes invoices or learning records."""
from datetime import timedelta, datetime
import frappe
from frappe.utils import now_datetime

def access_allowed(record, now=None):
    from .saas_rules import dt
    now=now or now_datetime()
    if record.get('lifecycle') in ('ARCHIVED','PENDING_DELETE','PURGED'):return False
    expiry=dt(record.get('expires_at'))
    if not expiry:return record.get('lifecycle') not in ('EXPIRED',)
    if now<expiry:return True
    grace=dt(record.get('course_grace_until'))
    return bool(grace and now<grace)

def lifecycle(record, now=None):
    from .saas_rules import dt
    now=now or now_datetime()
    old=record.get('lifecycle') or 'ACTIVE'
    if old=='PURGED':return old
    expiry=dt(record.get('expires_at'))
    if not expiry or now<expiry:return old
    grace=dt(record.get('course_grace_until'))
    if grace and now<grace:return 'GRACE'
    delete=dt(record.get('delete_at'));archive=dt(record.get('archive_at'))
    if delete and now>=delete:return 'PENDING_DELETE'
    if archive and now>=archive:return 'ARCHIVED'
    return 'EXPIRED'

@frappe.whitelist(methods=['POST'])
def configure_course(classroom,expires_at,grace_days=0,archive_days=30,delete_days=180):
    from .api import classroom_for
    from .teaching import require
    from .pricing_rules import integer
    from frappe.utils import get_datetime
    _,member,room=classroom_for(classroom,write=True);require(room,member,'edit')
    grace=integer(grace_days,'Grace',365);archive=integer(archive_days,'Archive',3650);delete=integer(delete_days,'Delete',36500)
    if archive<grace or delete<archive:frappe.throw('Retention intervals must be ordered')
    expiry=get_datetime(expires_at)
    room.expires_at=expiry;room.course_grace_until=expiry+timedelta(days=grace)
    room.archive_at=expiry+timedelta(days=archive);room.delete_at=expiry+timedelta(days=delete)
    room.lifecycle=lifecycle(room.as_dict());room.save(ignore_permissions=True)
    from .saas import audit
    audit('Configure course retention',room.name,str(expiry))
    return {'lifecycle':room.lifecycle}

def sweep():
    from .ai_retention import sweep as ai_sweep
    ai_sweep()
    from .notification_service import emit
    from .saas import managed
    from .saas_rules import effective_state
    for dt in ('IL Classroom','IL Enrollment'):
        for name in frappe.get_all(dt,filters={'expires_at':['<=',now_datetime()],'lifecycle':['!=','PURGED']},pluck='name',limit_page_length=500):
            d=frappe.get_doc(dt,name);new=lifecycle(d.as_dict())
            if new==d.lifecycle:continue
            d.lifecycle=new;d.save(ignore_permissions=True)
            students=[d.student] if dt=='IL Enrollment' else frappe.get_all('IL Enrollment',filters={'classroom':name,'active':1},pluck='student')
            for student in students:emit(d.institute,student,'course.expiry','expiry:'+dt+':'+name+':'+new,'Course access state: '+new)
    for name in frappe.get_all('IL Subscription',filters={'state':['in',['trial','active','grace']]},pluck='name',limit_page_length=500):
        d=frappe.get_doc('IL Subscription',name);new=effective_state(d.state,d.ends_at,d.grace_until,datetime.utcnow())
        if new!=d.state:
            d.state=new;managed(d)
            if not frappe.conf.get('il_control_plane'):
                from .api import institute
                inst=institute()
                for member in frappe.get_all('IL Member',filters={'role':'Admin','active':1},pluck='name'):
                    emit(inst.name,member,'subscription.expiry','subscription:'+name+':'+str(d.ends_at), 'Organization subscription '+new)
    for name in frappe.get_all('IL Stored Object',filters={'expiry_at':['<=',now_datetime()],'status':['!=','PURGED']},pluck='name',limit_page_length=500):
        d=frappe.get_doc('IL Stored Object',name,for_update=True)
        if d.legal_hold or frappe.db.exists('IL Lecture Access',{'media_key':d.storage_key,'revoked':0}):continue
        values=d.as_dict();values['expires_at']=d.expiry_at;values['lifecycle']=d.status
        d.status=lifecycle(values);managed(d)
    # Never automatically delete financial, assessment, certificate or audit data.
    # Physical purge is a separate explicitly reviewed operation below.

@frappe.whitelist(methods=['POST'])
def purge_orphan(object_name,reason):
    from .api import identity,require_role
    from .saas import managed,audit
    inst,m=identity();require_role(m,'Admin')
    d=frappe.get_doc('IL Stored Object',object_name)
    if d.backend!='frappe' or frappe.db.exists('IL Lecture Product',{'media_key':d.storage_key}):
        frappe.throw('Referenced or remote media requires reviewed provider reconciliation; no purge was performed')
    if d.institute!=inst.name or d.legal_hold or d.status!='PENDING_DELETE' or not str(reason).strip():frappe.throw('Object not eligible for reviewed purge')
    if d.file:
        f=frappe.get_doc('File',d.file)
        if f.attached_to_doctype or frappe.db.exists('IL Material',{'file_id':f.name}) or frappe.db.exists('IL Material',{'preview_file_id':f.name}):
            frappe.throw('Only detached, unreferenced files can be purged; preserve academic and financial attachments')
        # Remove our own Link within the same transaction; other Frappe links still
        # prevent deletion. Any exception rolls this detach back too.
        d.file=None;managed(d)
        frappe.delete_doc('File',f.name,ignore_permissions=True)
    d.file=None;d.status='PURGED';managed(d);audit('Purge orphan',object_name,reason)
    return {'status':'PURGED'}


def purge_expired_promotions():
    cutoff = now_datetime() - timedelta(days=30)
    # Creation is the immutable publication timestamp. Editing cannot extend TTL.
    # Bounded batches prevent a large backfill from monopolising the scheduler.
    for doctype in ("IL News",):
        names = frappe.get_all(doctype, filters={"creation": ["<=", cutoff]}, pluck="name", limit_page_length=500, order_by="creation asc")
        for name in names:
            frappe.delete_doc(doctype, name, ignore_permissions=True)
    # Shared File records are not removed: other posts/profiles may still use them.
