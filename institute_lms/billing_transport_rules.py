"""Domain-separated, short-lived billing messages. No credentials in payloads."""
import hashlib,hmac,json,re
from .saas_rules import canonical
PURPOSE='sisu.usage-billing.v1'
def sign_message(payload,key):
    if not isinstance(key,str) or len(key)<32:raise ValueError('Billing key not configured')
    return hmac.new(key.encode(),(PURPOSE+'\n'+canonical(payload)).encode(),hashlib.sha256).hexdigest()
def verify_message(payload,signature,key,tenant,site,now):
    if not isinstance(payload,dict) or len(canonical(payload))>32000:raise ValueError('Invalid billing payload')
    if not hmac.compare_digest(sign_message(payload,key),str(signature)):raise ValueError('Invalid billing signature')
    if payload.get('tenant_id')!=tenant or payload.get('site_hostname')!=site:raise ValueError('Wrong billing tenant')
    if type(payload.get('issued_at')) is not int or abs(now-payload['issued_at'])>120:raise ValueError('Expired billing message')
    if not re.fullmatch('[a-f0-9]{32}',str(payload.get('request_id',''))):raise ValueError('Invalid request identity')
    if payload.get('action') not in ('list','settle','reply'):raise ValueError('Invalid billing action')
    return payload
SNAPSHOT=('name','subscription','period_start','period_end','due_at','plan','unit_rate','quantity','amount_lkr','issued_at')
def fingerprint(doc):
    return hashlib.sha256(canonical({k:str(doc.get(k)) for k in SNAPSHOT}).encode()).hexdigest()
