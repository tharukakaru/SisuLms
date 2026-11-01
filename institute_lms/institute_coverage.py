"""Institute-paid teaching is scoped to confirmed membership and assigned institute classes."""
import frappe

# Deliberately no generic REST, standalone course creation or independent business APIs.
SCOPED_METHODS=frozenset('bootstrap classrooms classroom_detail schedule notifications dashboard_summary news save_session add_material post_announcement post_feedback enrollments'.split())

def enabled():
    return getattr(getattr(frappe,'local',None),'site',None)=='hnb-checkout.localhost' and frappe.conf.get('il_institute_teacher_coverage')==1

def sponsor(institute,user):
    if not enabled():return None
    member=frappe.db.exists('IL Member',{'institute':institute,'user':user,'role':'Teacher','active':1})
    if not member:return None
    profile=frappe.db.get_value('IL Public Profile',{'workspace':institute,'kind':'Institute','status':'Verified'},'name')
    if not profile or not frappe.db.exists('IL Profile Relationship',{'profile':profile,'user':user,'kind':'Teacher membership','status':'Active'}):return None
    name=frappe.db.get_value('IL Account Subscription',{'account_key':'Institute:'+institute,'role':'Institute','institute':institute},'name')
    if not name:return None
    account=frappe.get_doc('IL Account Subscription',name)
    from .account_billing import state
    from frappe.utils import get_datetime,now_datetime
    paid=bool(account.paid_until and get_datetime(account.paid_until)>now_datetime())
    grant=(frappe.conf.get('il_institute_trial_grants') or {}).get(institute) or {}
    trial=bool(grant.get('subscription')==account.name and grant.get('expires_at') and account.trial_until and get_datetime(grant['expires_at'])>now_datetime() and get_datetime(account.trial_until)>=get_datetime(grant['expires_at']))
    if not account.enabled or not (paid or trial) or not state(account)['available']:return None
    return {'account':account,'profile':profile}

def personal(member):
    from .account_billing import account,state
    from .api import institute
    return state(account(institute(),member))['available']

def room_allowed(room,member):
    if not enabled() or member.role!='Teacher':return True
    if personal(member):return True  # Existing assignment/ownership checks still apply in teaching.rights.
    if room.get('owner_type')=='Teacher':return False
    covered=sponsor(room.institute,member.user)
    return bool(covered and room.get('public_provider')==covered['profile'] and room.get('teacher')==member.name and room.get('teacher_assignment_active')!=0)

def request_allowed(method,institute,user):
    prefix='institute_lms.api.'
    return bool(method.startswith(prefix) and method[len(prefix):] in SCOPED_METHODS and sponsor(institute,user))
