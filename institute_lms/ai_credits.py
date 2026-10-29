"""Monthly personal limits under the existing serialized organization budget."""
import json
import frappe
from .saas import state, resolved, managed, audit
from .usage import used, period
from .full_rules import credit_check

def user_used(user, bucket):
    rows = frappe.db.sql('SELECT charged_units FROM `tabIL AI Usage` WHERE user=%s AND period=%s FOR UPDATE', (user, bucket))
    return sum(int(row[0] or 0) for row in rows)

def allocation(user, bucket):
    return int(frappe.db.get_value('IL AI Allocation', {'user': user, 'period': bucket}, 'credits') or 0)

def enforce(user, quantity):
    sub = state(lock=True)
    policy = resolved(sub)
    bucket = period('ai_credits')
    try:
        credit_check(sub.get('ai_mode') or 'Individual', allocation(user, bucket), user_used(user, bucket),
                     used('ai_credits', bucket), policy['limits']['ai_credits'], quantity)
    except ValueError as error:
        frappe.throw(str(error), frappe.PermissionError)

@frappe.whitelist()
def status():
    from .api import identity
    _, member = identity()
    sub = state(lock=True)
    policy = resolved(sub)
    bucket = period('ai_credits')
    mine = user_used(member.user, bucket)
    cap = allocation(member.user, bucket)
    total = used('ai_credits', bucket)
    mode = sub.get('ai_mode') or 'Individual'
    from datetime import datetime
    from .full_rules import month_end
    reset = month_end(datetime.strptime(bucket+'-01', '%Y-%m-%d')).isoformat()
    return {'mode': mode, 'period': bucket, 'reset_at': reset, 'used': mine,
            'allocated': cap if mode == 'Individual' else None,
            'remaining': max(0, cap-mine) if mode == 'Individual' else None,
            'organization_used': total, 'organization_limit': policy['limits']['ai_credits'],
            'organization_remaining': max(0, policy['limits']['ai_credits']-total)}

@frappe.whitelist()
def management(search="", role=None, page=0):
    from .api import identity, require_role
    inst, member = identity()
    require_role(member, 'Admin')
    info = status()
    filters={'institute':inst.name,'active':1}
    if role in ('Student','Teacher','Admin'):filters['role']=role
    if search:filters['full_name']=['like','%'+str(search)[:80]+'%']
    rows=frappe.get_all('IL Member',filters=filters,fields=['name','user','full_name','role'],
        order_by='full_name asc, name asc',start=max(0,min(int(page),10000))*50,limit_page_length=50)
    totals=frappe.db.sql('SELECT COALESCE(SUM(credits),0) FROM `tabIL AI Allocation` WHERE period=%s',(info['period'],))
    allocated=int(totals[0][0]) if totals else 0
    for row in rows:
        row['allocated'] = allocation(row.user, info['period'])
        row['used'] = user_used(row.user, info['period'])
        row['remaining'] = max(0, row['allocated']-row['used'])
    history = frappe.get_all('IL SaaS Audit', filters={'action':['in',['AI allocation','AI credit mode']]},
                            fields=['action','creation','actor','details'], order_by='creation desc', limit_page_length=30)
    return {**info, 'users': rows, 'history': history, 'page':int(page),'has_more':len(rows)==50,
            'total_allocated':allocated,'unallocated':max(0,info['organization_limit']-allocated)}

@frappe.whitelist(methods=['POST'])
def configure(mode, allocations=None, reason=''):
    from .api import identity, require_role
    from .pricing_rules import integer
    inst, member = identity()
    require_role(member, 'Admin')
    sub = state(lock=True)
    if mode not in ('Individual','Shared') or not 3 <= len(str(reason).strip()) <= 500:
        frappe.throw('Choose a mode and supply an audit reason')
    values = json.loads(allocations) if isinstance(allocations, str) else allocations or {}
    if not isinstance(values, dict) or len(values) > 1000:
        frappe.throw('Invalid allocation list')
    bucket = period('ai_credits')
    existing = {row.user: int(row.credits) for row in frappe.get_all('IL AI Allocation',
                filters={'period': bucket}, fields=['user','credits'])}
    for user, amount in values.items():
        if not frappe.db.exists('IL Member', {'institute':inst.name,'user':user,'active':1}):
            frappe.throw('Only active local members can receive credits', frappe.PermissionError)
        credits = integer(amount, 'Credits', 100000000)
        if credits < user_used(user, bucket):
            frappe.throw('Allocation cannot be below credits already spent this month')
        existing[user] = credits
    cap = resolved(sub)['limits']['ai_credits']
    if (values or mode == 'Individual') and sum(existing.values()) > cap:
        frappe.throw('Saved allocations exceed the organization monthly pool')
    for user in values:
        key = frappe.db.get_value('IL AI Allocation', {'user':user,'period':bucket}, 'name')
        doc = frappe.get_doc('IL AI Allocation', key) if key else frappe.get_doc({'doctype':'IL AI Allocation',
            'allocation_key':bucket+':'+user,'user':user,'period':bucket,'institute':inst.name})
        doc.credits = existing[user]
        managed(doc)
        audit('AI allocation', doc.name, str(existing[user])+': '+reason)
    sub.ai_mode = mode
    managed(sub)
    audit('AI credit mode', sub.name, mode+': '+reason)
    return management()
