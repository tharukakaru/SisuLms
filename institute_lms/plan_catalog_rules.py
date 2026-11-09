"""Validated, versioned provider plan data. No database dependency."""
from copy import deepcopy
from .provider_usage_rules import PLANS
from .commercial_rules import plan_features
FEATURE_LABELS = {'news':'News publishing','integrations':'Connected teaching tools','expenses':'Expense register','custom_domain':'Custom domain','view_limits':'Video view controls','reviews':'Class reviews','watermark':'Video watermark','tute_delivery':'Tute delivery','white_label':'Institute branding'}
EDITABLE_FEATURES = ('news', 'integrations', 'expenses', 'custom_domain', 'view_limits', 'reviews', 'watermark', 'tute_delivery', 'white_label')
def default_card_features(name):
    return ['Classroom learning', 'Assignments and quizzes', 'Live and recorded lessons'] + [FEATURE_LABELS[k] for k in EDITABLE_FEATURES if plan_features(name)[k]]

def defaults():
    return {name:dict(description='',card_features=default_card_features(name),monthly_lkr=p['monthly_lkr'],features={k:plan_features(name)[k] for k in EDITABLE_FEATURES}) for name,p in PLANS.items()}
def validate(plans):
    if not isinstance(plans,dict) or set(plans)!=set(PLANS):raise ValueError('Keep all four supported plans')
    result=deepcopy(plans)
    for name,p in result.items():
        if not isinstance(p,dict) or set(p)-{'description','monthly_lkr','features','card_features'} or not {'description','monthly_lkr','features'}<=set(p):raise ValueError('Unsupported plan fields')
        if type(p['monthly_lkr']) is not int or not 1<=p['monthly_lkr']<=10000000:raise ValueError('Monthly price must be whole LKR between 1 and 10,000,000')
        if not isinstance(p['description'],str) or len(p['description'])>500:raise ValueError('Description must be at most 500 characters')
        if not isinstance(p['features'],dict) or set(p['features'])!=set(EDITABLE_FEATURES) or any(type(v) is not bool for v in p['features'].values()):raise ValueError('Only supported feature switches are allowed')
        p.setdefault('card_features', ['Classroom learning', 'Assignments and quizzes', 'Live and recorded lessons'] + [FEATURE_LABELS[k] for k in EDITABLE_FEATURES if p['features'][k]])
        rows=p['card_features']
        if not isinstance(rows,list) or len(rows)>40 or any(not isinstance(x,str) or not 1<=len(x.strip())<=160 for x in rows):raise ValueError('Use up to 40 card features, each 1–160 characters')
        p['card_features']=[x.strip() for x in rows]
        if len(set(x.casefold() for x in p['card_features']))!=len(rows):raise ValueError('Remove duplicate card features')
        p['description']=p['description'].strip()
    return result
