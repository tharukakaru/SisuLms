"""Pure SaaS policy and transport rules. No provider or database side effects."""
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta

CORE = ('lms', 'integrations.email', 'integrations.sms', 'integrations.whatsapp',
        'integrations.push', 'integrations.youtube', 'integrations.calendar', 'branding')
AI = ('ai.assistant', 'ai.rag', 'ai.summaries', 'ai.notes', 'ai.flashcards',
      'ai.quiz', 'ai.questions', 'ai.assignments', 'ai.search', 'ai.recommendations',
      'ai.teacher', 'ai.analytics')
FEATURES = CORE + AI + ('custom_domain',)
LIMITS = ('students', 'teachers', 'storage_bytes', 'ai_credits', 'classes', 'courses')
STATES = ('trial', 'active', 'grace', 'past_due', 'suspended', 'cancelled', 'expired')

def object_value(value):
    if isinstance(value, str):
        if len(value) > 20000: raise ValueError('Policy too large')
        value = json.loads(value)
    if not isinstance(value, dict): raise ValueError('Policy must be an object')
    return value

def policy(features, limits):
    features, limits = object_value(features), object_value(limits)
    if set(features) - set(FEATURES) or any(type(v) is not bool for v in features.values()):
        raise ValueError('Unknown feature or non-boolean feature value')
    if set(limits) - set(LIMITS) or any(type(v) is not int or not 0 <= v <= 10**15 for v in limits.values()):
        raise ValueError('Limits must be nonnegative integers; zero denies allocation')
    return dict(features), dict(limits)

def resolve(features, limits, overrides=None):
    features, limits = policy(features, limits)
    extra = object_value(overrides or {})
    if set(extra) - {'features', 'limits', 'support_tier'}: raise ValueError('Unknown override')
    ef, el = policy(extra.get('features', {}), extra.get('limits', {}))
    features.update(ef); limits.update(el)
    tier = extra.get('support_tier', 'standard')
    if not isinstance(tier, str) or not re.fullmatch(r'[a-zA-Z0-9 _-]{1,40}', tier): raise ValueError('Invalid support tier')
    return {'features': {k: features.get(k, False) for k in FEATURES},
            'limits': {k: limits.get(k, 0) for k in LIMITS}, 'support_tier': tier}

def dt(value):
    return datetime.fromisoformat(str(value).replace('Z', '+00:00')).replace(tzinfo=None) if value else None

def effective_state(state, ends_at, grace_until=None, now=None):
    if state not in STATES: raise ValueError('Invalid subscription state')
    now = now or datetime.utcnow()
    if state in ('suspended', 'cancelled', 'expired', 'past_due'): return state
    end, grace = dt(ends_at), dt(grace_until)
    if state == 'grace': return 'grace' if grace and now < grace else 'expired'
    if not end: return 'expired'
    if now < end: return state
    return 'grace' if grace and now < grace else 'expired'

def remaining(used, limit): return max(0, int(limit) - int(used))

def check_capacity(used, requested, limit):
    if type(requested) is not int or requested < 0: raise ValueError('Invalid usage quantity')
    if int(used) + requested > int(limit): raise ValueError('Plan limit exceeded')
    return int(used) + requested

def hostname(value):
    value = str(value).lower().strip()
    if len(value) > 253 or '.' not in value or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', p) for p in value.split('.')):
        raise ValueError('Use a DNS hostname without scheme, port or path')
    return value

def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
def sign(value, key): return hmac.new(key.encode(), canonical(value).encode(), hashlib.sha256).hexdigest()
def verify_manifest(value, signature, key, tenant, site, revision, now=None):
    now = now or datetime.utcnow()
    if not isinstance(key, str) or len(key) < 32: raise ValueError('Control-plane key not configured')
    if not hmac.compare_digest(sign(value, key), str(signature)): raise ValueError('Invalid control-plane signature')
    if value.get('tenant_id') != tenant or value.get('site_hostname') != site: raise ValueError('Manifest belongs to another site')
    if type(value.get('revision')) is not int or value['revision'] <= revision: raise ValueError('Stale manifest')
    issued, lease = dt(value.get('issued_at')), dt(value.get('lease_until'))
    if not issued or not lease or abs((now-issued).total_seconds()) > 300 or not now < lease <= now+timedelta(hours=24):
        raise ValueError('Manifest expired or lease too long')
    resolve(value['features'], value['limits'], {'support_tier':value.get('support_tier','standard')})
    if 'base_features' in value or 'base_limits' in value:
        resolve(value.get('base_features',{}), value.get('base_limits',{}))
    if value.get('state') not in STATES or type(value.get('enabled')) is not bool: raise ValueError('Invalid manifest state')
    return value

def notification_key(event, recipient):
    return hashlib.sha256((event + ':' + recipient).encode()).hexdigest()

def transition_payment(old, incoming):
    if incoming not in ('pending','succeeded','failed','cancelled'): raise ValueError('Invalid payment state')
    # Verified success wins over reordered failure/cancel notifications.
    if old == 'succeeded': return old
    return incoming
