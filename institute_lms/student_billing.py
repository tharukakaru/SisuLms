"""Student-only view of enrolled providers and the student's own class bills."""
import frappe
@frappe.whitelist(methods=['POST'])
def status():
    from .api import identity,require_role,invoices
    from .commercial import account_for,slips
    inst,member=identity();require_role(member,'Student')
    enrollments=frappe.get_all('IL Enrollment',filters={'institute':inst.name,'student':member.name,'active':1},pluck='classroom')
    providers=[];seen=set()
    for name in enrollments:
        room=frappe.get_doc('IL Classroom',name)
        if room.institute!=inst.name:continue
        account=account_for(room,False)
        if not account or account.name in seen:continue
        seen.add(account.name)
        user=account.owner_user if account.owner_type=='Teacher' else None
        title=frappe.db.get_value('IL Public Profile',{'user':user,'status':'Verified'},'display_name') if user else inst.title
        providers.append(dict(name=title or room.get("teacher_name") or inst.title,kind=account.owner_type,plan=account.plan))
    return dict(providers=providers,invoices=invoices(),slips=slips())
