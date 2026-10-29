"""Bounded queued generation reusing source authorization, AI accounting and IL Paper."""
import json
import math
import frappe
from .saas import managed
from .ai_rules import fingerprint

def checked(name):
    from .ai_access import authorize
    doc=frappe.get_doc('IL Paper Generation Job',name)
    authorize('ai.quiz',doc.classroom,teacher=True)
    if doc.user!=frappe.session.user:frappe.throw('Only the job owner may read this private draft',frappe.PermissionError)
    return doc

@frappe.whitelist(methods=['POST'])
def create(classroom,document,topic,count=10,duration_minutes=120,request_id=None,blueprint=None,template_metadata=None):
    from .ai_access import authorize
    from .ai import sources_for
    from .pricing_rules import integer
    inst,member,room=authorize('ai.quiz',classroom,teacher=True)
    count=integer(count,'Question count',100);minutes=integer(duration_minutes,'Duration',360)
    if count<1 or minutes<1 or not 5<=len(str(topic))<=1000:frappe.throw('Provide a topic, 1â€“100 questions and 1â€“360 minutes')
    from .paper_blueprint import validate
    blueprint=json.loads(blueprint) if isinstance(blueprint,str) else blueprint
    template_metadata=json.loads(template_metadata) if isinstance(template_metadata,str) else template_metadata
    blueprint,template_metadata=validate(count,blueprint,template_metadata)
    import re
    if not re.fullmatch(r'[A-Za-z0-9_:-]{8,160}',str(request_id)):frappe.throw('Stable request identifier required')
    sources=sources_for(room,document)
    if not sources:frappe.throw('Index an authorized source first; video transcripts must be approved text')
    key=fingerprint([frappe.local.site,member.user,request_id])
    with frappe.cache.lock('il_paper_job:'+key,timeout=10):
        old=frappe.db.get_value('IL Paper Generation Job',{'request_key':key},'name')
        if old:
            d=checked(old)
            if (d.classroom,d.document,d.topic,int(d.count),int(d.duration_minutes))!=(classroom,document,topic,count,minutes):frappe.throw('Request identifier reused for different input')
            if json.loads(d.blueprint or '[]')!=blueprint or json.loads(d.template_metadata or '{}')!=template_metadata:frappe.throw('Request identifier reused for different blueprint')
            return {'name':d.name,'status':d.status}
        d=managed(frappe.get_doc({'doctype':'IL Paper Generation Job','request_key':key,'institute':inst.name,
            'classroom':classroom,'user':member.user,'document':document,'topic':topic,'count':count,'duration_minutes':minutes,
            'status':'Queued','progress':0,'blueprint':json.dumps(blueprint),'template_metadata':json.dumps(template_metadata),'batch_results':'[]','source_versions':json.dumps(sources)}))
        frappe.enqueue('institute_lms.paper_generator.run',name=d.name,queue='long',timeout=1200,enqueue_after_commit=True,job_id='paper-'+d.name)
        return {'name':d.name,'status':d.status,'batches':math.ceil(count/20)}

def run(name):
    d=frappe.get_doc('IL Paper Generation Job',name)
    previous=frappe.session.user
    try:
        frappe.set_user(d.user)
        with frappe.cache.lock('il_paper_job_run:'+name,timeout=1200,blocking_timeout=1):
            d=checked(name)
            if d.status!='Queued':return
            if not d.blueprint:frappe.throw('Legacy job requires accounting review; do not reissue provider work automatically')
            from .ai_access import authorize
            from .ai import generate_result,recheck_sources
            from .ai_accounting import execute
            context=authorize('ai.quiz',d.classroom,teacher=True);sources=json.loads(d.source_versions)
            def current_sources():
                recheck_sources(context[2],sources)
                for source in sources:
                    if frappe.db.get_value('IL Knowledge Document',source['document'],'version')!=source['version']:
                        frappe.throw('Source version changed; create a fresh generation request')
            current_sources()
            d.status='Running';managed(d);frappe.db.commit()
            from .paper_blueprint import batches
            from .paper_rules import validate_questions
            blueprint=json.loads(d.blueprint or 'null') or [{'kind':'MCQ','count':d.count,'marks':1}]
            completed=json.loads(d.batch_results or '[]');rows=[];seen=set()
            for index,spec in enumerate(batches(blueprint)):
                authorize('ai.quiz',d.classroom,teacher=True);current_sources()
                if index<len(completed):batch=validate_questions(completed[index])
                else:
                    prompt=f"{d.topic}. Create exactly {spec['count']} {spec['kind']} questions worth {spec['marks']} marks each. Avoid previous prompts: "+json.dumps([x['prompt'] for x in rows])[:8000]
                    def generate():
                        result=generate_result('quiz',prompt,sources)
                        batch=validate_questions(result['questions'])
                        if len(batch)!=spec['count'] or any(q['kind']!=spec['kind'] for q in batch):raise ValueError('Blueprint mismatch')
                        for q in batch:q['marks']=spec['marks']
                        return {'questions':batch,'draft':True}
                    # Each completed batch has an independent durable accounting result.
                    # Resume replays that result; unknown provider outcomes remain blocked.
                    result=execute('ai.quiz','paper-batch:'+d.name+':'+str(index),
                        {'job':d.name,'batch':index,'spec':spec,'sources':sources,'prompt':prompt},context,generate,kind='paper_batch')
                    batch=result['questions'];completed.append(batch)
                    d.batch_results=json.dumps(completed);d.progress=sum(len(x) for x in completed);managed(d);frappe.db.commit()
                for row in batch:
                    key=row['prompt'].strip().casefold()
                    if key in seen:raise ValueError('Duplicate question; review saved batch before a new job')
                    seen.add(key);rows.append(row)
            authorize('ai.quiz',d.classroom,teacher=True);current_sources()
            result={'questions':rows,'draft':True}
            from .papers import draft,save
            prior=frappe.db.get_value('IL Paper',{'ai_request_key':d.request_key},'name')
            if prior:
                d.paper=prior;d.status='Draft';managed(d);frappe.db.commit();return
            paper=draft({'classroom':d.classroom,'title':d.topic[:120],'questions':result['questions'],'duration_minutes':d.duration_minutes})
            p=frappe.get_doc('IL Paper',paper['name']);p.source='AI';p.ai_request_key=d.request_key;save(p)
            d.paper=p.name;d.status='Draft';managed(d);frappe.db.commit()
    except Exception:
        frappe.db.rollback();d=frappe.get_doc('IL Paper Generation Job',name);d.status='Review';d.error_code='Review source, quota or provider outcome; no automatic retry';managed(d);frappe.db.commit()
    finally:frappe.set_user(previous)

@frappe.whitelist()
def status(name):
    d=checked(name)
    return {k:d.get(k) for k in ('name','status','progress','count','paper','error_code','duration_minutes','classroom')}

@frappe.whitelist()
def export(paper):
    from .papers import checked as paper_checked
    d,_,_=paper_checked(paper,True)
    # A reviewed teacher-facing export; separate answer key never reaches Student APIs.
    return {'title':d.title,'status':d.status,'duration_minutes':d.duration_minutes,
            'questions':json.loads(d.questions),'notice':'Teacher export; review before distributing. Contains answer key.'}

@frappe.whitelist(methods=['POST'])
def resume(name):
    d=checked(name)
    with frappe.cache.lock('il_paper_job_run:'+name,timeout=10,blocking_timeout=1):
        d=checked(name)
        if d.status!='Review':frappe.throw('Only jobs requiring review can be resumed')
        if not d.blueprint:frappe.throw('Legacy job cannot be resumed; reconcile original accounting before creating a new request')
        # The accounting layer refuses ambiguous/failed batches and reuses succeeded ones.
        d.status='Queued';d.error_code=None;managed(d)
        frappe.enqueue('institute_lms.paper_generator.run',name=d.name,queue='long',timeout=1200,enqueue_after_commit=True)
    return {'name':d.name,'status':d.status}

@frappe.whitelist()
def listing():
    from .api import identity,require_role
    inst,m=identity();require_role(m,'Teacher','Admin')
    return frappe.get_all('IL Paper Generation Job',filters={'institute':inst.name,'user':m.user},
        fields=['name','classroom','topic','status','progress','count','paper','error_code'],order_by='creation desc',limit_page_length=50)

@frappe.whitelist()
def printable(paper,answer_key=False):
    from html import escape
    d=export(paper)
    name=frappe.db.get_value('IL Paper Generation Job',{'paper':paper},'name')
    meta=json.loads(frappe.db.get_value('IL Paper Generation Job',name,'template_metadata') or '{}') if name else {}
    pieces=['<!doctype html><html><head><meta charset="utf-8"><title>Paper export</title></head><body>',
        '<h1>'+escape(meta.get('heading') or d['title'])+'</h1>', '<p>'+escape(meta.get('instructions',''))+'</p>',
        '<p>'+escape(d['status'])+' · '+str(d['duration_minutes'])+' minutes</p><ol>']
    for q in d['questions']:
        pieces.append('<li><p>'+escape(q['prompt'])+(' ['+str(q['marks'])+' marks]' if meta.get('show_marks',True) else '')+'</p><ol type="A">')
        pieces.extend('<li>'+escape(x)+'</li>' for x in q['options']);pieces.append('</ol>')
        if answer_key is True and q['answer'] is not None:pieces.append('<p>Answer: '+escape(q['options'][q['answer']])+'</p>')
        pieces.append('</li>')
    return {'filename':'paper-'+paper+'.html','html':''.join(pieces)+'</ol></body></html>',
        'notice':'Print/save as PDF. Draft watermark is the authoritative status; review before distributing.'}
