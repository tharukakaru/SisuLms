from datetime import date

def preferences(data):
    if not isinstance(data,dict): raise ValueError('Invalid preferences')
    result={}
    for key,limit in [('motto',180),('event_title',80)]:
        value=data.get(key) or ''
        if not isinstance(value,str) or len(value)>limit: raise ValueError('Invalid text')
        result[key]=' '.join(value.split())
    value=data.get('event_date') or ''
    if bool(value)!=bool(result['event_title']): raise ValueError('Title and date required')
    if value:
        parsed=date.fromisoformat(value)
        if parsed.isoformat()!=value or not 1900<=parsed.year<=2200: raise ValueError('Invalid date')
    hidden=data.get('hide_countdown',0)
    if not isinstance(hidden,(int,bool)) or hidden not in (0,1): raise ValueError('Invalid countdown visibility')
    result['hide_countdown']=int(hidden)
    result['event_date']=value or None
    return result

