"""Classroom assessments. All reads use classroom gates; keys are manager-only."""
import hashlib
import json
import frappe
from frappe.utils import now_datetime
from .api import accessible_room
from .teaching import rights
from .classroom_quiz_rules import normalize, public_questions, grade

QUIZ = 'IL Classroom Quiz'
ATTEMPT = 'IL Classroom Quiz Submission'


def room_access(classroom, manage=False):
    inst, member, room = accessible_room(classroom)
    can_manage = member.role in ('Teacher', 'Admin') and rights(room, member)['edit']
    if (manage or member.role != 'Student') and not can_manage:
        frappe.throw('Classroom management access required', frappe.PermissionError)
    return inst, member, room, can_manage


def checked(name, manage=False, for_update=False):
    doc = frappe.get_doc(QUIZ, name, for_update=for_update)
    inst, member, room, can_manage = room_access(doc.classroom, manage)
    if doc.institute != inst.name or doc.institute != room.institute:
        frappe.throw('Quiz unavailable', frappe.PermissionError)
    if not can_manage and doc.status != 'Published':
        frappe.throw('Quiz unavailable', frappe.PermissionError)
    return doc, member, can_manage


def write(doc):
    doc.flags.classroom_quiz_service = True
    return doc.save(ignore_permissions=True)


def lock(name):
    frappe.db.sql('SELECT name FROM `tabIL Classroom Quiz` WHERE name=%s FOR UPDATE', (name,))


def key(quiz, user):
    return hashlib.sha256((quiz + ':' + user).encode()).hexdigest()


def summary(doc):
    return {k: doc.get(k) for k in ('name', 'quiz', 'classroom', 'score', 'total', 'percentage', 'submitted_at')}


@frappe.whitelist()
def metadata(classroom):
    """Authorize independently of quiz records, then inspect schema without writes."""
    _, _, _, manage = room_access(classroom)
    required = {
        QUIZ: {'institute', 'classroom', 'title', 'instructions', 'status', 'questions',
               'question_count', 'published_by', 'published_at'},
        ATTEMPT: {'quiz', 'institute', 'classroom', 'student', 'student_user', 'attempt_key',
                  'answers', 'snapshot', 'correctness', 'score', 'total', 'percentage', 'submitted_at'},
    }
    missing = []
    for doctype, columns in required.items():
        if (not frappe.db.exists('DocType', doctype) or not frappe.db.table_exists(doctype)
                or not columns.issubset(set(frappe.db.get_table_columns(doctype)))):
            missing.append(doctype)
    return {'can_manage': bool(manage), 'schema_ready': not missing,
            'missing_schema': missing if manage else []}


@frappe.whitelist()
def listing(classroom, page=0):
    inst, member, room, manage = room_access(classroom)
    filters = {'institute': inst.name, 'classroom': room.name}
    if not manage:
        filters['status'] = 'Published'
    rows = frappe.get_all(QUIZ, filters=filters,
        fields=['name', 'classroom', 'title', 'instructions', 'status', 'question_count', 'modified'],
        start=max(0, min(int(page), 10000))*30, limit_page_length=30, order_by='creation desc')
    if not manage:
        for row in rows:
            row['submitted'] = bool(frappe.db.exists(ATTEMPT, {'attempt_key': key(row.name, frappe.session.user)}))
    return {'items': rows, 'can_manage': bool(manage)}


@frappe.whitelist()
def detail(name):
    doc, member, manage = checked(name)
    result = {k: doc.get(k) for k in ('name', 'classroom', 'title', 'instructions', 'status', 'modified')}
    questions = json.loads(doc.questions)
    result['questions'] = questions if manage else public_questions(questions)
    result['can_manage'] = bool(manage)
    result['locked'] = bool(frappe.db.exists(ATTEMPT, {'quiz': name})) if manage else False
    if not manage:
        attempt = frappe.db.get_value(ATTEMPT, {'attempt_key': key(name, frappe.session.user)}, 'name')
        result['result'] = summary(frappe.get_doc(ATTEMPT, attempt)) if attempt else None
    return result


@frappe.whitelist(methods=['POST'])
def save(data, publish=False):
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, dict) or type(publish) is not bool:
        frappe.throw('Invalid quiz request')
    inst, _, room, _ = room_access(data.get('classroom'), True)
    if data.get('name'):
        checked(data['name'], True)
        lock(data['name'])
        doc, _, _ = checked(data['name'], True, for_update=True)
        if doc.classroom != room.name:
            frappe.throw('Quiz classroom cannot change')
        if str(doc.modified) != str(data.get('modified')):
            frappe.throw('This quiz changed. Reopen it before editing; your entered values have been retained.')
        # Same parent lock is used for submission, so editing and first submit cannot race.
        if frappe.db.sql('SELECT name FROM `tabIL Classroom Quiz Submission` WHERE quiz=%s LIMIT 1 FOR UPDATE', (doc.name,)):
            frappe.throw('Submitted quizzes cannot be edited. Create a new quiz.')
    else:
        doc = frappe.get_doc({'doctype': QUIZ, 'institute': inst.name, 'classroom': room.name, 'status': 'Draft'})
    try:
        clean = normalize(data, complete=publish or doc.status == 'Published')
    except ValueError as exc:
        frappe.throw(str(exc))
    doc.title = clean['title']; doc.instructions = clean['instructions']
    doc.questions = json.dumps(clean['questions'], ensure_ascii=False)
    doc.question_count = len(clean['questions'])
    if publish and doc.status != 'Published':
        doc.status = 'Published'; doc.published_by = frappe.session.user; doc.published_at = now_datetime()
    write(doc)
    return {'name': doc.name, 'status': doc.status, 'modified': str(doc.modified)}


@frappe.whitelist(methods=['POST'])
def submit(name, answers):
    _, member, manage = checked(name)
    if member.role != 'Student' or manage:
        frappe.throw('Student membership required', frappe.PermissionError)
    lock(name)
    doc, member, _ = checked(name, for_update=True)
    attempt_key = key(name, frappe.session.user)
    existing = frappe.db.sql('SELECT name FROM `tabIL Classroom Quiz Submission` WHERE attempt_key=%s FOR UPDATE', (attempt_key,))
    if existing:
        return summary(frappe.get_doc(ATTEMPT, existing[0][0], for_update=True))
    if isinstance(answers, str):
        answers = json.loads(answers)
    questions = json.loads(doc.questions)
    try:
        result = grade(questions, answers)
    except ValueError as exc:
        frappe.throw(str(exc))
    submission = write(frappe.get_doc({'doctype': ATTEMPT, 'quiz': name, 'classroom': doc.classroom,
        'institute': doc.institute, 'student': member.name, 'student_user': frappe.session.user,
        'attempt_key': attempt_key, 'answers': json.dumps(answers), 'snapshot': doc.questions,
        'correctness': json.dumps(result['correctness']), 'score': result['score'],
        'total': result['total'], 'percentage': result['percentage'], 'submitted_at': now_datetime()}))
    return summary(submission)


@frappe.whitelist()
def submissions(name, page=0):
    doc, member, manage = checked(name)
    filters = {'quiz': doc.name, 'classroom': doc.classroom, 'institute': doc.institute}
    if not manage:
        filters['student_user'] = frappe.session.user
    fields = ['name', 'quiz', 'classroom', 'score', 'total', 'percentage', 'submitted_at']
    if manage:
        fields += ['student', 'student_user', 'answers', 'correctness', 'snapshot']
    return frappe.get_all(ATTEMPT, filters=filters, fields=fields,
        start=max(0, min(int(page), 10000))*30, limit_page_length=30, order_by='creation desc')
