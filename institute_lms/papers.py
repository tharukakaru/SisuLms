"""Class-scoped papers. Answer keys never travel with student questions."""
import hashlib
import json
from datetime import timedelta
import frappe
from frappe.utils import now_datetime, get_datetime
from .api import identity, room_filters, classroom_for, accessible_room, require_role
from .paper_rules import validate_questions, public_questions, grade
from .pricing_rules import integer

def save(doc):
    doc.flags.paper_service=True
    return doc.save(ignore_permissions=True)

def checked(name,manage=False):
    doc=frappe.get_doc('IL Paper',name)
    _,member,room=classroom_for(doc.classroom,write=True) if manage else accessible_room(doc.classroom)
    if doc.institute!=room.institute: frappe.throw('Paper unavailable',frappe.PermissionError)
    if member.role=='Student' and doc.status!='Published': frappe.throw('Paper unavailable',frappe.PermissionError)
    return doc,member,room

@frappe.whitelist()
def listing(classroom=None,page=0):
    inst,member=identity()
    rooms=frappe.get_all('IL Classroom',filters=room_filters(inst,member),pluck='name')
    if classroom:
        classroom_for(classroom);rooms=[classroom] if classroom in rooms else []
    filters={'institute':inst.name,'classroom':['in',rooms or ['__none__']]}
    if member.role=='Student':filters['status']='Published'
    return frappe.get_all('IL Paper',filters=filters,fields=['name','classroom','title','source','status','duration_minutes','opens_at','closes_at','max_marks'],
        start=max(0,min(int(page),10000))*30,limit_page_length=30,order_by='creation desc')

@frappe.whitelist(methods=['POST'])
def draft(data):
    if isinstance(data,str):data=json.loads(data)
    inst,member,room=classroom_for(data.get('classroom'),write=True)
    if data.get('name'):
        frappe.db.sql('SELECT name FROM `tabIL Paper` WHERE name=%s FOR UPDATE',(data['name'],))
        doc,_,_=checked(data['name'],True)
        if doc.status!='Draft' or doc.classroom!=room.name:frappe.throw('Only drafts in this classroom can be edited')
    else:doc=frappe.get_doc({'doctype':'IL Paper','institute':inst.name,'classroom':room.name,'source':'Manual','status':'Draft'})
    title=str(data.get('title','')).strip()
    if not title or len(title)>120:frappe.throw('A title of at most 120 characters is required')
    try:
        rows=validate_questions(data.get('questions',[]))
        minutes=integer(data.get('duration_minutes',60),'Duration',360)
        if minutes<1:raise ValueError('Duration must be at least one minute')
    except ValueError as e:frappe.throw(str(e))
    doc.title=title;doc.description=str(data.get('description',''))[:2000];doc.questions=json.dumps(rows,ensure_ascii=False)
    doc.duration_minutes=minutes;doc.max_marks=sum(q['marks'] for q in rows)
    doc.opens_at=get_datetime(data['opens_at']) if data.get('opens_at') else None
    doc.closes_at=get_datetime(data['closes_at']) if data.get('closes_at') else None
    if doc.opens_at and doc.closes_at and doc.closes_at<=doc.opens_at:frappe.throw('Closing time must follow opening time')
    material=data.get('material')
    if material:
        mat=frappe.get_doc('IL Material',material)
        if mat.classroom!=room.name:frappe.throw('Choose a document in this classroom')
    doc.material=material;doc.allow_upload=int(data.get('allow_upload') is True)
    save(doc)
    return {'name':doc.name,'status':doc.status}

@frappe.whitelist()
def detail(name):
    doc,member,_=checked(name)
    result={k:doc.get(k) for k in ('name','title','description','classroom','status','source','max_marks','duration_minutes','opens_at','closes_at','material','allow_upload')}
    if member.role!='Student':result['questions']=json.loads(doc.questions)
    return result

@frappe.whitelist(methods=['POST'])
def publish(name,reviewed=False):
    frappe.db.sql('SELECT name FROM `tabIL Paper` WHERE name=%s FOR UPDATE',(name,))
    doc,_,_=checked(name,True)
    if doc.status!='Draft' or reviewed is not True:frappe.throw('Review the complete paper and answer key before publishing')
    validate_questions(json.loads(doc.questions))
    doc.status='Published';doc.published_by=frappe.session.user;doc.published_at=now_datetime();save(doc)
    return {'status':doc.status}

@frappe.whitelist(methods=['POST'])
def archive(name):
    frappe.db.sql('SELECT name FROM `tabIL Paper` WHERE name=%s FOR UPDATE',(name,))
    doc,_,_=checked(name,True);doc.status='Archived';save(doc)
    return {'status':doc.status}

@frappe.whitelist(methods=['POST'])
def start(name):
    doc,member,_=checked(name);require_role(member,'Student')
    now=now_datetime()
    if (doc.opens_at and now<get_datetime(doc.opens_at)) or (doc.closes_at and now>=get_datetime(doc.closes_at)):frappe.throw('This paper is outside its availability window')
    # One authoritative attempt per student; concurrent starts serialize on the student row.
    frappe.db.sql('SELECT name FROM `tabIL Member` WHERE name=%s FOR UPDATE',(member.name,))
    key=hashlib.sha256((name+':'+member.name).encode()).hexdigest()
    existing=frappe.db.get_value('IL Paper Attempt',{'attempt_key':key},'name')
    if existing:a=frappe.get_doc('IL Paper Attempt',existing)
    else:
        deadline=now+timedelta(minutes=doc.duration_minutes)
        if doc.closes_at:deadline=min(deadline,get_datetime(doc.closes_at))
        a=save(frappe.get_doc({'doctype':'IL Paper Attempt','paper':name,'student':member.name,'attempt_key':key,
            'started_at':now,'deadline':deadline,'status':'Started'}))
    if a.status!='Started' or get_datetime(a.deadline)<=now:frappe.throw('Your attempt has ended')
    return {'attempt':a.name,'deadline':a.deadline,'server_time':now,'questions':public_questions(json.loads(doc.questions))}

@frappe.whitelist(methods=['POST'])
def submit(attempt,answers):
    a=frappe.get_doc('IL Paper Attempt',attempt);doc,member,_=checked(a.paper);require_role(member,'Student')
    if a.student!=member.name:frappe.throw('Attempt unavailable',frappe.PermissionError)
    frappe.db.sql('SELECT name FROM `tabIL Paper Attempt` WHERE name=%s FOR UPDATE',(attempt,));a.reload()
    if a.status!='Started':return {'status':a.status}
    if now_datetime()>get_datetime(a.deadline):frappe.throw('The submission deadline has passed')
    if isinstance(answers,str):answers=json.loads(answers)
    try:score,manual=grade(json.loads(doc.questions),answers)
    except ValueError as e:frappe.throw(str(e))
    a.answers=json.dumps(answers,ensure_ascii=False);a.score=score;a.status='Submitted' if manual or a.file_id else 'Graded';a.submitted_at=now_datetime();save(a)
    return {'status':a.status,'score':a.score if a.status=='Graded' else None}

@frappe.whitelist()
def submissions(paper,page=0):
    doc,member,_=checked(paper)
    filters={'paper':doc.name}
    if member.role=='Student':filters['student']=member.name
    return frappe.get_all('IL Paper Attempt',filters=filters,fields=['name','student','status','started_at','deadline','score','feedback','answers','file_id'],
        start=max(0,min(int(page),10000))*30,limit_page_length=30,order_by='creation desc')

@frappe.whitelist(methods=['POST'])
def mark(attempt,score,feedback):
    a=frappe.get_doc('IL Paper Attempt',attempt);doc,_,_=checked(a.paper,True)
    frappe.db.sql('SELECT name FROM `tabIL Paper Attempt` WHERE name=%s FOR UPDATE',(attempt,));a.reload()
    if a.status not in ('Submitted','Graded'):frappe.throw('The student has not submitted this attempt')
    try:a.score=integer(score,'Score',doc.max_marks)
    except ValueError as e:frappe.throw(str(e))
    a.feedback=str(feedback)[:2000];a.status='Graded';a.graded_by=frappe.session.user;save(a)
    return {'status':a.status}

@frappe.whitelist(methods=['POST'])
def upload_answer(attempt):
    import secrets
    from .material_contract import validate_file,MAX_BYTES
    from frappe.utils.file_manager import save_file
    a=frappe.get_doc('IL Paper Attempt',attempt);doc,member,_=checked(a.paper);require_role(member,'Student')
    if a.student!=member.name or not doc.allow_upload:frappe.throw('Answer upload unavailable',frappe.PermissionError)
    frappe.db.sql('SELECT name FROM `tabIL Paper Attempt` WHERE name=%s FOR UPDATE',(attempt,));a.reload()
    if a.status!='Started' or now_datetime()>=get_datetime(a.deadline):frappe.throw('The attempt has ended')
    item=frappe.request.files.get('file')
    if not item:frappe.throw('Choose your answer PDF')
    raw=item.stream.read(MAX_BYTES+1)
    try:validate_file(item.filename,raw,preview=True)
    except ValueError as e:frappe.throw(str(e))
    f=save_file('answer-'+secrets.token_hex(12)+'.pdf',raw,'IL Paper Attempt',a.name,is_private=1)
    a.file_id=f.name;save(a)
    return {'uploaded':True}

@frappe.whitelist(methods=['GET'])
def answer_file(attempt):
    from pathlib import Path
    from .material_contract import validate_file,MAX_BYTES
    a=frappe.get_doc('IL Paper Attempt',attempt);_,member,_=checked(a.paper)
    if member.role=='Student' and a.student!=member.name:frappe.throw('Answer unavailable',frappe.PermissionError)
    if not a.file_id:frappe.throw('No answer PDF')
    f=frappe.get_doc('File',a.file_id)
    if not f.is_private or f.attached_to_doctype!='IL Paper Attempt' or f.attached_to_name!=a.name:frappe.throw('Answer unavailable',frappe.PermissionError)
    from .storage import read_private
    raw=read_private(f,MAX_BYTES);validate_file(f.file_name,raw,preview=True)
    frappe.local.response.update({'type':'download','filename':'answer.pdf','filecontent':raw,'content_type':'application/pdf','display_content_as':'inline'})
    frappe.local.response_headers.update({'Cache-Control':'no-store, private','X-Content-Type-Options':'nosniff'})

@frappe.whitelist(methods=['POST'])
def generate(classroom,topic,count=5,document=None,request_id=None):
    from .saas import require
    require('ai.quiz')
    from .ai_access import authorize
    inst,member,room=authorize('ai.quiz',classroom,teacher=True)
    count=integer(count,'Question count',20);topic=str(topic).strip()
    if count<1 or not 5<=len(topic)<=2000:frappe.throw('Use a topic of 5–2,000 characters and 1–20 questions')
    from .ai import feature
    from .ai_rules import fingerprint
    result=feature('quiz',classroom,document,f'Create exactly {count} MCQ questions about: '+topic,request_id,teacher=True)
    rows=validate_questions(result['questions'])
    if len(rows)!=count:frappe.throw('Generated count did not match; no paper was published')
    key=fingerprint([frappe.session.user,classroom,result,topic,count])
    frappe.db.sql('SELECT name FROM `tabIL Classroom` WHERE name=%s FOR UPDATE',(room.name,))
    old=frappe.db.sql('SELECT name,status FROM `tabIL Paper` WHERE ai_request_key=%s FOR UPDATE',(key,))
    if old:return {'name':old[0][0],'status':old[0][1]}
    created=draft({'classroom':room.name,'title':topic[:120],'questions':rows,'duration_minutes':60})
    doc=frappe.get_doc('IL Paper',created['name']);doc.source='AI';doc.ai_request_key=key;save(doc)
    return created
