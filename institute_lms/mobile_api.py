"""Version-one authenticated mobile facade; existing services retain authorization."""
import frappe

@frappe.whitelist()
def current():
    from .portal_session import current
    from .saas import status
    return {'api_version':1,'session':current(),'subscription':status()}

@frappe.whitelist()
def classes(page=0):
    from .api import classrooms
    return classrooms(page=page)

@frappe.whitelist()
def enrollments(page=0):
    from .api import identity
    inst,m=identity()
    return frappe.get_all('IL Enrollment',filters={'institute':inst.name,'student':m.name,'active':1},
        fields=['name','classroom','active','access_override','expires_at','lifecycle'],limit_start=max(0,min(int(page),10000))*50,limit_page_length=50)

@frappe.whitelist()
def lesson(course,chapter,lesson):
    from .native_access import require_course
    from .api import identity
    identity();require_course(course)
    from lms.lms.utils import get_lesson
    return get_lesson(course,int(chapter),int(lesson))
