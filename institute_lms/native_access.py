"""Fail-closed boundary for upstream LMS reads, including preview lessons.

Only reviewed course-scoped upstream APIs are exposed to portal users when SISU
courses are linked. Unknown native API shapes are denied rather than inferred
from client-controlled extra arguments. System operators retain maintenance access.
"""
from urllib.parse import unquote
import frappe

READERS={'lms.lms.utils.get_lesson','lms.lms.utils.get_course_details','lms.lms.utils.get_course_outline',
         'lms.lms.utils.get_chapters','lms.lms.utils.get_lessons','lms.lms.utils.get_course_progress'}
SAFE={'frappe.auth.get_logged_user','frappe.auth.get_roles','frappe.desk.form.load.getdoctype',
      'login','logout','upload_file','frappe.core.doctype.user.user.reset_password',
      'frappe.core.doctype.user.user.update_password','frappe.integrations.oauth2_logins.login_via_google'}

def require_course(course):
    names=frappe.get_all('IL Classroom',filters={'lms_course':course},pluck='name')
    if not names:return  # upstream retains authority for intentionally unlinked/free courses
    from .api import classroom_for,access
    from .saas import require
    require('lms')
    # Every linked classroom is checked; do not let a cheap duplicate mapping unlock a paid course.
    for name in names:
        room=frappe.get_doc('IL Classroom',name)
        from .retention import access_allowed
        from .commercial import account_for
        commercial=account_for(room,False)
        if not commercial and room.active and room.fee_mode=='Free' and access_allowed(room.as_dict()):continue
        _,member,room=classroom_for(name)
        if not access(room,member)['allowed']:frappe.throw('SISU course payment/access required',frappe.PermissionError)

def validate_link(doc,method=None):
    if not doc.get('lms_course'):return
    # Public files and SCORM paths may be served by nginx before any Frappe hook.
    # They must be moved to protected storage before attaching paid content.
    if doc.get('fee_mode')!='Free' and float(doc.get('fee') or 0)>0:
        lessons=[frappe.get_doc('Course Lesson',name).as_dict() for name in frappe.get_all('Course Lesson',filters={'course':doc.lms_course},pluck='name')]
        if any(x.get('is_scorm_package') or '/files/' in ((x.get('body') or '')+(x.get('content') or '')) for x in lessons):
            frappe.throw('Paid native content contains public files/SCORM. Move it to protected SISU materials before linking.')

def validate_lesson(doc,method=None):
    if doc.get('is_scorm_package') or '/files/' in ((doc.get('body') or '')+(doc.get('content') or '')):
        if frappe.db.exists('IL Classroom',{'lms_course':doc.get('course'),'fee_mode':['!=','Free'],'fee':['>',0]}):
            frappe.throw('Paid course files must use protected SISU materials')

def validate_file(doc,method=None):
    if doc.attached_to_doctype in ('IL Classroom','IL Paper Attempt','IL Delivery Order') and not doc.is_private:
        frappe.throw('Class materials and answers require private storage')
    course=doc.attached_to_name if doc.attached_to_doctype=='LMS Course' else None
    if doc.attached_to_doctype in ('Course Lesson','Course Chapter'):
        course=frappe.db.get_value(doc.attached_to_doctype,doc.attached_to_name,'course')
    if course and not doc.is_private and frappe.db.exists('IL Classroom',{'lms_course':course,'fee_mode':['!=','Free'],'fee':['>',0]}):
        frappe.throw('Paid native course files require private storage')

def file_permission(doc,user=None,permission_type=None):
    if permission_type not in (None,'read'):return None
    if doc.attached_to_doctype=='IL Delivery Order':
        from .delivery import checked_order
        checked_order(doc.attached_to_name)
    if doc.attached_to_doctype=='IL Classroom':
        from .api import accessible_room
        _,member,room=accessible_room(doc.attached_to_name)
        if member.role=='Student':
            protected=frappe.db.exists('IL Material',{'classroom':room.name,'file_id':doc.name}) or frappe.db.exists('IL Material',{'classroom':room.name,'preview_file_id':doc.name})
            if protected:frappe.throw('Open this document through the classroom viewer',frappe.PermissionError)
    if doc.attached_to_doctype=='IL Paper Attempt':
        from .papers import checked
        attempt=frappe.get_doc('IL Paper Attempt',doc.attached_to_name)
        _,member,_=checked(attempt.paper)
        if member.role=='Student' and member.name!=attempt.student:
            frappe.throw('Answer unavailable',frappe.PermissionError)
    if doc.attached_to_doctype in ('LMS Course','Course Lesson','Course Chapter'):
        course=doc.attached_to_name if doc.attached_to_doctype=='LMS Course' else frappe.db.get_value(doc.attached_to_doctype,doc.attached_to_name,'course')
        if course:require_course(course)
    return None  # never grants permission the upstream framework would deny

def guard():
    path=unquote(frappe.local.request.path)
    roles=frappe.get_roles() if frappe.session.user!='Guest' else []
    operator=frappe.session.user=='Administrator' or 'System Manager' in roles
    if operator:return
    method=frappe.form_dict.get('cmd') or (path.split('/method/',1)[1].rstrip('/') if '/method/' in path else '')
    if method.startswith('institute_lms.') or method in SAFE:return
    if method.startswith('frappe.integrations.oauth2_logins.'):return
    linked=frappe.db.exists('IL Classroom',{'lms_course':['is','set']})
    if not linked:return
    if method in READERS:
        course=frappe.form_dict.get('course')
        if not isinstance(course,str) or not course:frappe.throw('Course context required',frappe.PermissionError)
        if frappe.form_dict.get('member') not in (None,'',frappe.session.user):frappe.throw('Foreign progress request',frappe.PermissionError)
        require_course(course);return
    if path.startswith('/private/files/'):
        name=frappe.db.get_value('File',{'file_url':path},'name')
        if name:file_permission(frappe.get_doc('File',name))
        return
    # Cover /api/v1, /api/v2, generic REST, run_doc_method and unknown LMS RPC.
    # Client-supplied course arguments cannot turn an unreviewed endpoint into a safe one.
    if path.startswith('/api/') or method:
        frappe.throw('Use the authorized SISU API for this operation',frappe.PermissionError)
    base='/'+str(frappe.conf.get('lms_path','lms')).strip('/')
    if path.startswith(base+'/courses/'):
        course=path[len(base+'/courses/'):].split('/')[0]
        if course:require_course(course)
