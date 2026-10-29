"""Non-destructive final policy initialization. Historical contracts remain intact."""
import json
import frappe
from institute_lms.saas import managed
from institute_lms.full_rules import starter_policy

def execute():
    from institute_lms.patches.run1 import execute as seed
    seed()
    base = starter_policy(frappe.conf.get('il_starter_limits'))
    plan = frappe.get_doc('IL SaaS Plan','STARTER')
    # Only fill the old deliberately empty seed; never silently enlarge operator limits.
    if not any(json.loads(plan.limits or '{}').values()):
        plan.features=json.dumps(base['features']);plan.limits=json.dumps(base['limits'])
        plan.price_minor=0;plan.period_days=30;managed(plan)
    for name in subscription_names():
        sub=frappe.get_doc('IL Subscription',name)
        if not sub.base_features:sub.base_features=plan.features
        if not sub.base_limits:sub.base_limits=plan.limits
        if not sub.ai_mode:sub.ai_mode='Individual'
        # Free base access is resolved independently. Preserve historic paid state/dates.
        managed(sub)
    for dt, columns in {'IL AI Allocation':['user','period'], 'IL Premium Receipt':['tenant_id','paid_at'],
                        'IL Policy Delivery':['status','next_attempt']}.items():
        frappe.db.add_index(dt,columns)


def subscription_names():
    after=''
    while True:
        names=frappe.get_all('IL Subscription',filters={'name':['>',after]},pluck='name',order_by='name asc',limit_page_length=100)
        if not names:return
        yield from names
        after=names[-1]
