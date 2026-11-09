"""Owner visibility and retry for the existing signed hosted-site policy transport."""
from datetime import timedelta
import frappe
from frappe.utils import now_datetime,get_datetime

def blockers(org):
    result=[]
    if org.provisioning_state!='ready':result.append('Website setup has not been marked ready.')
    if org.site_hostname not in (frappe.conf.get('il_policy_delivery_hosts') or []):result.append('The hosting operator must enable delivery to this website.')
    key=(frappe.conf.get('il_tenant_signing_keys') or {}).get(org.name)
    if not isinstance(key,str) or len(key)<32:result.append('The hosting operator must configure the secure connection to this website.')
    return result

def delivery_label(row,now):
    if not row:return 'No confirmation yet'
    if row.get('status')=='Failed':return 'Delivery needs attention'
    if row.get('status')=='Pending':return 'Waiting for delivery'
    if row.get('status')=='Delivered' and row.get('acknowledged_at'):
        # Acknowledgement is historical; it is not a live uptime check.
        if get_datetime(row['acknowledged_at'])+timedelta(hours=24)>now:return 'Delivery confirmed'
        return 'Confirmation is out of date'
    return 'No confirmation yet'

@frappe.whitelist(methods=['GET'])
def listing(page=0):
    from .platform import owner
    owner()
    from .pricing_rules import integer
    page=integer(page,'Page',10000)
    rows=frappe.get_all('IL Organization',fields=['name','title','site_hostname','provisioning_state','enabled'],order_by='creation desc',limit_start=page*30,limit_page_length=31)
    result=[]
    for org in rows[:30]:
        delivery=frappe.db.get_value('IL Policy Delivery',{'organization':org.name},['status','revision','acknowledged_at','next_attempt'],as_dict=True)
        missing=blockers(org)
        result.append(dict(name=org.name,title=org.title,website=org.site_hostname,setup_ready=org.provisioning_state=='ready',enabled=bool(org.enabled),
            status=delivery_label(delivery,now_datetime()),revision=int((delivery or {}).get('revision') or 0),last_confirmed=(delivery or {}).get('acknowledged_at'),
            next_attempt=(delivery or {}).get('next_attempt'),blockers=missing,can_retry=not missing))
    return dict(sites=result,page=page,has_next=len(rows)>30)

@frappe.whitelist(methods=['POST'])
def retry(tenant,reason):
    from .platform import owner,organization
    owner();org=organization(tenant)
    if not isinstance(reason,str) or not 10<=len(reason.strip())<=1000:frappe.throw('Enter a reason of at least 10 characters.')
    missing=blockers(org)
    if missing:frappe.throw(' '.join(missing))
    # Lock the organization to serialize a first delivery row and repeat clicks.
    frappe.db.sql('SELECT name FROM `tabIL Organization` WHERE name=%s FOR UPDATE',(org.name,))
    name=frappe.db.get_value('IL Policy Delivery',{'organization':org.name},'name')
    doc=frappe.get_doc('IL Policy Delivery',name,for_update=True) if name else frappe.get_doc(dict(doctype='IL Policy Delivery',organization=org.name))
    if name and doc.status=='Pending':return dict(queued=True,message='An update is already waiting for delivery. Refresh to check confirmation.')
    doc.status='Pending';doc.next_attempt=now_datetime();doc.error_code=None
    from .saas import managed,audit
    managed(doc);audit('Retry hosted site policy',org.name,reason.strip())
    return dict(queued=True,message='Update queued. The background service will deliver it; refresh to check confirmation. This does not confirm that it is active yet.')

@frappe.whitelist(methods=['GET'])
def organization_details(tenant):
    from .platform import owner,organization
    owner();org=organization(tenant)
    result={key:org.get(key) for key in ('name','title','site_hostname','institute_code','admin_contact','enabled','custom_domain','plan','provisioning_state')}
    result['subscription']=frappe.db.get_value('IL Subscription',{'tenant_id':org.name},['state','ends_at','limits','overrides'],as_dict=True)
    return result
