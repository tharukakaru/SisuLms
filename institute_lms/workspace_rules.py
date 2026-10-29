"""Pure validation for provider tools. Money is stored in integer minor units."""
from datetime import date
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlsplit
CATEGORIES=('Teaching','Rent','Utilities','Marketing','Materials','Transport','Other')
def expense(data):
    try:
        amount=Decimal(str(data.get('amount','')))
        if not amount.is_finite() or amount<=0 or amount>Decimal('100000000') or amount*100!=(amount*100).to_integral_value():raise ValueError()
    except (InvalidOperation,ValueError):raise ValueError('Use a positive amount with at most two decimal places')
    day=date.fromisoformat(str(data.get('date','')))
    if day>date.today():raise ValueError('An expense date cannot be in the future')
    category=data.get('category')
    if category not in CATEGORIES:raise ValueError('Choose an expense category')
    note=str(data.get('note','')).strip()
    if not 3<=len(note)<=500:raise ValueError('Describe the expense in 3–500 characters')
    token=str(data.get('token',''))
    if not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',token):raise ValueError('A valid submission token is required')
    return dict(amount_minor=int(amount*100),date=day.isoformat(),category=category,note=note,token=token)
def settings(data,platinum=False):
    result={}
    for key,maximum in [('document_views',1000),('video_views',1000),('concurrent_sessions',10)]:
        value=data.get(key,0)
        if isinstance(value,bool) or str(value).strip()!=str(int(value)) or not 0<=int(value)<=maximum:raise ValueError('Limits must be whole numbers within the displayed range')
        result[key]=int(value)
    result['white_label']=bool(data.get('white_label')) if platinum else False
    result['pdf_watermark']=bool(data.get('pdf_watermark')) if platinum else False
    result['display_name']=str(data.get('display_name','')).strip()[:80] if platinum else ''
    color=str(data.get('accent','#51258a'))
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',color):raise ValueError('Choose a valid brand colour')
    result['accent']=color if platinum else '#51258a'
    return result
def review(data):
    rating=data.get('rating')
    if str(rating) not in ('1','2','3','4','5'):raise ValueError('Choose one to five stars')
    body=str(data.get('body','')).strip()
    if not 10<=len(body)<=1500:raise ValueError('Write 10–1500 characters about your learning experience')
    return dict(rating=int(rating),body=body)
def vimeo_embed(value):
    u=urlsplit(value)
    if u.scheme!='https' or u.hostname not in ('vimeo.com','www.vimeo.com','player.vimeo.com') or u.username or u.password:raise ValueError('Use an HTTPS Vimeo video URL')
    parts=u.path.strip('/').split('/')
    if parts[0]=='video':parts=parts[1:]
    if not parts or not parts[0].isdigit():raise ValueError('Use a Vimeo video URL')
    from urllib.parse import parse_qs,urlencode
    token=parts[1] if len(parts)>1 else parse_qs(u.query).get('h',[''])[0]
    if token and not re.fullmatch(r'[a-zA-Z0-9]+',token):raise ValueError('Invalid Vimeo privacy token')
    return 'https://player.vimeo.com/video/'+parts[0]+('?' + urlencode({'h':token}) if token else '')
