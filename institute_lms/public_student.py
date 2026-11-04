"""Student-only cross-workspace views. Revalidate membership for every scoped operation."""
import json
import inspect
from contextlib import contextmanager
import frappe

@contextmanager
def workspace(institute):
    from .campus_context import membership
    member=membership(institute)
    if member.role!='Student':frappe.throw('Student membership required.',frappe.PermissionError)
    previous=getattr(frappe.local,'student_request_institute',None)
    frappe.local.student_request_institute=institute
    try:yield member
    finally:frappe.local.student_request_institute=previous

def memberships():
    from .campus_context import require_user
    user=require_user()
    return frappe.get_all('IL Member',filters={'user':user,'active':1,'role':'Student'},pluck='institute',limit_page_length=100)

@frappe.whitelist(methods=['GET'])
def billing():
    from .api import invoices
    from .commercial import slips
    result={'invoices':[],'rooms':[],'slips':[]}
    for inst in memberships():
        with workspace(inst):
            rows=invoices();result['invoices']+=rows;result['slips']+=slips()
            names=list({r.classroom for r in rows})
            result['rooms']+=frappe.get_all('IL Classroom',filters={'institute':inst,'name':['in',names or ['__none__']]},fields=['name','title','fee','programme'])
    return result

@frappe.whitelist(methods=['GET'])
def classes(page=0,profile=''):
    from .profiles import followed_classes
    from .learning_spaces import classes as scoped_classes
    rows={r['name']:dict(r,state='available',teacher_name=r.get('provider_name',''),requires_registration=True) for r in followed_classes(page=page)}
    joined=memberships()
    for row in rows.values():
        inst=frappe.db.get_value('IL Classroom',row['name'],'institute')
        if inst in joined:row.update(requires_registration=False,institute=inst)
    for inst in joined:
        with workspace(inst):
            for r in scoped_classes(page=page)['classes']:rows[r['name']]=dict(r,institute=inst)
    if profile:
        rows={name:row for name,row in rows.items() if frappe.db.get_value('IL Classroom',name,'public_provider')==profile}
    return {'classes':list(rows.values()),'has_more':len(rows)>=24}

@frappe.whitelist(methods=['GET'])
def choices():
    from .profiles import signed_in
    from .learning_spaces import following
    signed_in()
    return frappe.get_all('IL Public Profile',filters={'name':['in',list(following()) or ['__none__']],'status':'Verified'},fields=['name','display_name','kind'],order_by='display_name asc')

@frappe.whitelist(methods=['GET'])
def schedule(page=0,starts_on=None,ends_on=None):
    from .api import schedule as scoped_schedule
    rows=[]
    for inst in memberships():
        with workspace(inst):
            rows.extend(dict(row,institute=inst) for row in scoped_schedule(page=page,starts_on=starts_on,ends_on=ends_on))
    return sorted(rows,key=lambda row:str(row['starts_at']),reverse=True)

@frappe.whitelist(methods=['POST'])
def action(module,method,args=None):
    from . import class_keys,catalog,commercial,teaching
    allowed={('class_keys','key_status'):class_keys.key_status,('class_keys','bank_details'):class_keys.bank_details,
      ('class_keys','redeem'):class_keys.redeem,('class_keys','resend'):class_keys.resend,
      ('catalog','join_class'):catalog.join_class,('teaching','enroll_programme'):teaching.enroll_programme,
      ('commercial','submit_slip'):commercial.submit_slip}
    fn=allowed.get((module,method))
    if not fn:frappe.throw('Unsupported student action.',frappe.PermissionError)
    args=json.loads(args) if isinstance(args,str) else args or {}
    if not isinstance(args,dict):frappe.throw('Invalid request.')
    if args.get('classroom'):inst=frappe.db.get_value('IL Classroom',args['classroom'],'institute')
    elif args.get('invoice'):inst=frappe.db.get_value('IL Invoice',args['invoice'],'institute')
    elif args.get('programme'):inst=frappe.db.get_value('IL Programme',args['programme'],'institute')
    else:inst=None
    # Match Frappe's whitelisted argument filtering: UI-only form properties
    # must not become unexpected Python keyword arguments.
    accepted=inspect.signature(fn).parameters
    with workspace(inst):return fn(**{key:value for key,value in args.items() if key in accepted})

@frappe.whitelist(methods=['POST'])
def upload_proof(invoice):
    from .commercial import upload_proof as upload
    inst=frappe.db.get_value('IL Invoice',invoice,'institute')
    with workspace(inst) as member:
        if not frappe.db.exists('IL Invoice',{'name':invoice,'student':member.name,'institute':inst}):frappe.throw('Payment unavailable.',frappe.PermissionError)
        return upload()


@frappe.whitelist(methods=['GET'])
def proof(name):
    from .commercial import proof as view
    inst=frappe.db.get_value('IL Bank Slip',name,'institute')
    with workspace(inst) as member:
        if not frappe.db.exists('IL Bank Slip',{'name':name,'student':member.name,'institute':inst}):frappe.throw('Proof unavailable.',frappe.PermissionError)
        return view(name)
