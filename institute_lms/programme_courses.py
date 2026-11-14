"""Institute-owned courses with dedicated teaching classrooms."""
import json
import re
import uuid
import frappe
from .programme_grading import weight


@frappe.whitelist()
def teachers():
    from .api import identity, require_role
    from .teaching import institute_profile
    inst, member = identity()
    require_role(member, 'Admin')
    profile = institute_profile(inst)
    users = frappe.get_all('IL Profile Relationship', filters={'profile': profile,
        'kind': 'Teacher membership', 'status': 'Active'}, pluck='user', limit_page_length=0)
    return frappe.get_all('IL Member', filters={'institute': inst.name, 'role': 'Teacher',
        'active': 1, 'user': ['in', users or ['__none__']]}, fields=['name', 'full_name'],
        order_by='full_name', limit_page_length=0)


@frappe.whitelist(methods=['POST'])
def module_code():
    from .api import identity, require_role
    _, member = identity()
    require_role(member, 'Admin')
    code = 'MOD-' + uuid.uuid4().hex.upper()
    # A code is platform-issued, bound to this administrator and not user-editable.
    frappe.cache().set_value('programme-module:' + code, member.user, expires_in_sec=604800)
    return code


@frappe.whitelist(methods=['POST'])
def create(data):
    from .api import identity, require_role, verified_image
    from .teaching import institute_profile, approved_teacher
    from .commercial_rules import duration_days
    from .domain import limited, money
    inst, member = identity()
    require_role(member, 'Admin')
    data = json.loads(data) if isinstance(data, str) else data
    if not isinstance(data, dict) or data.get('name'):
        frappe.throw('Create a new programme intake')
    rows = data.get('modules')
    if not isinstance(rows, list) or not rows:
        frappe.throw('Add at least one module')
    profile = institute_profile(inst)
    codes = set()
    checked = []
    for row in rows:
        code = row.get('module_code', '')
        if (not re.fullmatch(r'MOD-[A-F0-9]{32}', code) or code in codes or
                frappe.cache().get_value('programme-module:' + code) != member.user):
            frappe.throw('A module code expired or is invalid. Remove that module and add it again.')
        if frappe.db.exists('IL Programme Module', {'module_code': code}):
            frappe.throw('This programme was already saved. Refresh your programme list.')
        codes.add(code)
        teacher = approved_teacher(inst, row.get('teacher'), profile)
        title = limited(row.get('title'), 120, 'Module name')
        if not title:
            frappe.throw('Enter every module name')
        try:
            weeks = int(row.get('duration_weeks', 2))
            if not 1 <= weeks <= 52: raise ValueError('Module duration must be 1–52 weeks')
            assessment_weight = float(weight(row.get('assessment_weight', 90)))
        except (TypeError, ValueError) as error:
            frappe.throw(str(error))
        checked.append((code, title, teacher, weeks, assessment_weight))
    try:
        days = duration_days(data.get('access_duration_days'))
        if not days: raise ValueError('Choose a programme access duration')
    except ValueError as error:
        frappe.throw(str(error))
    title = limited(data.get('title'), 120, 'Programme name')
    if not title:
        frappe.throw('Enter a programme name')
    fee = money(data.get('fee'))
    if fee < 0: frappe.throw('Programme tuition cannot be negative')
    p = frappe.get_doc({'doctype': 'IL Programme', 'institute': inst.name, 'provider': profile,
        'title': title, 'description': limited(data.get('description'), 1500, 'Description'),
        'fee': fee, 'currency': 'LKR', 'active': 1, 'access_duration_days': days,
        'duration_months': (days + 29) // 30, 'sequential_modules': 1,
        'cover_image': verified_image(data.get('cover_image', ''), member),
        'profile_image': verified_image(data.get('profile_image', ''), member)})
    from .programme_certificates import configure
    configure(p, data)
    p.insert(ignore_permissions=True)
    for code, title, teacher, weeks, assessment_weight in checked:
        room = frappe.get_doc({'doctype': 'IL Classroom', 'institute': inst.name,
            'title': title, 'subject': title[:60], 'teacher': teacher.name,
            'owner_type': 'Institute', 'public_provider': profile, 'published': 0,
            'teacher_access': 'Teaching only', 'teacher_assignment_active': 1,
            'active': 1, 'programme': p.name, 'billing_type': 'Programme module',
            'fee': fee, 'fee_mode': 'Paid' if fee else 'Free', 'access_duration_days': days,
            'comments_enabled': 1}).insert(ignore_permissions=True)
        p.append('modules', {'classroom': room.name, 'title': title, 'teacher': teacher.name,
            'module_code': code, 'duration_weeks': weeks, 'assessment_weight': assessment_weight})
        from .notification_service import emit
        emit(inst.name, teacher.name, 'programme.assigned', 'programme-assigned:' + code,
            'You have been assigned ' + title + ' in ' + p.title +
            '. Open My classrooms to manage this module.',
            channels=('IN_APP', 'EMAIL', 'SMS'), classroom=room.name)
    p.save(ignore_permissions=True)
    return p.name


@frappe.whitelist()
def payment_details(programme):
    from .api import identity, scoped, require_role
    from .class_keys import bank_details
    inst, member = identity()
    require_role(member, 'Student')
    p = scoped('IL Programme', programme, inst)
    if not p.active or not p.modules:
        frappe.throw('Programme unavailable')
    details = bank_details(p.modules[0].classroom)
    details.update({'fee': p.fee, 'currency': p.currency, 'programme': p.name,
                    'payment_method': 'Bank transfer', 'one_time': True})
    purchase = frappe.db.get_value('IL Programme Enrollment',
        {'programme': p.name, 'student': member.name, 'active': 1}, 'billing_enrollment')
    details['invoice'] = frappe.db.get_value('IL Invoice',
        {'enrollment': purchase, 'student': member.name}, 'name') if purchase else None
    details['invoice_status'] = frappe.db.get_value('IL Invoice', details['invoice'], 'status') if details.get('invoice') else None
    return details


@frappe.whitelist(methods=['POST'])
def module_image(classroom, kind, url):
    from .api import classroom_for, verified_image
    _, member, room = classroom_for(classroom, write=True)
    if not room.get('programme') or kind not in ('cover_image', 'profile_image'):
        frappe.throw('Choose a programme module image')
    room.set(kind, verified_image(url, member))
    room.save(ignore_permissions=True)
    return {'saved': True}


@frappe.whitelist(methods=['POST'])
def module_images(classroom, images):
    """Validate both photo URLs before updating the module in one save."""
    from .api import classroom_for, verified_image
    _, member, room = classroom_for(classroom, write=True)
    images = frappe.parse_json(images) if isinstance(images, str) else images
    if not room.get('programme') or not isinstance(images, dict) or not images or set(images) - {'cover_image', 'profile_image'}:
        frappe.throw('Choose programme module photos')
    checked = {kind: verified_image(url, member) for kind, url in images.items()}
    for kind, url in checked.items():
        room.set(kind, url)
    room.save(ignore_permissions=True)
    return checked
