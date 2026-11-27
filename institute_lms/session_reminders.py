"""Five-minute class reminders, with durable deduplication and verified recipients."""
import hashlib
from datetime import timedelta
from urllib.parse import urlencode
import frappe
from frappe.utils import now_datetime, get_datetime, get_url

DT = 'IL Session Reminder'


def due(starts_at, now):
    return now < get_datetime(starts_at) <= now + timedelta(minutes=5)


def eligible(meeting, room, member):
    if meeting.status in ('Cancelled', 'Completed') or not room.active:
        return False
    if not member.active or member.role != 'Student' or member.institute != room.institute:
        return False
    if str(member.user).endswith(('.invalid', '.test')):
        return False
    if meeting.institute != room.institute or meeting.classroom != room.name:
        return False
    if not frappe.db.exists('IL Enrollment', {'classroom':room.name,'student':member.name,'active':1}):
        return False
    if not frappe.db.get_value('User', member.user, 'enabled'):
        return False
    from .api import access
    return access(room, member)['allowed']


def queue(meeting, now=None):
    now = now or now_datetime()
    if not due(meeting.starts_at, now) or meeting.status in ('Cancelled','Completed'):
        return []
    room = frappe.get_doc('IL Classroom', meeting.classroom)
    queued = []
    for student in frappe.get_all('IL Enrollment', filters={'classroom':room.name,'active':1}, pluck='student'):
        member = frappe.get_doc('IL Member', student)
        if not eligible(meeting, room, member):continue
        phone = frappe.db.get_value('IL Verified Phone', {'user':member.user}, 'phone')
        if not phone:continue
        key = hashlib.sha256(f'{meeting.name}:{get_datetime(meeting.starts_at)}:{student}'.encode()).hexdigest()
        with frappe.cache.lock('session-reminder:'+key, timeout=20):
            if frappe.db.exists(DT, {'reminder_key':key}):continue
            origin = str(frappe.conf.get('il_session_reminder_origin') or frappe.conf.get('host_name') or get_url()).rstrip('/')
            link = origin + '/campus?' + urlencode({'classroom':room.name,'institute':room.institute})
            start = get_datetime(meeting.starts_at)
            body = (f'Class starts soon\n{meeting.title[:90]}\n'
                    f'{start:%d %b, %I:%M %p} (Sri Lanka time)\nJoin your class: {link}')
            row = frappe.get_doc(dict(doctype=DT, reminder_key=key, session=meeting.name,
                classroom=room.name, institute=room.institute, student=student, starts_at=start,
                phone=phone, body=body, status='Queued')).insert(ignore_permissions=True)
            queued.append(row.name)
    return queued


def deliver(name):
    with frappe.cache.lock('session-reminder-send:'+name, timeout=90):
        row = frappe.get_doc(DT, name, for_update=True)
        if row.status != 'Queued':return
        meeting = frappe.get_doc('IL Session', row.session)
        room = frappe.get_doc('IL Classroom', row.classroom)
        member = frappe.get_doc('IL Member', row.student)
        valid = (get_datetime(meeting.starts_at) == get_datetime(row.starts_at)
                 and due(meeting.starts_at, now_datetime()) and eligible(meeting, room, member)
                 and frappe.db.exists('IL Verified Phone', {'user':member.user,'phone':row.phone}))
        if not valid:
            row.status='Skipped';row.save(ignore_permissions=True);frappe.db.commit();return
        if not frappe.conf.get('il_sms_adapter'):return
        # Persist uncertainty first: a timeout/crash must never cause duplicate SMS sends.
        row.status='Review';row.save(ignore_permissions=True);frappe.db.commit()
        try:
            from .providers import sms
            result=sms(row.phone,row.body,row.reminder_key)
            row.status='Accepted';row.provider_id=result.get('provider_id');row.sent_at=now_datetime()
        except Exception:
            row.last_error='SMS acceptance uncertain; reconcile before retrying.'
        row.save(ignore_permissions=True);frappe.db.commit()


def dispatch():
    if frappe.conf.get('il_control_plane'):return
    now=now_datetime()
    for name in frappe.get_all('IL Session', filters={'status':['in',['Scheduled','Live']],
        'starts_at':['between',[now,now+timedelta(minutes=5)]]}, pluck='name',limit_page_length=1000):
        queue(frappe.get_doc('IL Session',name),now)
    frappe.db.commit()
    for name in frappe.get_all(DT,filters={'status':'Queued'},pluck='name',limit_page_length=100):
        deliver(name)
