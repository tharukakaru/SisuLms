"""Validation shared by delivery endpoints; addresses are private order snapshots."""
import re
from .commercial_rules import money_minor

def address_snapshot(data):
    if data.get('address_confirmed') not in (True, 1, '1'):
        raise ValueError('Confirm your residential delivery address')
    result={}
    required={'recipient','phone','address_line1','city','postal_code','country'}
    for key in ('recipient','phone','address_line1','address_line2','city','region','postal_code','country'):
        value=str(data.get(key) or '').strip()
        limit=200 if key.startswith('address') else 100
        if (key in required and not value) or len(value)>limit:
            raise ValueError('Add a valid '+key.replace('_',' '))
        result[key]=value
    if not re.fullmatch(r'\+[1-9]\d{7,14}',result['phone']):
        raise ValueError('Use a delivery phone number with country code, for example +94771234567')
    return result

def offer_values(data):
    enabled=data.get('enabled') in (True,1,'1')
    if not enabled:return {'enabled':0}
    title=str(data.get('title') or '').strip()
    bank=str(data.get('bank_instructions') or '').strip()
    description=str(data.get('description') or '').strip()
    if not title or len(title)>140:raise ValueError('Add a material title of up to 140 characters')
    if not bank or len(bank)>1000:raise ValueError('Add bank transfer instructions of up to 1,000 characters')
    if len(description)>1000:raise ValueError('Description must be at most 1,000 characters')
    amount=money_minor(data.get('amount'))
    if amount>2147483647:raise ValueError('Delivery price exceeds the supported limit')
    return dict(enabled=1,title=title,description=description,bank_instructions=bank,amount_minor=amount)

def next_status(current,action):
    if current=='Pending' and action in ('Approved','Rejected'):return action
    if current=='Approved' and action=='Dispatched':return action
    raise ValueError('This order cannot move from '+current+' to '+action)
