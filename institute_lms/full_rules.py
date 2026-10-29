"""Pure final product policies; browser/mobile consume the resolved result."""
import calendar
import json
from datetime import datetime
from .saas_rules import AI, CORE, resolve, effective_state, dt

STARTER_LIMITS = dict(students=100, teachers=10, storage_bytes=1073741824,
                      ai_credits=0, classes=50, courses=50)

def starter_policy(limits=None):
    values = dict(STARTER_LIMITS)
    if limits is not None:
        values.update(limits)
    values['ai_credits'] = 0
    return resolve({k: True for k in CORE}, values)

def final_policy(record, now=None):
    now = now or datetime.utcnow()
    def value(key, default):
        raw=record.get(key)
        parsed=json.loads(raw) if isinstance(raw,str) else raw
        return parsed or default
    base = resolve(value('base_features', {k: True for k in CORE}), value('base_limits', STARTER_LIMITS))
    stored = resolve(record.get('features') or {}, record.get('limits') or {}, record.get('overrides') or {})
    state = effective_state(record.get('state') or 'expired', record.get('ends_at'), record.get('grace_until'), now)
    fresh = bool(record.get('lease_until') and dt(record['lease_until']) > now)
    enabled = bool(record.get('enabled') and fresh)
    premium = bool(enabled and record.get('plan') in ('PREMIUM AI', 'CUSTOM') and state in ('active', 'trial', 'grace')
                   and (not record.get('starts_at') or dt(record['starts_at']) <= now))
    result = stored if premium else base
    if not premium:
        result['features'].update({key: False for key in AI})
        result['limits']['ai_credits'] = 0
    result.update(plan='PREMIUM AI' if premium else 'STARTER', state=state if premium else 'active' if enabled else 'suspended',
                  premium_state=state, premium_active=premium, available=enabled,
                  organization_enabled=bool(record.get('enabled')), policy_current=fresh,
                  tenant_id=record.get('tenant_id'), starts_at=record.get('starts_at'), ends_at=record.get('ends_at'),
                  grace_until=record.get('grace_until'), lease_until=record.get('lease_until'), revision=record.get('revision', 0))
    return result

def month_end(start):
    value = dt(start)
    year, month = (value.year+1, 1) if value.month == 12 else (value.year, value.month+1)
    return value.replace(year=year, month=month, day=min(value.day, calendar.monthrange(year, month)[1]))

def credit_check(mode, allocated, user_used, organization_used, organization_limit, requested):
    if mode not in ('Individual', 'Shared') or type(requested) is not int or requested < 1:
        raise ValueError('Invalid AI allocation mode or quantity')
    if organization_used + requested > organization_limit:
        raise ValueError('Organization AI credits exhausted')
    if mode == 'Individual':
        if allocated <= 0:
            raise ValueError('No AI credits allocated. Contact your Institute Admin.')
        if user_used + requested > allocated:
            raise ValueError('Your AI credits are exhausted')
    return True
