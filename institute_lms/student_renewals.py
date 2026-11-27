"""Monthly class renewal periods and three-day student reminders."""
import hashlib
from datetime import timedelta
from urllib.parse import urlencode

import frappe
from frappe.utils import get_datetime, now_datetime

from .student_renewal_rules import paid_through, reminder_due

EVENT = 'class.renewal'


def coverage_end(room, student, start):
    rows = frappe.db.sql('''SELECT p.starts_at,p.ends_at FROM `tabIL Paid Access` p
        JOIN `tabIL Invoice` i ON i.name=p.invoice AND i.status='Paid'
        AND i.student=p.student AND i.classroom=p.classroom AND i.institute=p.institute
        WHERE p.institute=%s AND p.classroom=%s AND p.student=%s
        AND p.status IN ('Active','Awaiting key') AND p.ends_at>%s
        ORDER BY p.starts_at''', (room.institute, room.name, student, start), as_dict=True)
    return paid_through([(get_datetime(r.starts_at), get_datetime(r.ends_at)) for r in rows], get_datetime(start))


def reminder_state(room, member, now):
    if (not room.active or room.get('billing_type') != 'Monthly' or room.get('programme')
            or room.get('fee_mode') == 'Free' or float(room.fee or 0) <= 0
            or not member.active or member.role != 'Student' or member.institute != room.institute
            or str(member.user).endswith(('.invalid', '.test'))
            or not frappe.db.get_value('User', member.user, 'enabled')):
        return None
    enrollment = frappe.db.get_value('IL Enrollment',
        {'classroom':room.name, 'student':member.name, 'institute':room.institute, 'active':1},
        ['name','access_override'], as_dict=True)
    if not enrollment or enrollment.access_override in ('Open', 'Closed'):
        return None
    end = coverage_end(room, member.name, now)
    return end if reminder_due(end, now) else None


def reminder_key(room, end):
    return 'class-renewal:' + room.name + ':' + str(get_datetime(end))


def queue_reminder(room, member, now):
    from .notification_service import emit
    end = reminder_state(room, member, now)
    if not end:
        return
    origin = str(frappe.conf.get('host_name') or '').rstrip('/')
    link = origin + '/campus?' + urlencode({'institute':room.institute}) + '#payments'
    body = (f'Class renewal reminder\n{room.title[:100]}\n'
            f'Access ends: {end:%d %b %Y, %I:%M %p} (Sri Lanka time).\n'
            f'Renew in Class fees to keep joining lessons. Early renewal keeps your remaining paid days.\n{link}')
    event = emit(room.institute, member.name, EVENT, reminder_key(room, end), body,
                 channels=['IN_APP'], classroom=room.name)
    key = hashlib.sha256((event + ':renewal-sms').encode()).hexdigest()
    if not frappe.db.exists('IL Notification', {'event_key':key}):
        frappe.get_doc(dict(doctype='IL Notification', institute=room.institute,
            recipient=member.name, event=event, event_key=key, channel='SMS', body=body,
            status='Queued', attempts=0, next_attempt=now)).insert(ignore_permissions=True)


def deliver_sms(name):
    from .saas_rules import notification_key
    with frappe.cache.lock('class-renewal-sms:' + name, timeout=90):
        row = frappe.get_doc('IL Notification', name, for_update=True)
        if row.channel != 'SMS' or row.status != 'Queued':
            return
        event = frappe.get_doc('IL Notification Event', row.event)
        if event.event_type != EVENT:
            return
        room = frappe.get_doc('IL Classroom', event.classroom)
        member = frappe.get_doc('IL Member', row.recipient)
        end = reminder_state(room, member, now_datetime())
        phone = frappe.db.get_value('IL Verified Phone', {'user':member.user}, 'phone')
        valid = (end and phone and row.institute == room.institute == member.institute == event.institute
                 and event.user == member.user and event.recipient == member.name
                 and event.event_key == notification_key(reminder_key(room, end), member.name))
        if not valid:
            row.status = 'Skipped'; row.save(ignore_permissions=True); frappe.db.commit()
            return
        if not frappe.conf.get('il_sms_adapter'):
            return
        row.status = 'Review'; row.attempts = int(row.attempts or 0) + 1
        row.save(ignore_permissions=True); frappe.db.commit()
        try:
            from .providers import sms
            result = sms(phone, row.body, row.event_key)
            row.status = 'Accepted'; row.provider_id = result.get('provider_id')
            row.sent_at = now_datetime(); row.last_error = ''
        except Exception:
            row.last_error = 'SMS acceptance uncertain; reconcile before retrying.'
        row.save(ignore_permissions=True); frappe.db.commit()


def dispatch():
    if frappe.conf.get('il_control_plane'):
        return
    now = now_datetime()
    candidates = frappe.db.sql('''SELECT DISTINCT classroom,student FROM `tabIL Paid Access`
        WHERE status IN ('Active','Awaiting key') AND ends_at>%s AND ends_at<=%s''',
        (now, now + timedelta(days=3)), as_dict=True)
    for candidate in candidates:
        room = frappe.get_doc('IL Classroom', candidate.classroom)
        member = frappe.get_doc('IL Member', candidate.student)
        queue_reminder(room, member, now)
    frappe.db.commit()
    rows = frappe.db.sql('''SELECT n.name FROM `tabIL Notification` n
        JOIN `tabIL Notification Event` e ON e.name=n.event
        WHERE e.event_type=%s AND n.channel='SMS' AND n.status='Queued' LIMIT 100''', (EVENT,))
    for (name,) in rows:
        deliver_sms(name)
