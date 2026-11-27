"""Site-local plan catalogue. All changes require platform owner authority."""
import json
import hashlib
import frappe
from .plan_catalog_rules import defaults,validate,EDITABLE_FEATURES,FEATURE_LABELS
DT='IL Plan Catalog'
def current():
    from .plan_catalog_source import read_source
    shared=read_source()
    if shared is not None:return shared
    raw=frappe.db.get_value(DT,'current',['payload','revision'],as_dict=True)
    return dict(plans=validate(json.loads(raw.payload)) if raw else defaults(),revision=int(raw.revision) if raw else 0)
def plan(name):return current()['plans'][name]
def plan_features(name):
    from .commercial_rules import plan_features as baseline
    features=baseline(name)
    features.update(plan(name)['features'])
    return features
@frappe.whitelist(methods=['POST'])
def admin_get():
    from .account_billing import require_owner
    require_owner()
    from .plan_catalog_source import require_source_writer
    require_source_writer()
    return dict(**current(),editable_features=list(EDITABLE_FEATURES),feature_labels=FEATURE_LABELS)
@frappe.whitelist(methods=['POST'])
def publish(plans,revision,reason):
    from .account_billing import require_owner
    require_owner()
    from .plan_catalog_source import require_source_writer
    require_source_writer()
    if not isinstance(reason,str) or not 10<=len(reason.strip())<=1000:frappe.throw('Enter a change reason of 10–1000 characters')
    try:clean=validate(json.loads(plans) if isinstance(plans,str) else plans)
    except (ValueError,TypeError) as e:frappe.throw(str(e))
    # Serialize even the initial insert, and reject stale editor submissions.
    frappe.db.sql('SELECT name FROM `tabDocType` WHERE name=%s FOR UPDATE',(DT,))
    before=current()
    if str(revision)!=str(before['revision']):frappe.throw('Plans changed since you opened this page. Reload before editing.')
    doc=frappe.get_doc(DT,'current') if before['revision'] else frappe.get_doc(dict(doctype=DT,name='current'))
    doc.payload=json.dumps(clean,sort_keys=True);doc.revision=before['revision']+1
    doc.change_reason=reason.strip();doc.flags.plan_catalog_service=True
    if before['revision']:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    from .saas import audit
    audit('Publish plan catalog',str(doc.revision),json.dumps(dict(reason=reason.strip(),previous_revision=before['revision'],sha256=hashlib.sha256(doc.payload.encode()).hexdigest())))
    return dict(plans=clean,revision=doc.revision,editable_features=list(EDITABLE_FEATURES),feature_labels=FEATURE_LABELS)

@frappe.whitelist(allow_guest=True, methods=['GET'])
def public_catalog():
    """Published product information only; no account, audit or billing records."""
    from .provider_usage_rules import PLANS
    value=current()
    return dict(revision=value['revision'],currency='LKR',plans={name:dict(**p,active_student_lkr=PLANS[name]['active_student_lkr']) for name,p in value['plans'].items()})
