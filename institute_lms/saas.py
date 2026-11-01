"""Site-local plan resolver. Only signed control-plane snapshots set tenant policy."""
import json
import hmac
from datetime import datetime
import frappe
from frappe.utils import now_datetime, get_datetime
from .saas_rules import resolve, effective_state, check_capacity, verify_manifest

def managed(doc):
    doc.flags.saas_service = True
    return doc.save(ignore_permissions=True)

def audit(action, reference, detail):
    return managed(frappe.get_doc({'doctype':'IL SaaS Audit', 'action':action,
        'reference':reference, 'actor':frappe.session.user, 'details':str(detail)[:4000]}))

def state(lock=False):
    tenant = frappe.conf.get('il_tenant_id')
    if not tenant: frappe.throw('SaaS tenant must be provisioned before use', frappe.PermissionError)
    name = frappe.db.get_value('IL Subscription', {'tenant_id':tenant}, 'name')
    if not name: frappe.throw('Subscription not configured', frappe.PermissionError)
    if lock: frappe.db.sql('SELECT name FROM `tabIL Subscription` WHERE name=%s FOR UPDATE', (name,))
    return frappe.get_doc('IL Subscription', name, for_update=lock)

def resolved(doc=None):
    from .full_rules import final_policy
    d = doc or state()
    result=final_policy(d.as_dict())
    result['features'].update({key:False for key in result['features'] if key.startswith('ai.')})
    result['limits']['ai_credits']=0
    return result


def require(feature='lms'):
    from .commercial import feature_policy
    r = feature_policy() or resolved()
    if not r['available'] or not r['features'].get(feature):
        frappe.throw('Subscription or feature unavailable', frappe.PermissionError)
    return r

def quota(resource, current, requested=1):
    if resource in ('students','teachers','classes','courses'):
        return current()+requested
    from .account_storage import configured,capacity
    if resource=='storage_bytes' and configured():return capacity(current,requested)
    # Preserve configured infrastructure limits; they do not set subscription prices.
    d=state(lock=True)
    r=resolved(d)
    try:return check_capacity(current(),requested,r['limits'][resource])
    except (ValueError,KeyError) as e:frappe.throw(str(e))

@frappe.whitelist()
def status():
    if frappe.session.user == 'Guest': frappe.throw('Sign in required', frappe.AuthenticationError)
    from .account_billing import policy
    return policy()

@frappe.whitelist(allow_guest=True, methods=['POST'])
def apply_manifest(payload, signature):
    """Authenticated by a site-specific signing key, never the institute code."""
    if not isinstance(payload, str) or len(payload) > 30000: frappe.throw('Invalid manifest')
    data = json.loads(payload)
    tenant = frappe.conf.get('il_tenant_id')
    if frappe.conf.get('il_control_plane') or not tenant: frappe.throw('Tenant endpoint unavailable', frappe.PermissionError)
    from .saas_rules import sign
    key=frappe.conf.get('il_control_plane_key')
    if not isinstance(key,str) or len(key)<32 or not hmac.compare_digest(sign(data,key),str(signature)):
        frappe.throw('Invalid control-plane signature',frappe.PermissionError)
    # Serializes first application too; institute exists before provisioning handoff.
    from .api import institute
    inst = institute()
    frappe.db.sql('SELECT name FROM `tabIL Institute` WHERE name=%s FOR UPDATE', (inst.name,))
    name = frappe.db.get_value('IL Subscription', {'tenant_id':tenant}, 'name')
    d = frappe.get_doc('IL Subscription', name, for_update=True) if name else frappe.get_doc({'doctype':'IL Subscription','tenant_id':tenant})
    try: verify_manifest(data, signature, frappe.conf.get('il_control_plane_key'), tenant,
                         frappe.local.site, int(d.revision or 0), datetime.utcnow())
    except (ValueError, KeyError, TypeError) as e: frappe.throw(str(e), frappe.PermissionError)
    if data['plan'] not in ('STARTER','PREMIUM AI','CUSTOM'): frappe.throw('Unknown plan')
    previous_end=str(d.ends_at)
    for key in ('plan','state','starts_at','ends_at','grace_until','lease_until','revision','enabled'):
        d.set(key, data.get(key))
    d.features=json.dumps(data['features']); d.limits=json.dumps(data['limits']); d.overrides='{}'
    d.support_tier=data.get('support_tier','standard')
    d.base_features=json.dumps(data.get('base_features') or {})
    d.base_limits=json.dumps(data.get('base_limits') or {})
    managed(d)
    audit('Apply manifest', tenant, 'revision '+str(data['revision']))
    if data['state']=='active' and previous_end!=str(d.ends_at):
        from .notification_service import emit
        for member in frappe.get_all('IL Member',filters={'institute':inst.name,'role':'Admin','active':1},pluck='name'):
            emit(inst.name,member,'subscription.renewed','renewed:'+str(d.ends_at),'Organization subscription renewed')
    from .subscription_notices import apply
    apply(inst.name,data.get('notices',[]))
    return {'applied':True, 'revision':d.revision}

def current_count(doctype, condition='1=1', values=()):
    # Trusted internal table/condition only. Locking reads avoid old RR snapshots.
    if doctype not in ('IL Member','IL Classroom','LMS Course'): raise ValueError('Invalid counter')
    return len(frappe.db.sql('SELECT name FROM `tab'+doctype+'` WHERE '+condition+' FOR UPDATE', values))

def enforce_member(doc, method=None):
    if not doc.active: return
    previous = doc.get_doc_before_save()
    if previous and previous.active and previous.role == doc.role: return
    # Trusted bench provisioning grants the first named admin, not metered seats.
    if doc.role not in ('Student','Teacher'): return
    from .api import institute
    if doc.institute != institute().name: frappe.throw('Foreign institute', frappe.PermissionError)
    quota('students' if doc.role=='Student' else 'teachers',
          lambda: current_count('IL Member', 'role=%s AND active=1 AND name!=%s', (doc.role,doc.name or '')))

def enforce_class(doc, method=None):
    previous=doc.get_doc_before_save()
    if doc.active and (not previous or not previous.active):
        quota('classes', lambda: current_count('IL Classroom', 'active=1 AND name!=%s', (doc.name or '',)))

def enforce_course(doc, method=None):
    if doc.is_new(): quota('courses', lambda: current_count('LMS Course'))

def consume_ai(quantity, reference):
    """Internal RUN 2 accounting boundary; never trust a client-reported amount."""
    require('ai.assistant')
    from .usage import consume
    return consume('ai_credits', quantity, reference)

def guard_request():
    """Run after Frappe authentication; configuration/recovery remains reachable."""
    if frappe.conf.get('il_control_plane'):return
    path=frappe.local.request.path
    method=frappe.form_dict.get('cmd') or (path.split('/method/',1)[1].rstrip('/') if '/method/' in path else '')
    module=method.split('.')[1] if method.startswith('institute_lms.') else ''
    from .wallet import admin_actor
    if method.startswith('institute_lms.') and admin_actor():return  # Owner APIs enforce their own authorization.
    if module=='workspace':return  # Actor/feature checks inside workspace also check the owner's subscription.
    from .commercial import request_policy
    if request_policy(method,module):return
    if module in ('commercial','provider_bridge'):return  # Every commercial endpoint resolves its own actor and record scope.
    if module in ('health','release'):return  # Each facade method performs its own authorization.
    if method=='institute_lms.ai.archive_conversation':return  # ownership-only privacy operation
    if module in ('commerce_events','mobile_auth','saas','platform','subscription_payments','registration','portal_policy',
                  'portal_session','cybersource','account_billing','billing_bridge','profiles','private_contact','mobile_verification','contact','devices','notification_service'):
        return
    if module in ('payments_lk','payments','lectures') and method.endswith('.notify'):return
    if method=='institute_lms.live_classes.webhook':return
    if method in ('login','logout') or method.startswith('frappe.integrations.oauth2_logins.') or 'reset_password' in method or 'update_password' in method:return
    if frappe.session.user=='Administrator' or 'System Manager' in frappe.get_roles():return
    if module in ('youtube','calendar_sync'):
        integration('youtube' if module=='youtube' else 'calendar')
    if module or method.startswith('lms.') or path.startswith('/'+str(frappe.conf.get('lms_path','lms')).strip('/')):
        require('lms')

def integration(feature):
    require('integrations.'+feature)
