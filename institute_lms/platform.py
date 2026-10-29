"""Dedicated control-plane registry. Never opens another site's database."""
import json
import uuid
from datetime import timedelta, datetime
import frappe
from frappe.utils import now_datetime, get_datetime
from .saas import managed, audit
from .saas_rules import hostname, resolve, sign, policy, STATES

def control():
    if not frappe.conf.get('il_control_plane'): frappe.throw('Dedicated control-plane site required', frappe.PermissionError)

def owner():
    control()
    from .registration import require_owner
    require_owner()

def organization(name, administrator=False):
    control()
    d=frappe.get_doc('IL Organization', name)
    from .wallet import admin_actor
    if not admin_actor() and (not administrator or frappe.session.user=='Guest' or d.admin_contact != frappe.session.user):
        frappe.throw('Organization unavailable', frappe.PermissionError)
    if not frappe.db.get_value('User', frappe.session.user, 'enabled'): frappe.throw('Account disabled', frappe.PermissionError)
    return d

@frappe.whitelist(methods=['POST'])
def register(title, code, site_hostname, admin_contact, plan='STARTER'):
    owner()
    from .domain import institute_code
    code=institute_code(code); host=hostname(site_hostname)
    from .contact import email_address
    email=email_address(admin_contact)
    if plan != 'STARTER' or not 1<=len(str(title).strip())<=120: frappe.throw('Invalid organization')
    # Exact retries return the original; conflicting identities cannot be adopted.
    existing=frappe.db.get_value('IL Organization', {'site_hostname':host}, 'name')
    if existing:
        d=organization(existing)
        if (d.institute_code,d.admin_contact,d.title,d.plan)!=(code,email,title.strip(),plan): frappe.throw('Hostname already reserved with different details')
        return {'tenant_id':d.name,'existing':True}
    tenant='org-'+uuid.uuid4().hex
    if not frappe.db.exists('User',email):
        frappe.get_doc({'doctype':'User','email':email,'first_name':title.strip()[:100],
            'enabled':1,'user_type':'Website User','send_welcome_email':0}).insert(ignore_permissions=True)
    d=managed(frappe.get_doc({'doctype':'IL Organization','tenant_id':tenant,
        'title':title.strip(),'institute_code':code,'site_hostname':host,'admin_contact':email,
        'plan':plan,'enabled':1,'provisioning_state':'registered','revision':0}))
    p=frappe.get_doc('IL SaaS Plan', plan)
    managed(frappe.get_doc({'doctype':'IL Subscription','tenant_id':tenant,'plan':plan,
        'state':'active','enabled':1,'features':p.features,'limits':p.limits,'overrides':'{}',
        'base_features':p.features,'base_limits':p.limits}))
    job=managed(frappe.get_doc({'doctype':'IL Provisioning Job','organization':d.name,'status':'pending'}))
    audit('Register organization',d.name,'Provisioning job '+job.name)
    return {'tenant_id':d.name,'job':job.name,'existing':False}

@frappe.whitelist()
def organizations(page=0):
    owner()
    rows=frappe.get_all('IL Organization',fields=['name','title','institute_code','site_hostname','custom_domain','admin_contact','enabled','provisioning_state','plan','creation'],
                        order_by='creation desc',limit_start=max(0,min(int(page),10000))*50,limit_page_length=50)
    for row in rows:
        s=frappe.db.get_value('IL Subscription',{'tenant_id':row.name},['state','ends_at','limits','overrides'],as_dict=True)
        row['subscription']=s
    return rows

@frappe.whitelist(methods=['POST'])
def configure_plan(plan, features, limits, price_minor, period_days=30, reason=''):
    owner()
    if plan not in ('STARTER','PREMIUM AI','CUSTOM') or not str(reason).strip(): frappe.throw('Plan and audit reason required')
    f,l=policy(features,limits)
    from .pricing_rules import integer
    price=integer(price_minor,'Price'); days=integer(period_days,'Period days',366)
    if not days: frappe.throw('Positive billing period required')
    p=frappe.get_doc('IL SaaS Plan',plan);p.features=json.dumps(f);p.limits=json.dumps(l)
    p.price_minor=price;p.period_days=days;p.version=int(p.version or 0)+1;managed(p)
    audit('Configure plan',plan,reason)
    return {'version':p.version}

@frappe.whitelist(methods=['POST'])
def update_organization(tenant, enabled, reason, custom_domain=None):
    owner();d=organization(tenant)
    if type(enabled) is not bool or not str(reason).strip(): frappe.throw('Boolean status and reason required')
    s=frappe.get_doc('IL Subscription',frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name'),for_update=True)
    if custom_domain:
        if not resolve(s.features,s.limits,s.overrides)['features']['custom_domain']: frappe.throw('Custom domain not entitled')
        d.custom_domain=hostname(custom_domain)
    elif custom_domain is not None:d.custom_domain=None
    d.enabled=int(enabled);managed(d);s.enabled=int(enabled);managed(s)
    audit('Organization enabled' if enabled else 'Organization suspended',tenant,reason)
    return {'enabled':enabled,'requires_manifest_delivery':True}

@frappe.whitelist(methods=['POST'])
def override(tenant, values, reason):
    owner();organization(tenant)
    s=frappe.get_doc('IL Subscription',frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name'),for_update=True)
    if not str(reason).strip(): frappe.throw('An audit reason is required')
    values=json.loads(values) if isinstance(values,str) else values
    resolve(s.features,s.limits,values)
    s.overrides=json.dumps(values);managed(s);audit('Custom override',tenant,reason+' '+s.overrides)
    return {'saved':True,'requires_manifest_delivery':True}

@frappe.whitelist(methods=['POST'])
def trial(tenant, days, reason):
    owner();organization(tenant)
    from .pricing_rules import integer
    days=integer(days,'Trial days',30)
    if not days or not str(reason).strip():frappe.throw('Bounded trial and reason required')
    name=frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name')
    frappe.db.sql('SELECT name FROM `tabIL Subscription` WHERE name=%s FOR UPDATE',(name,))
    s=frappe.get_doc('IL Subscription',name,for_update=True)
    if s.trial_used or s.last_payment:frappe.throw('Trial already used or paid subscription exists')
    s.trial_used=1;s.state='trial';s.starts_at=datetime.utcnow();s.ends_at=datetime.utcnow()+timedelta(days=days);managed(s)
    audit('Grant bounded trial',tenant,reason)
    return {'ends_at':s.ends_at}

@frappe.whitelist(methods=['POST'])
def subscription_state(tenant, state, reason, grace_until=None):
    owner();organization(tenant)
    # Active is reserved for verified settlement. Trials have a separate bounded flow.
    if state not in ('grace','past_due','suspended','cancelled','expired') or not str(reason).strip(): frappe.throw('Invalid state change')
    s=frappe.get_doc('IL Subscription',frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name'),for_update=True)
    if state=='grace':
        end=get_datetime(grace_until)
        if not s.last_payment or not datetime.utcnow()<end<=datetime.utcnow()+timedelta(days=14):frappe.throw('Grace requires a settled subscription and at most 14 days')
        s.grace_until=end
    s.state=state;managed(s);audit('Subscription '+state,tenant,reason)
    return {'state':state,'requires_manifest_delivery':True}

@frappe.whitelist(methods=['POST'])
def manifest(tenant):
    owner();organization(tenant)
    return signed_policy(tenant)

def signed_policy(tenant):
    control()
    d=frappe.get_doc('IL Organization',tenant)
    frappe.db.sql('SELECT name FROM `tabIL Organization` WHERE name=%s FOR UPDATE',(d.name,));d=frappe.get_doc('IL Organization',d.name,for_update=True)
    s=frappe.get_doc('IL Subscription',frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name'),for_update=True)
    key=(frappe.conf.get('il_tenant_signing_keys') or {}).get(tenant)
    if not isinstance(key,str) or len(key)<32:frappe.throw('Operator must configure a tenant-specific signing key')
    r=resolve(s.features,s.limits,s.overrides);now=datetime.utcnow()
    data={'tenant_id':tenant,'site_hostname':d.site_hostname,'revision':int(d.revision or 0)+1,
          'plan':s.plan,'state':s.state,'enabled':bool(d.enabled and s.enabled),
          'features':r['features'],'limits':r['limits'],'support_tier':r['support_tier'],
          'base_features':json.loads(s.base_features or '{}'),'base_limits':json.loads(s.base_limits or '{}'),
          'starts_at':str(s.starts_at) if s.starts_at else None,'ends_at':str(s.ends_at) if s.ends_at else None,
          'grace_until':str(s.grace_until) if s.grace_until else None,
          'issued_at':str(now),'lease_until':str(now+timedelta(hours=24))}
    data['notices']=frappe.get_all('IL Subscription Notice',filters={'tenant_id':tenant,'acknowledged':0},fields=['name','event_key','event_type','body'],order_by='creation asc',limit_page_length=50)
    d.revision=data['revision'];managed(d);audit('Issue manifest',tenant,str(d.revision))
    return {'payload':json.dumps(data),'signature':sign(data,key)}

@frappe.whitelist()
def provisioning_spec(job):
    owner();j=frappe.get_doc('IL Provisioning Job',job);d=organization(j.organization)
    return {'job':j.name,'tenant_id':d.name,'site_hostname':d.site_hostname,'title':d.title,
            'code':d.institute_code,'admin_email':d.admin_contact,'apps':['lms','institute_lms'],
            'schema_version':1}

@frappe.whitelist(methods=['POST'])
def provisioning_result(job, status, reason):
    owner()
    if status not in ('running','ready','failed') or not str(reason).strip():frappe.throw('Status and reason required')
    j=frappe.get_doc('IL Provisioning Job',job);d=organization(j.organization)
    j.status=status;j.detail=str(reason)[:1000];managed(j);d.provisioning_state=status;managed(d)
    audit('Provisioning '+status,d.name,reason)
    return {'status':status}

@frappe.whitelist(methods=['POST'])
def invite_billing_contact(tenant):
    owner();d=organization(tenant)
    if not frappe.db.exists('Email Account',{'enable_outgoing':1}):frappe.throw('Configure outgoing email first')
    frappe.get_doc('User',d.admin_contact).reset_password(send_email=True)
    audit('Invite billing contact',tenant,'Password setup email queued')
    return {'queued':True}

@frappe.whitelist(methods=['POST'])
def reactivate(tenant,reason):
    owner();organization(tenant)
    s=frappe.get_doc('IL Subscription',frappe.db.get_value('IL Subscription',{'tenant_id':tenant},'name'),for_update=True)
    if not str(reason).strip() or s.state!='suspended' or not s.last_payment or not s.ends_at or get_datetime(s.ends_at)<=datetime.utcnow():
        frappe.throw('Only an unexpired previously settled subscription can be restored')
    if not frappe.db.exists('IL Payment Transaction',{'attempt':s.last_payment,'tenant_id':tenant}):frappe.throw('Verified settlement required')
    s.state='active';managed(s);audit('Restore settled subscription',tenant,reason)
    return {'state':s.state,'requires_manifest_delivery':True}
