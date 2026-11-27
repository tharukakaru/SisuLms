"""Reviewed institute assignments. Requests never revoke teaching access."""
import frappe
from frappe.utils import now_datetime
from .api import identity, scoped, classroom_for, require_role
from .teaching import require, approved_teacher

DT = 'IL Classroom Handover'


def write(doc):
    doc.flags.classroom_handover_service = True
    return doc.save(ignore_permissions=True)


def lock_room(name):
    frappe.db.sql('SELECT name FROM `tabIL Classroom` WHERE name=%s FOR UPDATE', (name,))


@frappe.whitelist(methods=['POST'])
def request_leave(classroom, reason):
    inst, member, room = classroom_for(classroom, write=True)
    lock_room(room.name)
    room.reload()
    require(room, member, 'teach')
    if member.role != 'Teacher' or room.owner_type != 'Institute' or room.teacher != member.name:
        frappe.throw('Only the assigned institute teacher can request a handover', frappe.PermissionError)
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 1000:
        frappe.throw('Enter a reason of up to 1,000 characters')
    existing = frappe.db.get_value(DT, {'classroom': room.name, 'teacher': member.name, 'status': 'Pending'}, 'name')
    if existing:
        return {'name': existing, 'status': 'Pending'}
    doc = write(frappe.get_doc(dict(doctype=DT, institute=inst.name, classroom=room.name,
        teacher=member.name, requested_by=member.user, reason=reason.strip(), status='Pending')))
    return {'name': doc.name, 'status': doc.status}


@frappe.whitelist()
def listing():
    inst, member = identity()
    require_role(member, 'Admin', 'Teacher')
    filters = {'institute': inst.name, 'status': 'Pending'}
    if member.role == 'Teacher':
        filters['teacher'] = member.name
    rows = frappe.get_all(DT, filters=filters,
        fields=['name', 'classroom', 'teacher', 'reason', 'status', 'creation'], order_by='creation asc', limit_page_length=200)
    for row in rows:
        row['classroom_title'] = frappe.db.get_value('IL Classroom', row.classroom, 'title')
        row['teacher_name'] = frappe.db.get_value('IL Member', row.teacher, 'full_name')
    return rows


@frappe.whitelist(methods=['POST'])
def review(name, decision, replacement=None):
    inst, member = identity()
    require_role(member, 'Admin')
    if decision not in ('Approved', 'Rejected'):
        frappe.throw('Choose approve or reject')
    initial = scoped(DT, name, inst)
    # Match submission lock order; serialize duplicate decisions and classroom edits.
    lock_room(initial.classroom)
    doc = frappe.get_doc(DT, name, for_update=True)
    if doc.institute != inst.name:
        frappe.throw('Request unavailable', frappe.PermissionError)
    if doc.status != 'Pending':
        frappe.throw('This request has already been reviewed. Refresh the list.')
    room = scoped('IL Classroom', doc.classroom, inst)
    require(room, member, 'assign')
    if decision == 'Approved':
        if room.owner_type != 'Institute' or room.teacher != doc.teacher or not room.teacher_assignment_active:
            frappe.throw('The assignment has changed. Reject this outdated request and review the classroom.')
        if not replacement or replacement == doc.teacher:
            frappe.throw('Choose a different replacement teacher before approving')
        if room.public_provider:
            teacher = approved_teacher(inst, replacement, room.public_provider)
        else:
            from .internal_classrooms import teacher_for
            teacher = teacher_for(inst, replacement)
        room.teacher = teacher.name
        room.teacher_assignment_active = 1
        room.save(ignore_permissions=True)
        # Programme timetables also keep a copy of the assignment.
        for module in frappe.get_all('IL Programme Module', filters={'classroom': room.name}, fields=['name', 'parent']):
            programme = scoped('IL Programme', module.parent, inst)
            frappe.db.set_value('IL Programme Module', module.name, 'teacher', teacher.name)
        doc.replacement = teacher.name
    doc.status = decision
    doc.reviewed_by = member.user
    doc.reviewed_at = now_datetime()
    write(doc)
    room.add_comment('Info', 'Classroom handover ' + decision.lower() + ': ' + doc.name)
    return {'status': doc.status}


@frappe.whitelist()
def institute_plan():
    """Minimal, read-only projection of this institute's plan, never personal billing."""
    inst, member = identity()
    require_role(member, 'Admin', 'Teacher')
    from .internal_classrooms import teacher_affiliated
    if member.role == 'Teacher' and not teacher_affiliated(inst.name, member.user):
        frappe.throw('Active institute membership required', frappe.PermissionError)
    name = frappe.db.get_value('IL Account Subscription',
        {'account_key': 'Institute:' + inst.name, 'role': 'Institute', 'institute': inst.name}, 'name')
    if not name:
        return {'institute': inst.title, 'plan': None, 'state': 'Not configured', 'features': {}}
    from .account_billing import state
    from .plan_catalog import plan_features, plan
    account = frappe.get_doc('IL Account Subscription', name)
    return {'institute': inst.title, 'plan': account.plan, 'state': state(account)['state'],
        'monthly_lkr': plan(account.plan)['monthly_lkr'], 'features': plan_features(account.plan), 'card_features': plan(account.plan)['card_features'], 'description': plan(account.plan)['description']}
