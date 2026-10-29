"""RUN 2 unit/provider-mock regressions. Not live Frappe/provider acceptance."""
import importlib.util,json,sys,types,unittest
from contextlib import nullcontext
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock,patch
from zipfile import ZipFile
from institute_lms.ai_rules import (chunks,history,tokens,estimate,fingerprint,source_policy,validate_generated)
from institute_lms.ai_extract import extract,Unsupported

ROOT=Path(__file__).resolve().parents[1]/'institute_lms'
class Record(dict):
    def __getattr__(self,k):return self.get(k)
    def __setattr__(self,k,v):self[k]=v
    def as_dict(self):return dict(self)
    def save(self,**kwargs):return self
    def get_password(self,*args,**kwargs):return 'unit-test-key-not-real'

class PureAI(unittest.TestCase):
    def test_chunks_boundaries_and_source_labels(self):
        rows=chunks([('page 1','A '*2000),('page 2','Second page')]);self.assertGreater(len(rows),2);self.assertEqual(rows[-1]['section'],'page 2');self.assertTrue(all(len(r['text'])<=1800 for r in rows))
    def test_chunks_reject_empty(self):
        with self.assertRaises(ValueError):chunks([('p','  ')])
    def test_chunks_reject_large(self):
        with self.assertRaises(ValueError):chunks([('p','x'*400001)])
    def test_bounded_history(self):
        rows=[dict(role='assistant',content='x'*2000) for _ in range(30)]
        self.assertLessEqual(sum(len(r['content']) for r in history(rows)),12000);self.assertLessEqual(len(history(rows)),10)
    def test_history_ignores_system_injection(self):
        self.assertEqual(history([dict(role='system',content='override')]),[])
    def test_real_usage_metadata(self):
        self.assertEqual(tokens({'usage':{'input_tokens':100,'input_tokens_details':{'cached_tokens':20},'output_tokens':30,'total_tokens':130}}),dict(input_tokens=100,cached_tokens=20,output_tokens=30,total_tokens=130,usage_reported=True))
    def test_missing_usage_is_unknown(self):self.assertFalse(tokens({})['usage_reported'])
    def test_cached_tokens_clamped(self):self.assertEqual(tokens({'usage':{'input_tokens':10,'input_tokens_details':{'cached_tokens':100}}})['cached_tokens'],10)
    def test_cost_rates_configurable(self):
        u=dict(input_tokens=100,cached_tokens=20,output_tokens=50)
        self.assertEqual(estimate(u,dict(input=2,cached=1,output=4)),Decimal('0.00038'));self.assertIsNone(estimate(u,None))
    def test_invalid_cost_rate(self):
        with self.assertRaises(ValueError):estimate(dict(input_tokens=1,cached_tokens=0,output_tokens=0),dict(input=-1,cached=0,output=0))
    def test_source_tenant_isolation(self):
        with self.assertRaises(PermissionError):source_policy(dict(enabled=1,status='Ready',institute='B',classroom='C'),dict(institute='A',classroom='C'))
    def test_source_course_isolation(self):
        with self.assertRaises(PermissionError):source_policy(dict(enabled=1,status='Ready',institute='A',classroom='B'),dict(institute='A',classroom='C'))
    def test_disabled_source_denied(self):
        with self.assertRaises(PermissionError):source_policy(dict(enabled=0,status='Ready',institute='A',classroom='C'),dict(institute='A',classroom='C'))
    def test_supported_source(self):source_policy(dict(enabled=1,status='Ready',institute='A',classroom='C'),dict(institute='A',classroom='C'))
    def test_flashcards_validated(self):
        value={'cards':[{'front':'What?','back':'Answer','source':'S1'}]};self.assertEqual(validate_generated(value,'flashcards',['S1']),value)
    def test_fabricated_card_citation_rejected(self):
        with self.assertRaises(ValueError):validate_generated({'cards':[{'front':'Q','back':'A','source':'S2'}]},'flashcards',['S1'])
    def test_question_schema(self):
        q=dict(kind='MCQ',prompt='One plus one?',options=['1','2'],answer=1,marks=1,source='S1')
        self.assertEqual(validate_generated({'questions':[q]},'questions',['S1'])['questions'][0]['answer'],1)
    def test_question_answer_bounds(self):
        with self.assertRaises(ValueError):validate_generated({'questions':[dict(kind='MCQ',prompt='Q',options=['A','B'],answer=8,marks=1,source='S1')]},'questions',['S1'])
    def test_true_false_and_written(self):
        for kind,answer in [('True/False',0),('Written',None)]:
            self.assertEqual(validate_generated({'questions':[dict(kind=kind,prompt='Q',options=[],answer=answer,marks=1,source='S1')]},'questions',['S1'])['questions'][0]['kind'],kind)
    def test_unsubstantiated_answer_is_explicit(self):
        r=validate_generated(dict(answer='Invented fact',supported=True,citations=[]),'answer',['S1']);self.assertFalse(r['supported']);self.assertNotIn('Invented',r['answer'])
    def test_unknown_citation_rejected(self):
        with self.assertRaises(ValueError):validate_generated(dict(answer='A',supported=True,citations=['invented']),'answer',['S1'])
    def test_plain_text(self):self.assertEqual(extract('notes.txt',b'Course notes'),[('text','Course notes')])
    def office(self,kind,xml):
        out=BytesIO()
        with ZipFile(out,'w') as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/document.xml' if kind=='docx' else 'ppt/presentation.xml',xml if kind=='docx' else '<p/>')
            if kind=='pptx':z.writestr('ppt/slides/slide1.xml',xml)
        return out.getvalue()
    def test_docx_extraction(self):
        raw=self.office('docx','<w:document xmlns:w="word"><w:t>Algebra lesson</w:t></w:document>');self.assertEqual(extract('a.docx',raw)[0][1],'Algebra lesson')
    def test_pptx_extraction(self):
        raw=self.office('pptx','<a:slide xmlns:a="slide"><a:t>Triangles</a:t></a:slide>');self.assertEqual(extract('a.pptx',raw),[('slide 1','Triangles')])
    def test_legacy_formats_conversion_required(self):
        for suffix in ('doc','ppt','exe'):
            with self.assertRaises(Unsupported):extract('a.'+suffix,b'not executable')
    def test_xml_entities_rejected(self):
        raw=self.office('docx','<!DOCTYPE x [<!ENTITY e SYSTEM "file:///private">]><w:document xmlns:w="word"><w:t>&e;</w:t></w:document>')
        with self.assertRaises(Exception):extract('a.docx',raw)
    def test_pdf_extraction(self):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        w=PdfWriter();p=w.add_blank_page(width=300,height=300)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        p[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
        stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 20 100 Td (Learning algebra) Tj ET');p[NameObject('/Contents')]=stream
        out=BytesIO();w.write(out);self.assertIn('Learning algebra',extract('a.pdf',out.getvalue())[0][1])
    def test_weakness_uses_actual_wrong_answers(self):
        # Import the pure function without bringing in a live Frappe runtime.
        import ast
        tree=ast.parse((ROOT/'ai_insights.py').read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='weakness_evidence');env={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'ai_insights.py','exec'),env)
        qs=[dict(kind='MCQ',prompt='Quadratic equation',answer=1),dict(kind='Written',prompt='Explain',answer=None)]
        self.assertEqual(len(env['weakness_evidence'](qs,[0,'text'],'P','A')),1);self.assertEqual(env['weakness_evidence'](qs,[1,'text'],'P','A'),[])

class ServiceAI(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda f:f
        self.f.PermissionError=PermissionError;self.f.DoesNotExistError=LookupError
        self.f.throw=lambda msg,kind=ValueError:(_ for _ in ()).throw(kind(msg))
        self.f.conf=Record(il_tenant_id='T',il_ai_hosted_student_reviewed=1);self.f.session=Record(user='u');self.f.local=Record(site='tenant.example.invalid')
        self.f.db=MagicMock();self.f.db.sql.return_value=[];self.f.db.exists.return_value=True
        self.f.get_doc=MagicMock();self.f.get_all=MagicMock(return_value=[]);self.f.enqueue=MagicMock();self.f.set_user=MagicMock()
        self.f.cache=MagicMock();self.f.cache.lock=lambda *a,**kw:nullcontext();self.f.cache.get_value.return_value=0
        u=types.ModuleType('frappe.utils');u.now_datetime=lambda:datetime(2026,10,2,12);u.get_datetime=lambda v:datetime.fromisoformat(str(v))
        self.modules=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':u});self.modules.start();self.addCleanup(self.modules.stop)
        self.inst=Record(name='I');self.member=Record(name='M',role='Student',user='u');self.room=Record(name='C',institute='I',active=1,lms_course='LC')
        self.fake('saas',require=MagicMock(),managed=lambda d:d,state=MagicMock(return_value=Record(name='SUB',tenant_id='T')))
        self.fake('soul',student_ready=lambda m:True)
    def fake(self,name,**attrs):
        m=types.ModuleType('institute_lms.'+name);m.__dict__.update(attrs);sys.modules[m.__name__]=m;return m
    def load(self,name):
        key='institute_lms.'+name;sys.modules.pop(key,None);spec=importlib.util.spec_from_file_location(key,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m);return m
    def access(self):
        self.api=self.fake('api',identity=lambda:(self.inst,self.member),classroom_for=MagicMock(return_value=(self.inst,self.member,self.room)),accessible_room=MagicMock(return_value=(self.inst,self.member,self.room)))
        self.fake('retention',access_allowed=lambda d:True);return self.load('ai_access')
    def test_starter_denied_before_course_or_provider(self):
        a=self.access();sys.modules['institute_lms.saas'].require.side_effect=PermissionError('denied')
        with self.assertRaises(PermissionError):a.authorize('ai.rag','C')
        self.api.accessible_room.assert_not_called()
    def test_authorized_teacher(self):
        a=self.access();self.member.role='Teacher';a.authorize('ai.teacher','C',teacher=True);self.api.classroom_for.assert_called_once_with('C',write=True)
    def test_student_cannot_index(self):
        a=self.access()
        with self.assertRaises(PermissionError):a.authorize('ai.rag','C',teacher=True)
    def test_unpaid_unenrolled_denied(self):
        a=self.access();self.api.accessible_room.side_effect=PermissionError('payment')
        with self.assertRaises(PermissionError):a.authorize('ai.rag','C')
    def test_foreign_tenant_course_denied(self):
        a=self.access();self.room.institute='OTHER'
        with self.assertRaises(PermissionError):a.authorize('ai.rag','C')
    def test_control_plane_cannot_access_private_data(self):
        a=self.access();self.f.conf.il_control_plane=1
        with self.assertRaises(PermissionError):a.authorize('ai.rag','C')
    def test_operator_not_a_membership(self):
        a=self.access();self.member.name=None
        with self.assertRaises(PermissionError):a.authorize('ai.rag','C')
    def test_admin_is_not_conversation_owner(self):
        a=self.access();self.member.role='Admin';self.f.get_doc.return_value=Record(user='other',institute='I',classroom='C',status='Active')
        with self.assertRaises(PermissionError):a.owned_conversation('private')
    def test_own_conversation_allowed(self):
        a=self.access();self.f.get_doc.return_value=Record(user='u',institute='I',classroom='C',status='Active');self.assertEqual(a.owned_conversation('mine')[0].user,'u')
    def test_student_admin_insights_denied(self):
        a=self.access()
        with self.assertRaises(PermissionError):a.authorize('ai.analytics','C',admin=True)
    def accounting(self):
        self.personal_credits=self.fake('ai_credits',enforce=MagicMock())
        self.ledger=self.fake('usage',consume=MagicMock(),period=lambda r:'2026-10')
        self.settings=Record(enabled=1,model='configured-model',feature_credits='{}',model_rates='{}')
        self.provider=self.fake('ai_provider',config=lambda:(self.settings,'secret'),settings=lambda:self.settings,ProviderError=type('ProviderError',(RuntimeError,),{}))
        a=self.load('ai_accounting');a.rate_limit=MagicMock();self.stored={}
        def doc(*args,**kwargs):
            if isinstance(args[0],dict):
                d=Record(args[0]);d.flags=Record();d.name='USAGE';self.stored[d.name]=d;return d
            return self.stored[args[1]]
        self.f.get_doc.side_effect=doc
        return a
    def test_allowance_exhausted_before_provider(self):
        a=self.accounting();self.ledger.consume.side_effect=ValueError('exhausted');work=MagicMock()
        with self.assertRaises(ValueError):a.execute('ai.notes','request-123',{},(self.inst,self.member,self.room),work)
        work.assert_not_called()
    def test_usage_recorded_and_retry_does_not_charge_twice(self):
        a=self.accounting()
        def work():a.started();a.receipt({'usage':{'input_tokens':30,'output_tokens':5,'total_tokens':35}},'configured-model','responses');return {'answer':'ok'}
        self.assertEqual(a.execute('ai.notes','request-123',{},(self.inst,self.member,self.room),work)['answer'],'ok')
        d=self.stored['USAGE'];self.assertEqual(d.total_tokens,35);self.assertEqual(d.charged_units,1);self.assertEqual(d.period,'2026-10')
        self.f.db.sql.return_value=[('USAGE',)];work2=MagicMock()
        a.execute('ai.notes','request-123',{},(self.inst,self.member,self.room),work2);work2.assert_not_called();self.assertEqual(self.ledger.consume.call_count,1)
    def test_ambiguous_failure_retains_charge(self):
        a=self.accounting()
        def work():a.started();raise self.provider.ProviderError('timeout')
        with self.assertRaises(ValueError):a.execute('ai.notes','request-123',{},(self.inst,self.member,self.room),work)
        self.assertEqual(self.stored['USAGE'].state,'Review');self.assertEqual(self.stored['USAGE'].charged_units,1)
    def test_pre_provider_failure_releases_credit(self):
        a=self.accounting();saved=[]
        original=self.f.get_doc.side_effect
        def doc(*args,**kw):
            if isinstance(args[0],dict) and args[0]['doctype']=='IL Usage Entry':saved.append(args[0]);return Record(args[0])
            return original(*args,**kw)
        self.f.get_doc.side_effect=doc
        with self.assertRaises(ValueError):a.execute('ai.notes','request-123',{},(self.inst,self.member,self.room),lambda:(_ for _ in ()).throw(ValueError('bad input')))
        self.assertEqual(saved[0]['quantity'],-1);self.assertEqual(self.stored['USAGE'].state,'Released')
    def test_reused_id_with_different_input_rejected(self):
        a=self.accounting();a.execute('ai.notes','request-123',{'x':1},(self.inst,self.member,self.room),lambda:{})
        self.f.db.sql.return_value=[('USAGE',)]
        with self.assertRaises(ValueError):a.execute('ai.notes','request-123',{'x':2},(self.inst,self.member,self.room),MagicMock())
    def knowledge(self):
        self.fake('ai_accounting',save=lambda d:d,execute=MagicMock());self.fake('ai_access',authorize=lambda *a,**kw:(self.inst,self.member,self.room),hosted_student=lambda m:None)
        return self.load('knowledge')
    def test_material_other_course_rejected(self):
        k=self.knowledge();self.f.get_doc.return_value=Record(institute='I',classroom='B')
        with self.assertRaises(PermissionError):k.source('IL Material','D',self.room)
    def test_arbitrary_source_type_rejected(self):
        k=self.knowledge()
        with self.assertRaises(ValueError):k.source('User','u',self.room)
    def test_changed_source_rejects_ready_index(self):
        k=self.knowledge();k.source=lambda *a,**kw:dict(revision='new')
        d=Record(enabled=1,status='Ready',institute='I',classroom='C',source_type='IL Material',source_name='M',source_revision='old')
        with self.assertRaises(PermissionError):k.current(d,self.room)
    def test_duplicate_unchanged_ingestion_no_job(self):
        k=self.knowledge();self.fake('ai_provider',retrieval=lambda:None,settings=lambda:Record());sys.modules['institute_lms.ai_accounting'].rate_limit=lambda *a:None
        k.source=lambda *a,**kw:dict(raw=b'unchanged',revision='R');self.f.db.sql.side_effect=[[],[('D','Ready')]]
        self.assertTrue(k.ingest('C','IL Material','M')['unchanged']);self.f.enqueue.assert_not_called()
    def test_changed_version_queues_new_job(self):
        k=self.knowledge();self.fake('ai_provider',retrieval=lambda:None,settings=lambda:Record(max_documents_per_course=100));sys.modules['institute_lms.ai_accounting'].rate_limit=lambda *a:None
        k.source=lambda *a,**kw:dict(raw=b'changed',revision='new',file='F',title='Lesson',filename='a.txt')
        self.f.db.count.return_value=1;self.f.db.sql.return_value=[]
        self.f.get_doc.side_effect=lambda data:Record(dict(data,name='DNEW'))
        result=k.ingest('C','IL Material','M');self.assertEqual(result['document'],'DNEW');self.assertEqual(result['status'],'Queued');self.f.enqueue.assert_called_once()
    def test_unsupported_worker_never_calls_provider(self):
        k=self.knowledge();d=Record(name='D',status='Queued',enabled=1,requested_by='u',classroom='C',institute='I',source_type='IL Material',source_name='M',source_revision='R',source_hash=__import__('hashlib').sha256(b'legacy').hexdigest())
        self.f.get_doc.return_value=d;k.source=lambda *a,**kw:dict(raw=b'legacy',filename='a.doc',revision='R')
        k.index_document('D');self.assertEqual(d.status,'Unsupported');sys.modules['institute_lms.ai_accounting'].execute.assert_not_called()
    def test_deleted_source_does_not_become_candidate(self):
        k=self.knowledge();self.f.get_all.return_value=['D'];self.f.get_doc.return_value=Record(name='D');k.current=MagicMock(side_effect=LookupError('deleted'))
        self.assertEqual(k.candidates(self.room),{})
    def test_disabled_source_retired_for_reindex(self):
        k=self.knowledge();d=Record(name='D',source_key='old',enabled=1,status='Ready');k.disable_record(d)
        self.assertEqual(d.status,'Disabled');self.assertFalse(d.enabled);self.assertNotEqual(d.source_key,'old')
    def test_source_deletion_hook_disables_knowledge(self):
        k=self.knowledge();self.f.get_all.return_value=['D'];d=Record(name='D',enabled=1,status='Ready',source_key='old');self.f.get_doc.return_value=d
        k.source_changed(Record(doctype='IL Material',name='M'),'on_trash');self.assertFalse(d.enabled)
    def test_search_filters_out_foreign_provider_file(self):
        k=self.knowledge();d=Record(name='D',index='X',provider_file='file-own');k.candidates=lambda *a:{'D':d}
        adapter=MagicMock();adapter.search.return_value=[dict(file_id='file-foreign',content=[dict(text='private other course')])]
        self.fake('ai_provider',retrieval=lambda:adapter);self.f.get_doc.return_value=Record(institute='I',classroom='C',tenant_id='T',status='Ready',provider_store='vs_x')
        self.assertEqual(k.search_context(self.room,self.member,'question'),[]);self.assertEqual(adapter.search.call_args.args[2],['D'])
    def feature_api(self):
        self.fake('ai_access',authorize=lambda *a,**kw:(self.inst,self.member,self.room),owned_conversation=MagicMock())
        self.fake('ai_accounting',save=lambda d:d,execute=lambda f,k,p,c,op,*a:op())
        self.fake('ai_provider',settings=lambda:Record(model='configured',max_output_tokens=1000))
        a=self.load('ai');a.sources_for=lambda *args:[dict(id='S1',document='D',excerpt='Learning content',version=1)];a.recheck_sources=MagicMock();return a
    def test_summary_and_notes_use_source_and_correct_feature(self):
        a=self.feature_api();a.generate_result=MagicMock(return_value={'answer':'draft'})
        for kind in ('summary','notes'):
            self.assertEqual(a.feature(kind,'C')['answer'],'draft');self.assertEqual(a.generate_result.call_args.args[0],kind)
    def test_assignment_feedback_cannot_be_requested_by_student(self):
        a=self.feature_api();self.f.get_doc.return_value=Record(paper='P')
        self.fake('papers',checked=MagicMock(side_effect=PermissionError('teacher required')))
        with self.assertRaises(PermissionError):a.assignment_feedback('A','request-123')
    def test_admin_aggregate_suppresses_small_cohort(self):
        a=self.load('ai_insights');self.f.db.sql.return_value=[Record(students=2,attempts=2)]
        self.assertFalse(a.aggregates(self.room)['sufficient_data']);self.assertEqual(self.f.db.sql.call_count,1)
    def test_insufficient_recommendation_evidence(self):
        a=self.load('ai_insights');self.f.db.sql.return_value=[]
        self.assertFalse(a.recommendations_for(self.inst,self.member,self.room)['sufficient_evidence'])
    def test_provider_uses_responses_store_false(self):
        p=self.load('ai_provider');p.config=lambda:(Record(model='configured',max_output_tokens=500),'secret');p.moderate=MagicMock()
        p.request=MagicMock(return_value={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'{"answer":"ok"}'}]}]})
        p.generate('question',{'type':'object'});body=p.request.call_args.args[2]
        self.assertFalse(body['store']);self.assertNotIn('tools',body);self.assertEqual(p.request.call_args.args[1],'responses')
    def test_hosted_adapter_filters_each_allowed_document(self):
        p=self.load('ai_provider');p.request=MagicMock(return_value={'data':[]});p.OpenAIRetrieval().search('vs_test','q',['D1','D2'])
        body=p.request.call_args.args[2];self.assertEqual([r['value'] for r in body['filters']['filters']],['D1','D2'])
    def test_provider_file_id_formats_are_bounded(self):
        p=self.load('ai_provider')
        for name in ('file_abc123','file-abc123'):self.assertEqual(p.identifier(name,'file[-_]'),name)
        with self.assertRaises(ValueError):p.identifier('file_abc/../../secret','file[-_]')
    def test_semantic_search_authorization_precedes_retrieval(self):
        a=self.feature_api();a.authorize=MagicMock(side_effect=PermissionError('foreign course'))
        k=self.fake('knowledge',search_context=MagicMock(),candidates=MagicMock())
        with self.assertRaises(PermissionError):a.search('foreign','q','request-123')
        k.search_context.assert_not_called()
    def test_ai_quiz_preserves_explicit_publication_review(self):
        import ast
        tree=ast.parse((ROOT/'papers.py').read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='publish');fn.decorator_list=[]
        d=Record(status='Draft');save=MagicMock()
        env={'frappe':self.f,'checked':lambda *a:(d,None,None),'validate_questions':MagicMock(),'json':json,'now_datetime':lambda:datetime.now(),'save':save}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'papers.py','exec'),env)
        with self.assertRaises(ValueError):env['publish']('P',False)
        save.assert_not_called()

if __name__=='__main__':unittest.main()
