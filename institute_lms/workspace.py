"""Provider-scoped expenses, operators, reviews and content controls.

Operator grants are deliberately limited to expenses. They never become teachers,
institute administrators, payment approvers or financial settlement operators.
"""
import hashlib,json,secrets
from datetime import datetime
import frappe
from .commercial import account_access,current_account,account_for,locked,locked_reason
from .commercial_rules import PLANS
from .plan_catalog import plan_features
from .workspace_rules import expense,settings,review
DT='IL Workspace Record'
def unpack(row):
    value=json.loads(row.payload or '{}')
    return dict(value,name=row.name,status=row.status,created_at=str(row.creation),subject_user=row.subject_user)
def save(row):
    row.flags.workspace_service=True
    return row.save(ignore_permissions=True)
def record(account,kind,key,values,**extra):
    name=frappe.db.get_value(DT,{'record_key':key},'name')
    row=frappe.get_doc(DT,name) if name else frappe.get_doc(dict(doctype=DT,record_key=key,institute=account.institute,provider_account=account.name,kind=kind,status='Active',**extra))
    row.payload=json.dumps(values);return save(row)
def active_operator():
    if frappe.session.user=='Guest':return None
    name=frappe.db.get_value(DT,{'kind':'Operator','subject_user':frappe.session.user,'status':'Active'},'name')
    return frappe.get_doc(DT,name) if name else None
def actor(operator_ok=False):
    if frappe.session.user=='Guest' or not frappe.db.get_value('User',frappe.session.user,'enabled'):frappe.throw('Sign in with an active account',frappe.PermissionError)
    if operator_ok:
        grant=active_operator()
        if grant:
            account=frappe.get_doc('IL Provider Account',grant.provider_account)
            limit=PLANS[account.plan]['operators']
            allowed=frappe.get_all(DT,filters={'kind':'Operator','provider_account':account.name,'status':'Active'},pluck='name',order_by='creation asc',limit_page_length=limit or 1)
            if not limit or grant.name not in allowed:frappe.throw('Operator access is not included in the current package',frappe.PermissionError)
            if locked_reason(account):frappe.throw(locked_reason(account),frappe.PermissionError)
            return account,True
    account=current_account()
    if not account:frappe.throw('Assign a provider package first')
    account_access(account)
    if locked_reason(account):frappe.throw(locked_reason(account),frappe.PermissionError)
    return account,False
def require(account,feature):
    if not plan_features(account.plan).get(feature):frappe.throw('This tool is not included in your package',frappe.PermissionError)
def settings_for(account):
    name=frappe.db.get_value(DT,{'record_key':'settings:'+account.name},'name')
    raw=unpack(frappe.get_doc(DT,name)) if name else {}
    return settings(raw,account.plan=='Platinum')
@frappe.whitelist(methods=['GET'])
def overview():
    account,is_operator=actor(True)
    return dict(plan=account.plan,operator=is_operator,operator_limit=PLANS[account.plan]['operators'],features=plan_features(account.plan),settings=settings_for(account),
        readiness=dict(private_video=bool(frappe.conf.get('il_private_media_s3')),zoom=bool(frappe.conf.get('il_zoom_server')),watermark=True),
        operators=[] if is_operator else [unpack(x) for x in frappe.get_all(DT,filters={'provider_account':account.name,'kind':'Operator'},fields=['*'],limit_page_length=100)])
@frappe.whitelist(methods=['POST'])
def save_settings(data):
    account,_=actor();require(account,'view_limits');locked('IL Provider Account',account.name)
    try:values=settings(frappe.parse_json(data),account.plan=='Platinum')
    except (ValueError,TypeError,OverflowError) as exc:frappe.throw(str(exc))
    record(account,'Settings','settings:'+account.name,values)
    return values
@frappe.whitelist(methods=['GET'])
def expenses(start=None,end=None):
    from datetime import date
    account,_=actor(True);require(account,'expenses')
    try:
        start=date.fromisoformat(start or date.today().replace(day=1).isoformat());end=date.fromisoformat(end or date.today().isoformat())
        if start>end:raise ValueError('Start date must precede the end date')
    except ValueError as exc:frappe.throw(str(exc))
    rows=[unpack(x) for x in frappe.get_all(DT,filters={'provider_account':account.name,'kind':'Expense'},fields=['*'],order_by='creation desc',limit_page_length=10001)]
    if len(rows)>10000:frappe.throw('Use an administrator export for more than 10,000 expenses')
    rows=[x for x in rows if start.isoformat()<=x['date']<=end.isoformat()]
    return dict(rows=rows,total_minor=sum(x['amount_minor'] for x in rows if x['status']=='Active'))
@frappe.whitelist(methods=['POST'])
def add_expense(data):
    account,_=actor(True);require(account,'expenses');locked('IL Provider Account',account.name)
    try:values=expense(frappe.parse_json(data))
    except (ValueError,TypeError) as exc:frappe.throw(str(exc))
    key='expense:'+account.name+':'+values['token']
    existing=frappe.db.get_value(DT,{'record_key':key},'name')
    if existing:return unpack(frappe.get_doc(DT,existing))
    return unpack(record(account,'Expense',key,values,subject_user=frappe.session.user))
@frappe.whitelist(methods=['POST'])
def void_expense(name,reason):
    account,is_operator=actor(True);require(account,'expenses')
    row=locked(DT,name)
    if row.kind!='Expense' or row.provider_account!=account.name:frappe.throw('Expense unavailable',frappe.PermissionError)
    if is_operator and row.subject_user!=frappe.session.user:frappe.throw('Only the provider can void another operator’s expense',frappe.PermissionError)
    if not 5<=len(str(reason).strip())<=300:frappe.throw('Give a reason in 5–300 characters')
    values=json.loads(row.payload);values['void_reason']=reason;values['voided_by']=frappe.session.user
    row.status='Void';row.payload=json.dumps(values);save(row);return {'status':'Void'}
@frappe.whitelist(methods=['POST'])
def add_operator(user):
    account,_=actor();locked('IL Provider Account',account.name)
    maximum=PLANS[account.plan]['operators']
    if not maximum:frappe.throw('Operators require Gold or Platinum',frappe.PermissionError)
    if user in ('Administrator','Guest',frappe.session.user) or not frappe.db.get_value('User',user,'enabled'):frappe.throw('Choose an existing, enabled operator account')
    if frappe.db.exists('IL Member',{'user':user,'active':1}):frappe.throw('Use a dedicated operator account without an active teaching or student membership')
    key='operator:'+hashlib.sha256(user.encode()).hexdigest()
    old=frappe.db.get_value(DT,{'record_key':key},['name','status','provider_account'],as_dict=True)
    if old and old.provider_account!=account.name:frappe.throw('This operator is assigned to another provider')
    if old and old.status=='Active':return {'saved':True}
    if frappe.db.count(DT,{'kind':'Operator','provider_account':account.name,'status':'Active'})>=maximum:frappe.throw('Your package operator limit has been reached')
    row=record(account,'Operator',key,{'permissions':['expenses']},subject_user=user);row.status='Active';save(row)
    return {'saved':True}
@frappe.whitelist(methods=['POST'])
def revoke_operator(name):
    account,_=actor();locked('IL Provider Account',account.name);row=locked(DT,name)
    if row.kind!='Operator' or row.provider_account!=account.name:frappe.throw('Operator unavailable',frappe.PermissionError)
    row.status='Revoked';save(row);return {'saved':True}
def review_room(classroom,write=False):
    from .api import accessible_room,classroom_for
    result=classroom_for(classroom,write=True) if write else accessible_room(classroom)
    account=account_for(result[2]);require(account,'reviews')
    return account,result[1],result[2]
@frappe.whitelist(methods=['GET'])
def reviews(classroom):
    account,member,room=review_room(classroom)
    filters={'provider_account':account.name,'classroom':room.name,'kind':'Review'}
    if member.role=='Student':filters['status']='Active'
    rows=[dict(unpack(x),mine=x.subject_user==frappe.session.user) for x in frappe.get_all(DT,filters=filters,fields=['*'],order_by='creation desc',limit_page_length=200)]
    for x in rows:x.pop('subject_user',None)
    return rows
@frappe.whitelist(methods=['POST'])
def save_review(classroom,data):
    account,member,room=review_room(classroom)
    if member.role!='Student':frappe.throw('Only enrolled students can review a class',frappe.PermissionError)
    locked('IL Provider Account',account.name)
    try:values=review(frappe.parse_json(data))
    except (ValueError,TypeError) as exc:frappe.throw(str(exc))
    values['student_name']=member.full_name;key='review:'+hashlib.sha256((room.name+':'+member.user).encode()).hexdigest()
    existing=frappe.db.get_value(DT,{'record_key':key},'name')
    if existing:
        previous=frappe.get_doc(DT,existing)
        if previous.status=='Hidden':frappe.throw('This review is under moderation. Contact your teacher.')
        old=json.loads(previous.payload);values['reply']=old.get('reply','')
    record(account,'Review',key,values,classroom=room.name,subject_user=member.user)
    return {'saved':True}
@frappe.whitelist(methods=['POST'])
def moderate_review(name,action,body=''):
    row=frappe.get_doc(DT,name)
    if row.kind!='Review':frappe.throw('Review unavailable')
    account,member,room=review_room(row.classroom,True)
    if row.provider_account!=account.name:frappe.throw('Review unavailable',frappe.PermissionError)
    if action not in ('reply','hide','restore') or not 5<=len(body.strip())<=1000:frappe.throw('Add a reply or moderation reason in 5–1000 characters')
    row=locked(DT,name);values=json.loads(row.payload)
    if action=='reply':values['reply']=body
    else:row.status='Hidden' if action=='hide' else 'Active';values['moderation_reason']=body
    row.payload=json.dumps(values);save(row);return {'saved':True}
def consume_view(room,member,key,kind):
    if member.role!='Student':return
    account=account_for(room,False)
    if not account or not plan_features(account.plan).get('view_limits'):return
    config=settings_for(account);limit=config.get(kind+'_views',0)
    if not limit:return
    locked('IL Provider Account',account.name)
    record_key='views:'+hashlib.sha256((member.user+':'+key).encode()).hexdigest()
    existing=frappe.db.get_value(DT,{'record_key':record_key},'name')
    count=json.loads(frappe.get_doc(DT,existing).payload)['count'] if existing else 0
    if count>=limit:frappe.throw('Your viewing limit has been reached. Contact your teacher.',frappe.PermissionError)
    record(account,'View',record_key,{'count':count+1},classroom=room.name,subject_user=member.user)
    # GET content responses are not auto-committed by Frappe.
    frappe.db.commit()
def enforce_session(room,member):
    if member.role!='Student':return
    account=account_for(room,False)
    if not account or not plan_features(account.plan).get('view_limits'):return
    maximum=settings_for(account).get('concurrent_sessions',0)
    if not maximum:return
    sid=str(frappe.session.sid or '')
    if not sid or sid=='Guest':frappe.throw('A browser session is required',frappe.PermissionError)
    key='sisu-session-lease:'+hashlib.sha256((account.name+':'+member.user).encode()).hexdigest()
    fingerprint=hashlib.sha256(sid.encode()).hexdigest();now=datetime.now().timestamp()
    cache=frappe.cache()
    with cache.lock(key+':lock',timeout=5):
        leases=cache.get_value(key) or {};leases={k:v for k,v in leases.items() if v>now-900}
        if fingerprint not in leases and len(leases)>=maximum:frappe.throw('Another session is active. Close it and wait up to 15 minutes before switching.',frappe.PermissionError)
        leases[fingerprint]=now;cache.set_value(key,leases,expires_in_sec=900)

@frappe.whitelist(methods=['POST'])
def analyse_slip(name):
    from .commercial import reviewer
    from .slip_analysis import compare_text
    slip=frappe.get_doc('IL Bank Slip',name);_,_,room=reviewer(slip);account=account_for(room);require(account,'expenses')
    file=frappe.get_doc('File',slip.proof_file)
    if not file.is_private:frappe.throw('A private proof file is required')
    raw=file.get_content()
    if len(raw)>5*1024*1024:frappe.throw('Proof exceeds the supported size')
    text='';mode='Image: manual visual verification required'
    if raw.startswith(b'%PDF-'):
        from pypdf import PdfReader
        from io import BytesIO
        try:
            reader=PdfReader(BytesIO(raw))
            if reader.is_encrypted or len(reader.pages)>10:frappe.throw('Use a readable PDF with at most ten pages')
            text=' '.join(page.extract_text() or '' for page in reader.pages)[:50000];mode='PDF text checks'
        except (ValueError,TypeError):frappe.throw('This PDF could not be analysed; review the original slip')
    else:
        from .slip_ocr import image_text
        try:text,mode=image_text(raw,frappe.conf.get('il_slip_ocr_executable'))
        except ValueError as exc:frappe.throw(str(exc))
    checks=compare_text(text,int(slip.claimed_minor),slip.reference,slip.transfer_date)
    duplicate=frappe.db.exists('IL Bank Slip',{'name':['!=',slip.name],'provider_account':account.name,'reference':slip.reference,'status':['!=','Rejected']})
    return dict(mode=mode,checks=checks,duplicate_reference=bool(duplicate),notice='Assistance only. Missing text is inconclusive. Verify the credit in your bank account before approval.')

@frappe.whitelist(methods=['POST'])
def vimeo_playback(material):
    from .api import accessible_room
    from .workspace_rules import vimeo_embed
    doc=frappe.get_doc('IL Material',material);_,member,room=accessible_room(doc.classroom)
    account=account_for(room);require(account,'integrations')
    try:url=vimeo_embed(doc.url or '')
    except ValueError as exc:frappe.throw(str(exc))
    consume_view(room,member,'vimeo:'+doc.name,'video')
    return {'url':url,'title':doc.title}

@frappe.whitelist(methods=['POST'])
def create_zoom_session(session):
    from .zoom_meetings import create
    return create(session)

def campus_brand(inst):
    values={k:inst.get(k) for k in ('name','code','title','logo','accent','language','base_fee')}
    # Institute branding applies to the campus; an independent teacher's settings
    # must not replace another institute's identity for its enrolled students.
    account=account_for({'institute':inst.name},False)
    if account and account.plan=='Platinum' and not locked_reason(account):
        config=settings_for(account)
        if config['white_label']:
            values.update(white_label=True,title=config['display_name'] or values['title'],accent=config['accent'])
    return values
