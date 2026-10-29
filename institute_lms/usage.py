"""Atomic period usage ledger. Counters are derived under the subscription row lock."""
import hashlib
import frappe
from frappe.utils import now_datetime
from .saas import state, resolved, managed
from .saas_rules import check_capacity, remaining

def period(resource):
    return now_datetime().strftime('%Y-%m') if resource=='ai_credits' else 'lifetime'

def used(resource, bucket=None):
    if resource in ('students','teachers'):
        return frappe.db.count('IL Member',{'active':1,'role':'Student' if resource=='students' else 'Teacher'})
    if resource=='classes':return frappe.db.count('IL Classroom',{'active':1})
    if resource=='courses':return frappe.db.count('LMS Course')
    if resource=='storage_bytes':
        return int(frappe.db.sql('SELECT COALESCE(SUM(file_size),0) FROM `tabFile` WHERE is_folder=0 FOR UPDATE')[0][0]) + int(frappe.db.sql("SELECT COALESCE(SUM(bytes),0) FROM `tabIL Stored Object` WHERE (file IS NULL OR file='') AND status!='PURGED' FOR UPDATE")[0][0])
    return int(frappe.db.sql('SELECT COALESCE(SUM(quantity),0) FROM `tabIL Usage Entry` WHERE resource=%s AND period=%s FOR UPDATE',
                            (resource,bucket or period(resource)))[0][0])

def consume(resource, quantity, reference):
    if resource!='ai_credits' or not isinstance(reference,str) or not 1<=len(reference)<=200:frappe.throw('Invalid usage reference')
    d=state(lock=True);r=resolved(d)
    if not r['available']:frappe.throw('Subscription unavailable',frappe.PermissionError)
    bucket=period(resource);key=hashlib.sha256((bucket+':'+resource+':'+reference).encode()).hexdigest()
    rows=frappe.db.sql('SELECT name,quantity FROM `tabIL Usage Entry` WHERE event_key=%s FOR UPDATE',(key,),as_dict=True)
    old=rows[0] if rows else None
    if old:
        if old.quantity!=quantity:frappe.throw('Usage reference reused with a different amount')
        return old.name
    try:check_capacity(used(resource,bucket),quantity,r['limits'][resource])
    except ValueError as e:frappe.throw(str(e))
    return managed(frappe.get_doc({'doctype':'IL Usage Entry','event_key':key,'resource':resource,
        'period':bucket,'quantity':quantity,'reference':reference,'tenant_id':d.tenant_id})).name

@frappe.whitelist()
def summary():
    if frappe.session.user=='Guest':frappe.throw('Sign in required',frappe.AuthenticationError)
    from .api import identity,require_role
    _,member=identity();require_role(member,'Admin')
    r=resolved();rows={}
    for key,limit in r['limits'].items():
        n=used(key);rows[key]={'used':n,'limit':limit,'remaining':remaining(n,limit),'period':period(key)}
    return {'usage':rows,'renews_at':r['ends_at'],'ai_reset':'First day of next calendar month (site time)'}
