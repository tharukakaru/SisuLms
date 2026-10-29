"""Bounded, testable AI contracts. No credentials, Frappe or network calls."""
import hashlib,json,math,re,unicodedata
from decimal import Decimal

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def normalize(text):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',text).replace('\x00','')).strip()
def bounded(text,maximum=4000):
    if not isinstance(text,str) or not text.strip() or len(text)>maximum:raise ValueError('Text is empty or exceeds the allowed length')
    return text.strip()
def chunks(sections,size=1800,overlap=180):
    rows=[];total=0
    for label,text in sections:
        text=normalize(text);total+=len(text)
        if total>400000:raise ValueError('Document exceeds extracted text limit')
        for start in range(0,len(text),size-overlap):
            value=text[start:start+size]
            if value:rows.append(dict(section=str(label)[:120],text=value,text_hash=hashlib.sha256(value.encode()).hexdigest()))
            if start+size>=len(text):break
    if not rows:raise ValueError('No extractable text; scanned files require conversion/OCR outside this pipeline')
    if len(rows)>300:raise ValueError('Document has too many chunks')
    return rows
def history(rows,max_chars=12000,max_messages=10):
    result=[];remaining=max_chars
    for row in reversed(rows[-max_messages:]):
        if row.get('role') not in ('user','assistant'):continue
        content=str(row.get('content',''))
        if len(content)>remaining:break
        result.append({'role':row['role'],'content':content});remaining-=len(content)
    return list(reversed(result))
def tokens(response):
    u=response.get('usage') or {};details=u.get('input_tokens_details') or {}
    def n(value):return value if type(value) is int and 0<=value<=10**9 else 0
    i=n(u.get('input_tokens',u.get('prompt_tokens',0)));o=n(u.get('output_tokens',0));c=min(i,n(details.get('cached_tokens',0)))
    return dict(input_tokens=i,cached_tokens=c,output_tokens=o,total_tokens=n(u.get('total_tokens',i+o)),usage_reported=bool(u))
def estimate(usage,rate):
    if not rate:return None
    values={k:Decimal(str(rate[k])) for k in ('input','cached','output')}
    if any(not v.is_finite() or v<0 for v in values.values()):raise ValueError('Invalid model rate')
    return ((usage['input_tokens']-usage['cached_tokens'])*values['input']+usage['cached_tokens']*values['cached']+usage['output_tokens']*values['output'])/1000000
def source_policy(source,context):
    if not source.get('enabled') or source.get('status')!='Ready' or source.get('institute')!=context['institute'] or source.get('classroom')!=context['classroom']:
        raise PermissionError('Knowledge source unavailable')
def object_schema(properties):return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)
STRING={'type':'string'}
ANSWER_SCHEMA=object_schema({'answer':STRING,'citations':{'type':'array','items':STRING},'supported':{'type':'boolean'}})
CARD_SCHEMA=object_schema({'cards':{'type':'array','items':object_schema({'front':STRING,'back':STRING,'source':STRING})}})
QUESTION_SCHEMA=object_schema({'questions':{'type':'array','items':object_schema({'kind':{'type':'string','enum':['MCQ','True/False','Written']},'prompt':STRING,'options':{'type':'array','items':STRING},'answer':{'type':['integer','null']},'marks':{'type':'integer'},'source':STRING})}})
def validate_generated(value,kind,sources):
    allowed=set(sources)
    if not isinstance(value,dict):raise ValueError('Invalid generated result')
    if kind=='flashcards':
        rows=value.get('cards')
        if not isinstance(rows,list) or not 1<=len(rows)<=20:raise ValueError('Invalid flashcards')
        for row in rows:
            bounded(row.get('front'),1000);bounded(row.get('back'),2000)
            if row.get('source') not in allowed:raise ValueError('Unverified citation')
    elif kind in ('questions','quiz'):
        from .paper_rules import validate_questions
        rows=value.get('questions');clean=validate_questions(rows)
        if len(rows)>20:raise ValueError('Too many questions')
        for a,c in zip(rows,clean):
            if a.get('source') not in allowed:raise ValueError('Unverified citation')
            c['source']=a['source']
        value={'questions':clean}
    else:
        bounded(value.get('answer'),20000)
        if type(value.get('supported')) is not bool or not isinstance(value.get('citations'),list) or any(x not in allowed for x in value['citations']):raise ValueError('Unverified citation')
        if not value['supported'] or (allowed and not value['citations']):
            return dict(answer='The available course material does not support an answer to this request.',citations=[],supported=False)
    return value
