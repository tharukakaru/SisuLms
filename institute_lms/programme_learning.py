"""Scoped programme progress; attendance affects marks, never progression."""
import hashlib
import frappe
from frappe.utils import now_datetime
from .programme_grading import module_grade


def purchase_for(programme, student):
    return frappe.db.get_value('IL Programme Enrollment',
        {'programme': programme, 'student': student, 'active': 1}, 'name')


def completed_rooms(purchase):
    return set(frappe.get_all('IL Programme Progress', filters={'enrollment': purchase},
                              pluck='classroom', limit_page_length=0)) if purchase else set()


def access_reason(room, member):
    if member.role != 'Student' or not room.get('programme'):
        return None
    programme = frappe.get_doc('IL Programme', room.programme)
    if programme.institute != member.institute or not programme.active:
        return 'Programme unavailable'
    if not programme.get('sequential_modules'):
        return None
    purchase = purchase_for(programme.name, member.name)
    if not purchase:
        return 'Enrol in the programme first'
    completed = completed_rooms(purchase)
    preceding = []
    for module in programme.modules:
        if module.classroom == room.name:
            if room.name in completed or all(name in completed for name in preceding):
                return None
            return 'Complete the preceding module before opening this module'
        preceding.append(module.classroom)
    return 'Classroom is not part of this programme'


def grading(room, student, module):
    assessments = []
    for quiz in frappe.get_all('IL Classroom Quiz', filters={
            'institute': room.institute, 'classroom': room.name, 'status': 'Published'},
            fields=['name'], limit_page_length=0):
        answer = frappe.db.get_value('IL Classroom Quiz Submission',
            {'quiz': quiz.name, 'student': student, 'classroom': room.name},
            ['score', 'total', 'submitted_at'], as_dict=True)
        submitted = bool(answer and answer.submitted_at)
        assessments.append(dict(submitted=submitted, graded=submitted,
            score=answer.score if answer else None, maximum=answer.total if answer else None))
    for paper in frappe.get_all('IL Paper', filters={
            'institute': room.institute, 'classroom': room.name, 'status': 'Published'},
            fields=['name', 'max_marks'], limit_page_length=0):
        answer = frappe.db.get_value('IL Paper Attempt', {'paper': paper.name, 'student': student},
                                    ['status', 'score'], as_dict=True)
        assessments.append(dict(submitted=bool(answer and answer.status in ('Submitted', 'Graded')),
            graded=bool(answer and answer.status == 'Graded'),
            score=answer.score if answer else None, maximum=paper.max_marks))
    sessions = frappe.get_all('IL Session', filters={'institute': room.institute,
        'classroom': room.name, 'status': ['!=', 'Cancelled']},
        fields=['name', 'ends_at'], limit_page_length=0)
    records = {r.session: r.status for r in frappe.get_all('IL Attendance',
        filters={'institute': room.institute, 'classroom': room.name, 'student': student},
        fields=['session', 'status'], limit_page_length=0)}
    attendance = [records.get(s.name) if s.ends_at and s.ends_at <= now_datetime() else None for s in sessions]
    configured = module.get('assessment_weight')
    return module_grade(assessments, attendance, 90 if configured is None else configured)


@frappe.whitelist()
def status(programme):
    from .api import identity, scoped, access
    from .teaching import rights
    inst, member = identity()
    p = scoped('IL Programme', programme, inst)
    purchase = purchase_for(p.name, member.name) if member.role == 'Student' else None
    done = completed_rooms(purchase)
    rows = []
    for module in p.modules:
        room = scoped('IL Classroom', module.classroom, inst)
        if member.role == 'Teacher' and not rights(room, member)['teach']:
            continue
        decision = access(room, member)
        rows.append({'classroom': room.name, 'title': module.title,
            'module_code': module.get('module_code'), 'completed': room.name in done,
            'allowed': bool(decision['allowed']), 'reason': decision['reason'],
            'grade': grading(room, member.name, module) if purchase else None})
    return {'programme': p.name, 'enrolled': bool(purchase), 'modules': rows,
            'completed': bool(purchase and p.modules and all(m.classroom in done for m in p.modules))}


@frappe.whitelist(methods=['POST'])
def complete(classroom):
    from .api import identity, scoped, require_role, accessible_room
    inst, member = identity()
    require_role(member, 'Student')
    room = scoped('IL Classroom', classroom, inst)
    if not room.get('programme'):
        frappe.throw('Programme module required')
    frappe.db.sql('SELECT name FROM `tabIL Programme` WHERE name=%s FOR UPDATE', (room.programme,))
    p = scoped('IL Programme', room.programme, inst)
    purchase = purchase_for(p.name, member.name)
    if not purchase:
        frappe.throw('Enrol in this programme first', frappe.PermissionError)
    frappe.db.sql('SELECT name FROM `tabIL Programme Enrollment` WHERE name=%s FOR UPDATE', (purchase,))
    # Recheck paid access, membership and preceding modules inside the transaction.
    accessible_room(classroom)
    module = next((m for m in p.modules if m.classroom == classroom), None)
    if not module:
        frappe.throw('Programme module unavailable')
    key = hashlib.sha256((purchase + ':' + classroom).encode()).hexdigest()
    if not frappe.db.exists('IL Programme Progress', {'progress_key': key}):
        grade = grading(room, member.name, module)
        if not grade['can_complete']:
            frappe.throw('Submit every published assessment before completing this module')
        doc = frappe.get_doc({'doctype': 'IL Programme Progress', 'progress_key': key,
            'institute': inst.name, 'programme': p.name, 'enrollment': purchase,
            'student': member.name, 'classroom': classroom, 'completed_at': now_datetime()})
        doc.flags.programme_service = True
        doc.insert(ignore_permissions=True)
    return status(p.name)


@frappe.whitelist()
def gradebook(classroom, page=0):
    from .api import classroom_for, scoped, paginate
    from .teaching import require
    inst, member, room = classroom_for(classroom, write=True)
    require(room, member, 'teach')
    if not room.get('programme'):
        frappe.throw('Programme module required')
    p = scoped('IL Programme', room.programme, inst)
    module = next((m for m in p.modules if m.classroom == room.name), None)
    if not module:
        frappe.throw('Programme module unavailable')
    students = frappe.get_all('IL Enrollment', filters={'institute': inst.name,
        'classroom': room.name, 'active': 1}, fields=['student', 'programme_enrollment'],
        order_by='student', limit_start=paginate(page, 50), limit_page_length=51)
    return {'has_more': len(students) > 50, 'rows': [
        {'student': row.student, 'full_name': frappe.db.get_value('IL Member', row.student, 'full_name'),
         'completed': room.name in completed_rooms(row.programme_enrollment),
         'grade': grading(room, row.student, module)} for row in students[:50]]}
