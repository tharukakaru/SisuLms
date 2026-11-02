"""Disabled-by-default shared-campus student membership, not class enrollment."""
import frappe
from frappe.model.naming import make_autoname
from .campus_context import require_user


@frappe.whitelist(methods=['GET'])
def directory(query='', page=0):
    """Discover verified institutes without choosing a workspace first."""
    require_user()
    if not isinstance(query, str) or len(query) > 80:
        frappe.throw('Use a search of up to 80 characters.', frappe.PermissionError)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = -1
    if not 0 <= page <= 1000:
        frappe.throw('Choose a valid results page.', frappe.PermissionError)
    # Explicit public fields only; no account email, contact proof or member data.
    rows = frappe.db.sql('''
        SELECT p.name, p.display_name
        FROM `tabIL Public Profile` p
        WHERE p.kind='Institute' AND p.status='Verified'
          AND LOCATE(%s, p.display_name)>0
          AND EXISTS (SELECT 1 FROM `tabIL Member` m
                      WHERE m.institute=p.workspace AND m.user=p.user
                        AND m.role='Admin' AND m.active=1)
        ORDER BY p.display_name, p.name LIMIT 25 OFFSET %s
    ''', (query.strip(), page * 24), as_dict=True)
    return {'institutes': rows[:24], 'has_more': len(rows) > 24}


@frappe.whitelist(methods=['GET'])
def details():
    user = require_user()
    from .profiles import required
    profile = required()
    if profile.user != user or profile.kind != 'Student':
        frappe.throw('Sign in with your verified student account.', frappe.PermissionError)
    account = frappe.get_doc('User', user)
    phone = frappe.db.get_value('IL Verified Phone', {'user': user}, ['phone', 'verified_at'], as_dict=True)
    return {'first_name': account.first_name, 'last_name': account.last_name or '',
            'email': user, 'phone': phone.phone if phone and phone.verified_at else '',
            'phone_verified': bool(phone and phone.phone and phone.verified_at)}


@frappe.whitelist(methods=['POST'])
def register_student(profile,language="en"):
    if language not in ("en","si","ta"):frappe.throw("Choose a supported language.")
    user = require_user()
    if not isinstance(profile, str) or not profile or len(profile) > 140:
        frappe.throw('Choose an available institute.', frappe.PermissionError)
    from .profiles import required
    student = required()
    if student.user != user or student.kind != 'Student':
        frappe.throw('Sign in with your verified student account.', frappe.PermissionError)
    phone = frappe.db.get_value('IL Verified Phone', {'user': user}, ['phone', 'verified_at'], as_dict=True)
    if not phone or not phone.phone or not phone.verified_at:
        frappe.throw('Verify your mobile number before registering.', frappe.PermissionError)
    provider = frappe.db.get_value('IL Public Profile', {'name': profile, 'kind': 'Institute', 'status': 'Verified'}, ['workspace', 'user', 'display_name'], as_dict=True)
    if not provider or not provider.workspace:
        frappe.throw('This institute is not accepting registrations.', frappe.PermissionError)
    if not frappe.db.exists('IL Member', {'institute': provider.workspace, 'user': provider.user, 'role': 'Admin', 'active': 1}):
        frappe.throw('This institute is not accepting registrations.', frappe.PermissionError)
    # Serialize repeated clicks and simultaneous registration for this account.
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE', (user,))
    previous = frappe.db.get_value('IL Member', {'institute': provider.workspace, 'user': user}, ['name', 'role', 'active'], as_dict=True)
    if previous:
        if previous.role != 'Student' or not previous.active:
            frappe.throw('Your existing membership needs institute review.', frappe.PermissionError)
        from .profiles import relate
        relate(profile,'Follow')
        return result(previous.name, provider, False)
    institute = frappe.get_doc('IL Institute', provider.workspace)
    code = str(institute.code or '')
    if not code or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-' for c in code):
        frappe.throw('Institute setup needs administrator review.', frappe.PermissionError)
    number = make_autoname('ST-' + code + '-.#####')
    member = frappe.get_doc({'doctype': 'IL Member', 'institute': institute.name, 'user': user,
        'role': 'Student', 'full_name': student.display_name, 'phone': phone.phone,
        'language': language, 'active': 1, 'whatsapp_opt_in': 0, 'email_opt_in': 0})
    from .membership_write import authorized_insert
    with authorized_insert(member):
        member.insert(ignore_permissions=True, set_name=number)
    from .account_confirmations import queue
    queue(user,'institute-registration:'+number,'Registration successful','You are registered with '+provider.display_name+'. Student ID: '+number)
    # The usual request transaction commits the member. No explicit commit here.
    # Receipts are queued only after the registration commits.
    from .profiles import relate
    relate(profile,'Follow')
    return result(number, provider, True)


def result(number, provider, created):
    return {'registered': True, 'created': created, 'student_number': number,
            'institute': provider.workspace, 'institute_title': provider.display_name,
            'message': 'You are registered with this institute. Class enrollment is separate.'}


@frappe.whitelist(methods=['POST'])
def register_teacher(profile):
    """Register with an independent teacher; does not grant institute/class access."""
    import hashlib
    from .profiles import required,write
    user=require_user();student=required()
    if student.kind!='Student':frappe.throw('Student account required.',frappe.PermissionError)
    phone=frappe.db.get_value('IL Verified Phone',{'user':user},['phone','verified_at'],as_dict=True)
    if not phone or not phone.phone or not phone.verified_at:frappe.throw('Verify your mobile first.')
    provider=frappe.get_doc('IL Public Profile',profile)
    if provider.kind!='Teacher' or provider.status!='Verified':frappe.throw('Teacher unavailable.')
    if frappe.db.exists('IL Member',{'user':provider.user,'role':'Teacher','active':1}):frappe.throw('Register through this teacher’s institute.')
    frappe.db.sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(user,))
    key=hashlib.sha256(f'{user}:{profile}:Student join'.encode()).hexdigest()
    name=frappe.db.get_value('IL Profile Relationship',{'relationship_key':key},'name')
    if name:
        link=frappe.get_doc('IL Profile Relationship',name)
        if link.status!='Active':frappe.throw('Your previous registration requires teacher review.')
    else:
        link=frappe.get_doc({'doctype':'IL Profile Relationship','relationship_key':key,'profile':profile,'user':user,'kind':'Student join','status':'Active'})
        link.flags.community_service=True
        link.insert(ignore_permissions=True,set_name=make_autoname('ST-IND-.#####'))
        from .account_confirmations import queue
        queue(user,'teacher-registration:'+link.name,'Registration successful','You are registered with '+provider.display_name+'. Student ID: '+link.name)
    from .profiles import relate
    relate(profile,'Follow')
    return {'registered':True,'created':not bool(name),'student_number':link.name,'institute':None,'institute_title':provider.display_name}


@frappe.whitelist(methods=['GET'])
def people(query=''):
    """Public profile fields of active members in the selected institute only."""
    from .campus_context import current_institute
    inst=current_institute()
    users=frappe.get_all('IL Member',filters={'institute':inst.name,'active':1,'role':['in',['Teacher','Admin']]},pluck='user',limit_page_length=0)
    return frappe.get_all('IL Public Profile',filters={'user':['in',users or ['__none__']],'status':'Verified'},
        or_filters=[['display_name','like','%'+str(query)[:80]+'%'],['username','like','%'+str(query)[:80]+'%']],
        fields=['name','display_name','kind','profile_image','tagline','bio'],order_by='display_name',limit_page_length=100)
