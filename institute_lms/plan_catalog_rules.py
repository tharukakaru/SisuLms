"""Validated, versioned provider plan data. No database dependency."""
from copy import deepcopy
from .provider_usage_rules import PLANS
from .commercial_rules import plan_features
EDITABLE_FEATURES = ('news', 'integrations', 'expenses', 'custom_domain', 'view_limits', 'reviews', 'watermark', 'tute_delivery', 'white_label')
def defaults():
    return {name:dict(description='',monthly_lkr=p['monthly_lkr'],features={k:plan_features(name)[k] for k in EDITABLE_FEATURES}) for name,p in PLANS.items()}
def validate(plans):
    if not isinstance(plans,dict) or set(plans)!=set(PLANS):raise ValueError('Keep all four supported plans')
    result=deepcopy(plans)
    for name,p in result.items():
        if not isinstance(p,dict) or set(p)!={'description','monthly_lkr','features'}:raise ValueError('Unsupported plan fields')
        if type(p['monthly_lkr']) is not int or not 1<=p['monthly_lkr']<=10000000:raise ValueError('Monthly price must be whole LKR between 1 and 10,000,000')
        if not isinstance(p['description'],str) or len(p['description'])>500:raise ValueError('Description must be at most 500 characters')
        if not isinstance(p['features'],dict) or set(p['features'])!=set(EDITABLE_FEATURES) or any(type(v) is not bool for v in p['features'].values()):raise ValueError('Only supported feature switches are allowed')
        p['description']=p['description'].strip()
    return result
