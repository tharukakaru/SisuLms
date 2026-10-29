"""Stable, site-local Premium AI RPCs for Vue and Flutter. Outputs are drafts."""
import json,uuid
from datetime import timedelta
import frappe
from frappe.utils import now_datetime
from .ai_access import authorize,owned_conversation
from .ai_accounting import save,execute
from .ai_rules import (bounded,history,fingerprint,validate_generated,ANSWER_SCHEMA,CARD_SCHEMA,QUESTION_SCHEMA)

FEATURES={'summary':'ai.summaries','notes':'ai.notes','flashcards':'ai.flashcards','questions':'ai.questions','quiz':'ai.quiz','lesson_plan':'ai.teacher','revision':'ai.teacher','explanation':'ai.teacher'}

@frappe.whitelist()
def status():
    from .api import identity
    from .saas import resolved
    from .soul import student_ready
    _,m=identity();r=resolved();d=frappe.get_single('IL SOUL Settings')
    return {'features':{k:v for k,v in r['features'].items() if k.startswith('ai.')},'available':bool(r['available'] and d.enabled and student_ready(m)),
        'hosted_retrieval_enabled':bool(d.hosted_retrieval_reviewed),'usage':allowance()}

def allowance():
    from .saas import resolved
    from .usage import used,period
    r=resolved();n=used('ai_credits');p=period('ai_credits')
    user=frappe.db.sql('SELECT COALESCE(SUM(charged_units),0),COALESCE(SUM(total_tokens),0) FROM `tabIL AI Usage` WHERE user=%s AND period=%s',(frappe.session.user,p))[0]
    from .ai_credits import status as credit_status
    personal=credit_status();remaining=personal['organization_remaining']
    if personal['mode']=='Individual':remaining=min(remaining,personal['remaining'])
    return {'period':p,'mode':personal['mode'],'allocated':personal['allocated'],'personal_remaining':personal['remaining'],
        'effective_remaining':remaining,'tenant_used':n,'tenant_limit':r['limits']['ai_credits'],'tenant_remaining':max(0,r['limits']['ai_credits']-n),'user_credits':user[0],'user_tokens':user[1],'reset':'Next calendar month in site time','credit_basis':'Configured request units; tokens tracked separately'}

@frappe.whitelist()
def usage(tenant=False):
    from .api import identity,require_role
    inst,m=identity()
    if tenant is True:require_role(m,'Admin')
    filters={'institute':inst.name}
    if tenant is not True:filters['user']=frappe.session.user
    rows=frappe.get_all('IL AI Usage',filters=filters,fields=['feature','request_type','period','state','charged_units','input_tokens','cached_tokens','output_tokens','total_tokens','estimated_cost','cost_currency','usage_reported'],limit_page_length=1000,order_by='creation desc')
    return {'allowance':allowance(),'requests':rows,'bounded_to':1000}

@frappe.whitelist(methods=['POST'])
def create_conversation(classroom,title='Learning conversation'):
    inst,m,room=authorize('ai.assistant',classroom)
    title=bounded(title,120)
    d=save(frappe.get_doc({'doctype':'IL AI Conversation','institute':inst.name,'user':frappe.session.user,'classroom':room.name,'member_role':m.role,'title':title,'status':'Active'}))
    return {'name':d.name}

@frappe.whitelist()
def conversations(page=0):
    inst,_,_=authorize('ai.assistant')
    rows=frappe.get_all('IL AI Conversation',filters={'user':frappe.session.user,'institute':inst.name,'status':['!=','Deleted']},fields=['name','classroom','title','status','modified'],limit_start=max(0,min(int(page),10000))*30,limit_page_length=30,order_by='modified desc')
    allowed=[]
    for row in rows:
        try:owned_conversation(row.name)
        except frappe.PermissionError:continue
        allowed.append(row)
    return allowed

@frappe.whitelist()
def conversation(name,page=0):
    d,_,_,room=owned_conversation(name)
    rows=frappe.get_all('IL AI Message',filters={'conversation':d.name},fields=['role','content','citations','creation'],order_by='creation asc',limit_start=max(0,min(int(page),10000))*50,limit_page_length=50)
    for row in rows:
        if row.role!='assistant':continue
        try:recheck_sources(room,json.loads(row.citations or '[]'))
        except (PermissionError,frappe.PermissionError,frappe.DoesNotExistError):
            row.content='This response referenced material that is no longer available.';row.citations='[]'
    return {'name':d.name,'title':d.title,'status':d.status,'messages':rows}

@frappe.whitelist(methods=['POST'])
def archive_conversation(name,delete=False):
    # A lapsed subscription/course access must not prevent private-data deletion.
    from .api import identity
    inst,_=identity();d=frappe.get_doc('IL AI Conversation',name)
    if d.user!=frappe.session.user or d.institute!=inst.name:frappe.throw('Conversation unavailable',frappe.PermissionError)
    if d.status=='Deleted':return {'status':'Deleted','purge_after':d.delete_after}
    d.status='Deleted' if delete is True else 'Archived';d.archived_at=now_datetime()
    days=max(1,min(int(frappe.get_single('IL SOUL Settings').conversation_days or 90),3650))
    d.delete_after=now_datetime()+timedelta(days=days);save(d)
    return {'status':d.status,'purge_after':d.delete_after}

def sources_for(room,document=None):
    from .knowledge import candidates
    out=[];budget=18000
    for d in candidates(room,document).values():
        rows=frappe.get_all('IL Knowledge Chunk',filters={'document':d.name},fields=['text','section'],order_by='ordinal',limit_page_length=300)
        for row in rows:
            if len(row.text)>budget:frappe.throw('Source exceeds generation context limit; use course_question for a focused answer or a smaller source')
            out.append({'id':'S'+str(len(out)+1),'document':d.name,'version':d.version,'source_type':d.source_type,'material':d.source_name,'classroom':room.name,'title':d.title,'section':row.section,'excerpt':row.text});budget-=len(row.text)
    return out

def recheck_sources(room,sources):
    from .knowledge import current
    for name in {s['document'] for s in sources}:current(frappe.get_doc('IL Knowledge Document',name),room)

def generate_result(kind,question,sources,history_rows=None):
    from .ai_provider import generate
    schema=CARD_SCHEMA if kind=='flashcards' else QUESTION_SCHEMA if kind in ('questions','quiz') else ANSWER_SCHEMA
    if not sources:return {'answer':'The available course material does not support an answer. Ask your teacher to index relevant material.','citations':[],'supported':False,'sources':[]}
    prompt=json.dumps({'task':kind,'request':question,'sources':sources},ensure_ascii=False)
    instructions='Use only the supplied sources. Cite exact source IDs; never invent a source. Set supported=false if evidence does not answer the request. All teaching and assessment outputs are private drafts for human review. Produce at most 20 items. '
    if kind=='notes':instructions+='Organize definitions, key concepts, important points and revision notes. '
    if kind=='lesson_plan':instructions+='Draft objectives, explanation, worked examples, activities and checks for understanding. '
    data=validate_generated(generate(prompt,schema,instructions,history_rows),kind,[s['id'] for s in sources])
    data['sources']=[{k:v for k,v in s.items() if k!='excerpt'} for s in sources];data['draft']=True
    return data

def feature(kind,classroom,document=None,instruction='',request_id=None,teacher=False):
    f=FEATURES[kind];context=authorize(f,classroom,teacher=teacher);inst,m,room=context
    instruction=bounded(instruction or 'Create '+kind.replace('_',' ')+' from the supplied course material.',2000)
    sources=sources_for(room,document)
    if not sources:frappe.throw('No current indexed source is available')
    from .ai_provider import settings
    config=settings()
    payload={'kind':kind,'instruction':instruction,'sources':sources,'model':config.model,'limit':config.max_output_tokens,'prompt_version':1}
    # Cache is private per user, feature and source version. Never a shared student cache.
    key=request_id or 'cache:'+fingerprint(payload)
    def work():
        authorize(f,classroom,teacher=teacher);recheck_sources(room,sources)
        result=generate_result(kind,instruction,sources)
        authorize(f,classroom,teacher=teacher);recheck_sources(room,sources);return result
    result=execute(f,key,payload,context,work)
    authorize(f,classroom,teacher=teacher);recheck_sources(room,sources);return result

@frappe.whitelist(methods=['POST'])
def summary(classroom,document=None,instruction='',request_id=None):return feature('summary',classroom,document,instruction,request_id)
@frappe.whitelist(methods=['POST'])
def notes(classroom,document=None,instruction='',request_id=None):return feature('notes',classroom,document,instruction,request_id)
@frappe.whitelist(methods=['POST'])
def flashcards(classroom,document=None,instruction='',request_id=None):return feature('flashcards',classroom,document,instruction,request_id)
@frappe.whitelist(methods=['POST'])
def questions(classroom,document=None,instruction='',request_id=None):return feature('questions',classroom,document,instruction,request_id)

@frappe.whitelist(methods=['POST'])
def teacher_assistant(classroom,task='lesson_plan',document=None,instruction='',request_id=None):
    authorize('ai.teacher',classroom,teacher=True)
    if task not in FEATURES:frappe.throw('Unsupported teacher task')
    return feature(task,classroom,document,instruction,request_id,teacher=True)

@frappe.whitelist(methods=['POST'])
def course_question(classroom,question,request_id,conversation=None,consent=False,mode='question'):
    from .saas import require
    context=authorize('ai.assistant',classroom);require('ai.rag')
    inst,m,room=context;question=bounded(question)
    if consent is not True:frappe.throw('Accept the AI data-processing notice before sending')
    if mode not in ('question','explain','simplify','examples'):frappe.throw('Invalid assistant mode')
    d=None
    if conversation:
        d,_,_,_=owned_conversation(conversation,active=True)
        if d.classroom!=room.name:frappe.throw('Conversation belongs to another course',frappe.PermissionError)
    from .knowledge import candidates,search_context
    revisions={n:v.source_revision for n,v in candidates(room).items()}
    payload={'question':question,'conversation':conversation,'mode':mode,'sources':revisions}
    def work():
        authorize('ai.assistant',classroom);require('ai.rag')
        from .ai_provider import moderate
        moderate(question)
        sources=search_context(room,m,question)
        past=[]
        if d:
            # History only from still-current source versions. Revoked/changed source
            # content cannot leak back into the context through an old conversation.
            rows=frappe.get_all('IL AI Message',filters={'conversation':d.name},fields=['role','content','citations'],order_by='creation desc',limit_page_length=10)
            valid=[]
            for row in reversed(rows):
                refs=json.loads(row.citations or '[]')
                if row.role=='user':continue  # current user request is already included
                if refs and all(r['document'] in revisions for r in refs):valid.append(row)
            past=history(valid)
        result=generate_result('answer',mode+': '+question,sources,past)
        authorize('ai.assistant',classroom);recheck_sources(room,sources)
        if d:
            owned_conversation(d.name,active=True)
            from .ai_accounting import ACTIVE
            receipts=(ACTIVE.get() or {}).get('receipts',[])
            provider_id=next((r['request_id'] for r in reversed(receipts) if r['operation']=='responses'),'')
            for role,content in [('user',question),('assistant',result['answer'])]:
                save(frappe.get_doc({'doctype':'IL AI Message','conversation':d.name,'request_key':request_id,'role':role,'content':content,'citations':json.dumps(result['sources']), 'model':frappe.get_single('IL SOUL Settings').model,'provider_request_id':provider_id}))
            save(d)
        return result
    result=execute('ai.assistant',request_id,payload,context,work)
    authorize('ai.assistant',classroom);recheck_sources(room,result.get('sources',[]))
    return result

@frappe.whitelist(methods=['POST'])
def chat(conversation,question,request_id,consent=False,mode='question'):
    d,_,_,_=owned_conversation(conversation,active=True)
    return course_question(d.classroom,question,request_id,conversation,consent,mode)

@frappe.whitelist(methods=['POST'])
def search(classroom,query,request_id):
    context=authorize('ai.search',classroom);inst,m,room=context;query=bounded(query,2000)
    from .knowledge import search_context,candidates
    versions={n:d.source_revision for n,d in candidates(room).items()}
    def work():
        from .ai_provider import moderate
        moderate(query);result=search_context(room,m,query)
        authorize('ai.search',classroom);recheck_sources(room,result);return {'results':result}
    result=execute('ai.search',request_id,{'query':query,'versions':versions},context,work,'search')
    authorize('ai.search',classroom);recheck_sources(room,result['results']);return result

@frappe.whitelist(methods=['POST'])
def assignment_feedback(attempt,request_id):
    from .papers import checked
    a=frappe.get_doc('IL Paper Attempt',attempt);p,_,room=checked(a.paper,True)
    context=authorize('ai.assignments',room.name,teacher=True)
    if a.status not in ('Submitted','Graded'):frappe.throw('Submission is not ready')
    answers=json.loads(a.answers or '[]')
    if a.file_id:
        from .storage import read_private
        from .ai_extract import extract
        f=frappe.get_doc('File',a.file_id)
        if not f.is_private or f.attached_to_doctype!='IL Paper Attempt' or f.attached_to_name!=a.name:frappe.throw('Submission file unavailable',frappe.PermissionError)
        answers.append('\n'.join(text for _,text in extract(f.file_name,read_private(f,10*1024*1024))))
    payload={'questions':json.loads(p.questions),'answers':answers}
    if len(json.dumps(payload))>18000:frappe.throw('Submission exceeds AI feedback context limit')
    def work():
        from .ai_provider import generate
        result=generate(json.dumps(payload),ANSWER_SCHEMA,'Suggest draft academic feedback and rubric guidance only. Do not assign or change a final grade. Citation list must be empty; this is feedback on the supplied submission.')
        authorize('ai.assignments',room.name,teacher=True);checked(a.paper,True)
        return {'draft_feedback':validate_generated(result,'answer',[])['answer'],'attempt':attempt,'requires_teacher_review':True}
    return execute('ai.assignments',request_id,{'attempt':attempt,'modified':str(a.modified),'data':payload},context,work,'feedback')

@frappe.whitelist()
def recommendations(classroom):
    from .ai_insights import recommendations_for
    inst,m,room=authorize('ai.recommendations',classroom)
    if m.role!='Student':frappe.throw('Personal recommendations require a student account')
    return recommendations_for(inst,m,room)

@frappe.whitelist(methods=['POST'])
def admin_insights(classroom,explain=False,request_id=None):
    from .ai_insights import aggregates
    context=authorize('ai.analytics',classroom,admin=True);inst,m,room=context
    data=aggregates(room)
    if explain is not True:return data
    def work():
        from .ai_provider import generate
        result=generate(json.dumps(data),ANSWER_SCHEMA,'Explain only these verified aggregates. Never invent statistics, identify students or infer personal traits. Citations must be empty. Explicitly mention insufficient data.')
        authorize('ai.analytics',classroom,admin=True)
        return {'aggregates':data,'explanation':validate_generated(result,'answer',[])['answer']}
    return execute('ai.analytics',request_id,data,context,work,'analytics')
