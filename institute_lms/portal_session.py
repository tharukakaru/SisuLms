"""Session routing is resolved on the server. A selected login tile grants no role."""
import frappe
from .wallet import owner, admin_actor

@frappe.whitelist(allow_guest=True, methods=['GET'])
def current():
    if frappe.session.user=='Guest': return {'authenticated':False}
    if not frappe.db.get_value('User',frappe.session.user,'enabled'): frappe.throw('Account disabled',frappe.PermissionError)
    csrf=frappe.sessions.get_csrf_token()
    if admin_actor():
        owner()
        return {'authenticated':True,'role':'Super Admin','control_plane':bool(frappe.conf.get('il_control_plane')),'user':frappe.session.user,'csrf_token':csrf}
    if frappe.conf.get('il_control_plane'):
        return {'authenticated':True,'role':'Billing','control_plane':True,'user':frappe.session.user,'csrf_token':csrf}
    from .campus_context import enabled, SESSION_KEY
    shared = enabled()
    if shared:
        selected = frappe.session.data.get(SESSION_KEY)
        admins=[]
        if not selected or not frappe.db.exists('IL Member', {'institute':selected,'user':frappe.session.user,'active':1}):
            admins=frappe.get_all('IL Member',filters={'user':frappe.session.user,'role':['in',['Admin','Teacher']],'active':1},pluck='institute')
            admins=sorted(set(admins))
            # An active membership is the authority; registration choices never grant access.
            personal=frappe.db.get_value('IL Public Profile',
                {'user':frappe.session.user,'kind':'Teacher','status':'Verified'},'workspace')
            if admins:
                selected=personal if personal in admins else admins[0]
                frappe.session.data[SESSION_KEY]=selected
                frappe.local.session_obj.update(force=True)

        if not selected or not frappe.db.exists('IL Member', {'institute': selected, 'user': frappe.session.user, 'active': 1}):
            from .onboarding import account_kind
            kind=account_kind()
            path=''
            rows=[]
            if kind in ('Teacher','Institute'):
                from .onboarding_navigation import teaching_path
                rows=frappe.get_all('IL Registration Request',filters={'email':frappe.session.user,'account_type':'Institute' if kind=='Institute' else 'Individual Teacher','status':'Approved','email_verified':1},fields=['details'],order_by='creation desc',limit_page_length=10)
                path=teaching_path(rows,frappe.session.user)
            from .onboarding_navigation import profile_pending
            return {'authenticated':True,'role':'Campus','shared_campus':True,'member':None,
                    'provider_onboarding_required':kind in ('Teacher','Institute') and (profile_pending(rows) or not frappe.db.exists('IL Public Profile',{'user':frappe.session.user}) or not frappe.db.exists('IL Verified Phone',{'user':frappe.session.user})),
                    'onboarding_kind':kind,'teaching_path':path,'workspace_choices_required':len(admins)>1,'user':frappe.session.user,'csrf_token':csrf}
    from .api import institute
    inst=institute()
    member=frappe.db.get_value('IL Member',{'institute':inst.name,'user':frappe.session.user,'active':1},['name','role','full_name','user'],as_dict=True)
    if member and member.role=="Student":
        from .portal_policy import require_google_student
        require_google_student()
    if not member:
        from .workspace import active_operator,actor
        if active_operator():
            actor(True)
            return {'authenticated':True,'role':'Operator','user':frappe.session.user,'csrf_token':csrf}
    onboarding_kind=None
    if not member:
        from .onboarding import account_kind
        onboarding_kind=account_kind()
    # Framework System Managers retain technical site administration, not automatic platform ownership.
    return {'authenticated':True,'role':member.role if member else 'Onboarding','shared_campus':shared,'onboarding_kind':onboarding_kind,'member':member,'user':frappe.session.user,'csrf_token':csrf}

@frappe.whitelist()
def overview():
    owner()
    return {'students':frappe.db.count('IL Member',{'role':'Student','active':1}),
        'teachers':frappe.db.count('IL Public Profile',{'kind':'Teacher','status':'Verified'}),
        'institutes':frappe.db.count('IL Public Profile',{'kind':'Institute','status':'Verified'}),
        'pending_profiles':frappe.db.count('IL Public Profile',{'status':'Pending'}),
        'pending_payouts':frappe.db.count('IL Payout Request',{'status':'Pending'})}
