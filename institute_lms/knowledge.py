"""Authorized, versioned source ingestion and hosted retrieval orchestration."""
import hashlib,json
from datetime import timedelta
from html.parser import HTMLParser
import frappe
from frappe.utils import now_datetime
from .ai_accounting import save,execute
from .ai_access import authorize,hosted_student
from .ai_rules import fingerprint,chunks,normalize,source_policy

class Plain(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
def plain(value):
    p=Plain();p.feed(str(value or ''));return ' '.join(p.parts)

def source(source_type,name,room,read=False):
    if source_type not in ('IL Material','IL Session','Course Lesson'):frappe.throw('Unsupported knowledge source')
    d=frappe.get_doc(source_type,name)
    if source_type=='Course Lesson':
        if not room.lms_course or d.get('course')!=room.lms_course:frappe.throw('Foreign course lesson',frappe.PermissionError)
        # Cross-mapped native courses must satisfy every SISU access boundary.
        from .native_access import require_course
        require_course(room.lms_course)
        raw=plain(d.get('body') or d.get('content')).encode();file=None;filename='lesson.txt'
    else:
        if d.institute!=room.institute or d.classroom!=room.name:frappe.throw('Foreign course source',frappe.PermissionError)
        file=None;filename='lesson.txt';raw=plain(d.description).encode()
        if source_type=='IL Material' and d.get('file_id'):
            file=frappe.get_doc('File',d.file_id)
            if not file.is_private or file.attached_to_doctype!='IL Classroom' or file.attached_to_name!=room.name:frappe.throw('Source must be a protected classroom file',frappe.PermissionError)
            filename=file.file_name
            if read:
                from .storage import read_private
                raw=read_private(file,10*1024*1024)
            else:raw=None
        elif source_type=='IL Material' and d.kind!='Document':
            # Never fetch external URLs, YouTube or linked pages.
            from .ai_extract import Unsupported
            raise Unsupported('Only uploaded documents and explicit lesson text are supported')
    revision=fingerprint([str(d.modified),file.name if file else None,str(file.modified) if file else None,file.content_hash if file else None])
    return dict(title=d.title,raw=raw,filename=filename,file=file.name if file else None,revision=revision)

@frappe.whitelist(methods=['POST'])
def ingest(classroom,source_type,source_name):
    inst,m,room=authorize('ai.rag',classroom,teacher=True)
    from .ai_provider import retrieval,settings
    retrieval()  # configuration/retention review, no network call
    from .ai_extract import Unsupported
    from .ai_accounting import rate_limit
    rate_limit(frappe.session.user,inst.name)
    s=source(source_type,source_name,room,read=True)
    if not s['raw']:frappe.throw('No source text or file')
    digest=hashlib.sha256(s['raw']).hexdigest();key=fingerprint([source_type,source_name,s['revision'],digest])
    frappe.db.sql('SELECT name FROM `tabIL Classroom` WHERE name=%s FOR UPDATE',(room.name,))
    old=frappe.db.sql('SELECT name,status FROM `tabIL Knowledge Document` WHERE source_key=%s FOR UPDATE',(key,))
    if old:return {'document':old[0][0],'status':old[0][1],'unchanged':True}
    count=frappe.db.count('IL Knowledge Document',{'classroom':classroom,'enabled':1})
    cap=max(1,min(int(settings().max_documents_per_course or 100),100))
    same=frappe.get_all('IL Knowledge Document',filters={'source_type':source_type,'source_name':source_name,'enabled':1},pluck='name')
    if count-len(same)>=cap:frappe.throw('Course knowledge document limit reached')
    for name in same:disable_record(frappe.get_doc('IL Knowledge Document',name))
    d=save(frappe.get_doc({'doctype':'IL Knowledge Document','source_key':key,'institute':inst.name,'classroom':room.name,
        'source_type':source_type,'source_name':source_name,'source_file':s['file'],'source_hash':digest,'source_revision':s['revision'],
        'title':s['title'],'mime_type':s['filename'].rsplit('.',1)[-1].lower(),'requested_by':frappe.session.user,
        'version':frappe.db.count('IL Knowledge Document',{'source_type':source_type,'source_name':source_name})+1,'status':'Queued','enabled':1}))
    frappe.enqueue('institute_lms.knowledge.index_document',document=d.name,queue='long',timeout=300,enqueue_after_commit=True,job_id='il-index-'+d.name)
    return {'document':d.name,'status':d.status,'unchanged':False}

def ensure_index(room,adapter):
    key=fingerprint([frappe.local.site,room.name]);frappe.db.sql('SELECT name FROM `tabIL Classroom` WHERE name=%s FOR UPDATE',(room.name,))
    name=frappe.db.get_value('IL Knowledge Index',{'index_key':key},'name')
    d=frappe.get_doc('IL Knowledge Index',name,for_update=True) if name else save(frappe.get_doc({'doctype':'IL Knowledge Index','index_key':key,
        'institute':room.institute,'classroom':room.name,'tenant_id':frappe.conf.il_tenant_id,'status':'New'}))
    if d.status=='Ready':return d
    if d.status=='Deleted':d.status='New';d.provider_store=None;save(d)
    if d.status!='New':frappe.throw('Course index requires reconciliation before retrying')
    d.status='Creating';save(d);frappe.db.commit()
    try:d.provider_store=adapter.create('sisu-'+key);d.status='Ready';save(d);frappe.db.commit();return d
    except Exception:
        d.status='Review';d.error_code='index_creation_unconfirmed';save(d);frappe.db.commit();raise

def index_document(document):
    with frappe.cache.lock('il_index_doc:'+document,timeout=420,blocking_timeout=1):
        d=frappe.get_doc('IL Knowledge Document',document)
        if d.status!='Queued' or not d.enabled:return
        previous=frappe.session.user;frappe.set_user(d.requested_by)
        try:
            context=authorize('ai.rag',d.classroom,teacher=True);inst,m,room=context
            if d.institute!=inst.name:frappe.throw('Foreign source')
            s=source(d.source_type,d.source_name,room,read=True)
            if s['revision']!=d.source_revision or hashlib.sha256(s['raw']).hexdigest()!=d.source_hash:raise ValueError('source_changed')
            from .ai_extract import extract,Unsupported
            try:rows=chunks(extract(s['filename'],s['raw']))
            except Unsupported:
                d.status='Unsupported';d.error_code='conversion_required';save(d);frappe.db.commit();return
            d.status='Extracting';save(d);frappe.db.commit()
            def work():
                from .ai_provider import retrieval
                adapter=retrieval();index=ensure_index(room,adapter);d.index=index.name
                text='\n\n'.join('['+r['section']+']\n'+r['text'] for r in rows)
                # Persist uncertain state before creating remote resources.
                d.status='Review';save(d);frappe.db.commit()
                d.provider_file=adapter.upload(index.provider_store,d.name,text,{});save(d);frappe.db.commit()
                adapter.attach(index.provider_store,d.provider_file,{'knowledge':d.name,'tenant':frappe.conf.il_tenant_id,'classroom':room.name})
                for n,row in enumerate(rows):save(frappe.get_doc({'doctype':'IL Knowledge Chunk','document':d.name,'ordinal':n,**row}))
                d.status='Indexing';save(d)
                return {'document':d.name,'status':'Indexing'}
            execute('ai.rag','ingest:'+d.name,{'hash':d.source_hash},context,work,'ingestion')
        except Exception:
            frappe.db.rollback();d=frappe.get_doc('IL Knowledge Document',document)
            if d.status not in ('Review','Indexing'):d.status='Failed'
            d.error_code='ingestion_failed_review_required';save(d);frappe.db.commit()
        finally:frappe.set_user(previous)

def current(d,room):
    source_policy(d.as_dict(),{'institute':room.institute,'classroom':room.name})
    s=source(d.source_type,d.source_name,room)
    if s['revision']!=d.source_revision:raise PermissionError('Source changed; reindex required')
    return s

def candidates(room,document=None):
    filters={'institute':room.institute,'classroom':room.name,'status':'Ready','enabled':1}
    if document:filters['name']=document
    result={}
    for name in frappe.get_all('IL Knowledge Document',filters=filters,pluck='name',limit_page_length=100):
        d=frappe.get_doc('IL Knowledge Document',name)
        try:current(d,room)
        except (PermissionError,frappe.PermissionError,frappe.DoesNotExistError):continue
        result[d.name]=d
    return result

def search_context(room,member,query,document=None):
    hosted_student(member)
    docs=candidates(room,document)
    if not docs:return []
    from .ai_provider import retrieval
    adapter=retrieval()
    index=frappe.get_doc('IL Knowledge Index',next(iter(docs.values())).index)
    if index.institute!=room.institute or index.classroom!=room.name or index.tenant_id!=frappe.conf.il_tenant_id or index.status!='Ready':frappe.throw('Course index unavailable')
    rows=adapter.search(index.provider_store,query,list(docs))
    by_file={d.provider_file:d for d in docs.values()};out=[];budget=18000
    for hit in rows[:8]:
        d=by_file.get(hit.get('file_id'))
        if not d:continue
        # Revalidate after provider work too; removed/replaced sources never enter LLM input.
        current(d,room)
        parts=frappe.get_all('IL Knowledge Chunk',filters={'document':d.name},fields=['section','text'],order_by='ordinal',limit_page_length=300)
        full=normalize(' '.join('['+p.section+'] '+p.text for p in parts))
        for content in hit.get('content',[]):
            excerpt=normalize(content.get('text',''))[:3500]
            if not excerpt or excerpt not in full or len(excerpt)>budget:continue
            section=next((p.section for p in parts if excerpt in normalize(p.text)), 'document')
            out.append(dict(id='S'+str(len(out)+1),document=d.name,version=d.version,material=d.source_name,source_type=d.source_type,
                classroom=room.name,title=d.title,section=section,excerpt=excerpt,score=hit.get('score')));budget-=len(excerpt)
            if len(out)>=8:return out
    return out

def disable_record(d):
    if not d.enabled and d.status in ('Disabled','Deleted'):return
    d.source_key=fingerprint(['retired',d.name,d.source_key])
    d.enabled=0;d.status='Disabled';d.delete_after=now_datetime();save(d)

@frappe.whitelist(methods=['POST'])
def deactivate(document):
    d=frappe.get_doc('IL Knowledge Document',document);inst,_,_=authorize('ai.rag',d.classroom,teacher=True)
    if d.institute!=inst.name:frappe.throw('Foreign source',frappe.PermissionError)
    disable_record(d);return {'disabled':True}

@frappe.whitelist()
def documents(classroom):
    inst,_,room=authorize('ai.rag',classroom,teacher=True)
    return frappe.get_all('IL Knowledge Document',filters={'institute':inst.name,'classroom':room.name},fields=['name','title','version','status','error_code','source_type','source_name','modified'],limit_page_length=100,order_by='creation desc')

@frappe.whitelist(methods=['POST'])
def reset_index(classroom,reason):
    inst,_,room=authorize('ai.rag',classroom,teacher=True)
    if not str(reason).strip():frappe.throw('Review reason required')
    # Fail closed locally before remote deletion; no automatic paid reindex.
    for name in frappe.get_all('IL Knowledge Document',filters={'classroom':room.name,'enabled':1},pluck='name'):
        disable_record(frappe.get_doc('IL Knowledge Document',name))
    frappe.db.commit()
    from .ai_provider import retrieval
    adapter=retrieval()
    for name in frappe.get_all('IL Knowledge Index',filters={'classroom':room.name,'institute':inst.name},pluck='name'):
        d=frappe.get_doc('IL Knowledge Index',name)
        if d.provider_store:adapter.delete_store(d.provider_store)
        d.status='Deleted';save(d)
    from .saas import audit
    audit('Reset course AI index',room.name,str(reason)[:500])
    return {'disabled':True,'next':'Explicitly ingest the current source materials again'}

def source_changed(doc,method=None):
    if getattr(frappe,'flags',{}).get('in_install') or getattr(frappe,'flags',{}).get('in_migrate'):return
    filters={'source_file':doc.name} if doc.doctype=='File' else {'source_type':doc.doctype,'source_name':doc.name}
    filters['enabled']=1
    for name in frappe.get_all('IL Knowledge Document',filters=filters,pluck='name'):
        d=frappe.get_doc('IL Knowledge Document',name)
        if doc.doctype=='File' and method=='on_trash':d.source_file=None
        disable_record(d)

def maintain():
    if frappe.conf.get('il_control_plane'):return
    from .ai_provider import retrieval
    try:adapter=retrieval(cleanup=True)
    except Exception:return
    for name in frappe.get_all('IL Knowledge Document',filters={'status':'Indexing','enabled':1},pluck='name',limit_page_length=20):
        d=frappe.get_doc('IL Knowledge Document',name);index=frappe.get_doc('IL Knowledge Index',d.index)
        try:
            result=adapter.poll(index.provider_store,d.provider_file)
            if result.get('status')=='completed':d.status='Ready';d.indexed_at=now_datetime();save(d)
            elif result.get('status') in ('failed','cancelled'):d.status='Failed';d.error_code='provider_index_failed';save(d)
        except Exception:d.status='Review';d.error_code='index_poll_unconfirmed';save(d)
    for name in frappe.get_all('IL Knowledge Document',filters={'enabled':0,'status':['!=','Deleted'],'cleanup_attempts':['<',10]},pluck='name',limit_page_length=20):
        d=frappe.get_doc('IL Knowledge Document',name);d.cleanup_attempts=int(d.cleanup_attempts or 0)+1
        try:
            index=frappe.get_doc('IL Knowledge Index',d.index) if d.index else None
            if d.provider_file:adapter.delete(index.provider_store if index else None,d.provider_file)
            for chunk in frappe.get_all('IL Knowledge Chunk',filters={'document':d.name},pluck='name'):
                frappe.db.delete('IL Knowledge Chunk',{'name':chunk})
            d.status='Deleted';d.provider_file=None;d.source_file=None;d.error_code=''
        except Exception:d.error_code='provider_cleanup_unconfirmed'
        save(d);frappe.db.commit()
