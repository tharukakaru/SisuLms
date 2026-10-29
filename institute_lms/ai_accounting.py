"""Request-credit reservations plus real provider usage, with no blind retries.

Credits are configurable flat request units, not a currency/token conversion.
Unknown provider outcomes retain their reservation for operator reconciliation.
"""
import json,re,time
from contextvars import ContextVar
import frappe
from frappe.utils import now_datetime
from .saas import managed,state
from .usage import consume,period
from .ai_rules import fingerprint,tokens,estimate

ACTIVE=ContextVar('sisu_ai_usage',default=None)
def save(doc):doc.flags.ai_service=True;return doc.save(ignore_permissions=True)
def started():
    current=ACTIVE.get()
    if current:
        current['started']=True;current['sequence']=current.get('sequence',0)+1
        return current.get('request_id','ai')+'-'+str(current['sequence'])
def receipt(response,model,operation):
    current=ACTIVE.get()
    if not current:return
    usage=tokens(response);model=response.get('model') or model
    current['receipts'].append(dict(model=model,operation=operation,request_id=response.get('_request_id') or response.get('id',''),**usage))
def rate_limit(user,institute):
    from .ai_provider import settings
    d=settings();now=int(time.time())
    checks=[('minute:'+user+':'+str(now//60),6,120),('user:'+user+':'+str(now//86400),max(1,min(int(d.user_daily_limit or 50),1000)),172800),('site:'+str(now//86400),max(1,min(int(d.site_daily_limit or 500),10000)),172800)]
    with frappe.cache.lock('il_ai_limits',timeout=5):
        for key,n,ttl in checks:
            if int(frappe.cache.get_value('il_ai:'+key) or 0)>=n:frappe.throw('AI request rate limit reached')
        for key,n,ttl in checks:frappe.cache.set_value('il_ai:'+key,int(frappe.cache.get_value('il_ai:'+key) or 0)+1,expires_in_sec=ttl)

def execute(feature,request_id,payload,context,operation,kind='generation',units_multiplier=1):
    from .saas import require
    from .ai_provider import config,ProviderError
    require(feature);settings,_=config()
    if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9_:-]{8,160}',request_id):frappe.throw('A stable request_id of 8–160 safe characters is required')
    inst,member,room=context;key=fingerprint([frappe.local.site,frappe.session.user,feature,request_id]);digest=fingerprint(payload)
    with frappe.cache.lock('il_ai_request:'+key,timeout=600,blocking_timeout=1):
        sub=state(lock=True)
        rows=frappe.db.sql('SELECT name FROM `tabIL AI Usage` WHERE request_key=%s FOR UPDATE',(key,))
        if rows:
            old=frappe.get_doc('IL AI Usage',rows[0][0],for_update=True)
            if old.payload_hash!=digest:frappe.throw('request_id was already used for different input')
            if old.state=='Succeeded' and old.result:return json.loads(old.result)
            frappe.throw('Request '+old.state+'. Do not retry ambiguous provider work with a new identifier; reconcile first.')
        rate_limit(frappe.session.user,inst.name)
        costs=json.loads(settings.feature_credits or '{}');units=costs.get(feature,1)
        if type(units) is not int or not 1<=units<=100:frappe.throw('Invalid AI credit configuration')
        if type(units_multiplier) is not int or not 1<=units_multiplier<=5:frappe.throw('Invalid AI job budget')
        units *= units_multiplier
        rates=json.loads(settings.model_rates or '{}')
        # Validate configured estimates before any provider work.
        for rate in rates.values():estimate(dict(input_tokens=0,cached_tokens=0,output_tokens=0),rate)
        from .ai_credits import enforce
        enforce(frappe.session.user, units)
        consume('ai_credits',units,'ai:'+key)
        d=save(frappe.get_doc({'doctype':'IL AI Usage','request_key':key,'payload_hash':digest,'institute':inst.name,
            'user':frappe.session.user,'classroom':room.name if room else None,'subscription':sub.name,'feature':feature,
            'request_type':kind,'period':period('ai_credits'),'model':settings.model,'state':'Running',
            'reserved_units':units,'charged_units':units,'rate_snapshot':json.dumps(rates)}))
        frappe.db.commit()  # quota debit and idempotency marker precede all provider work
        current={'started':False,'receipts':[],'request_id':key};token=ACTIVE.set(current)
        try:
            result=operation();d.state='Succeeded';d.result=json.dumps(result,ensure_ascii=False)
            if len(d.result)>100000:raise ValueError('AI result too large')
        except Exception as error:
            frappe.db.rollback();d.result=None
            d.state='Review' if isinstance(error,ProviderError) else 'Failed'
            d.error_code=str(error)[:100] if isinstance(error,ProviderError) else 'request_failed_or_blocked'
            if not current['started']:
                state(lock=True)
                managed(frappe.get_doc({'doctype':'IL Usage Entry','event_key':fingerprint(['release',key]),'tenant_id':sub.tenant_id,
                    'resource':'ai_credits','period':d.period,'quantity':-units,'reference':'ai-release:'+key}))
                d.charged_units=0;d.state='Released'
            finish(d,current,rates);frappe.db.commit()
            frappe.throw('AI request did not complete ('+d.state+'). Reference: '+d.name)
        finally:ACTIVE.reset(token)
        finish(d,current,rates);frappe.db.commit()
        return result

def finish(d,current,rates):
    receipts=current['receipts'];d.provider_requests=json.dumps(receipts);d.usage_reported=int(any(r['usage_reported'] for r in receipts))
    for k in ('input_tokens','cached_tokens','output_tokens','total_tokens'):setattr(d,k,sum(r[k] for r in receipts))
    known=[(estimate(r,rates.get(r['model'])),rates.get(r['model'],{}).get('currency')) for r in receipts if r['usage_reported']]
    if known and all(v is not None and c for v,c in known) and len({c for _,c in known})==1:
        d.estimated_cost=sum(v for v,_ in known);d.cost_currency=known[0][1]
    d.completed_at=now_datetime();save(d)

@frappe.whitelist(methods=['POST'])
def reconcile(request,decision,reason):
    """Owner-only resolution after external provider reconciliation; no blind refund."""
    from .wallet import owner
    from .saas import audit
    owner()
    if decision not in ('release','retain') or not isinstance(reason,str) or not 10<=len(reason.strip())<=1000:
        frappe.throw('Recorded provider reconciliation and decision required')
    state(lock=True)
    d=frappe.get_doc('IL AI Usage',request,for_update=True)
    if d.state not in ('Review','Running') or (now_datetime()-d.modified).total_seconds()<600:
        frappe.throw('Only unresolved requests older than ten minutes may be reconciled')
    if decision=='release' and d.charged_units:
        managed(frappe.get_doc({'doctype':'IL Usage Entry','event_key':fingerprint(['reconcile-release',d.request_key]),
            'tenant_id':frappe.conf.il_tenant_id,'resource':'ai_credits','period':d.period,
            'quantity':-int(d.charged_units),'reference':'ai-reconcile:'+d.request_key}))
        d.charged_units=0
    d.state='Released' if decision=='release' else 'Failed';d.completed_at=now_datetime();save(d)
    audit('AI usage reconciliation',d.name,decision+': '+reason)
    return {'state':d.state,'charged_units':d.charged_units}
