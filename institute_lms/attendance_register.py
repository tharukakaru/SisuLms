"""Editable, paginated session checklists scoped to teaching permissions."""
import json
import frappe
from frappe.utils import get_datetime, now_datetime
from .api import classroom_for
from .operations import record


def context(session):
    meeting=frappe.get_doc('IL Session',session)
    inst,member,room=classroom_for(meeting.classroom,write=True)
    if meeting.institute!=inst.name or meeting.status=='Cancelled':
        frappe.throw('Session unavailable',frappe.PermissionError)
    if get_datetime(meeting.starts_at)>now_datetime():
        frappe.throw('The attendance register opens when the session starts')
    return meeting,room


def validate_entries(entries):
    if not isinstance(entries,list) or not 1<=len(entries)<=100:
        raise ValueError('Submit between 1 and 100 students at a time')
    seen=set()
    for row in entries:
        if not isinstance(row,dict) or not isinstance(row.get('student'),str):
            raise ValueError('Invalid student entry')
        if row['student'] in seen or row.get('status') not in ('Present','Absent','Excused'):
            raise ValueError('Duplicate student or invalid attendance status')
        if not isinstance(row.get('note',''),str) or len(row.get('note',''))>500:
            raise ValueError('Use a note of at most 500 characters')
        seen.add(row['student'])
    return entries


@frappe.whitelist()
def roster(session,page=0):
    meeting,room=context(session)
    page=max(0,min(int(page),10000))
    rows=frappe.db.sql('''SELECT DISTINCT m.name AS student,m.full_name
        FROM `tabIL Enrollment` e JOIN `tabIL Member` m ON m.name=e.student
        WHERE e.classroom=%s AND e.institute=%s AND e.active=1
        AND m.institute=%s AND m.active=1 AND m.role='Student'
        ORDER BY m.full_name,m.name LIMIT 101 OFFSET %s''',
        (room.name,room.institute,room.institute,page*100),as_dict=True)
    more=len(rows)>100
    rows=rows[:100]
    saved=frappe.get_all('IL Attendance',filters={'institute':room.institute,
        'classroom':room.name,'session':meeting.name,
        'student':['in',[r.student for r in rows] or ['__none__']]},
        fields=['student','status','note'],limit_page_length=100)
    lookup={r.student:r for r in saved}
    for row in rows:
        previous=lookup.get(row.student)
        row.update(status=previous.status if previous else None,
                   note=(previous.note or '') if previous else '')
    return {'rows':rows,'has_more':more}


@frappe.whitelist(methods=['POST'])
def submit(session,entries):
    meeting,room=context(session)
    try:
        entries=validate_entries(json.loads(entries) if isinstance(entries,str) else entries)
    except (ValueError,TypeError) as exc:
        frappe.throw(str(exc))
    for row in entries:
        if not frappe.db.exists('IL Member',{'name':row['student'],'institute':room.institute,'role':'Student','active':1}):
            frappe.throw('Student unavailable',frappe.PermissionError)
        if not frappe.db.exists('IL Enrollment',{'classroom':room.name,'institute':room.institute,'student':row['student'],'active':1}):
            frappe.throw('Student is not enrolled',frappe.PermissionError)
    for row in entries:
        record(room,meeting,row['student'],row['status'],'Physical',row.get('note',''))
    return {'saved':len(entries)}
