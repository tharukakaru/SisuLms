import ast,types,unittest,sys
from pathlib import Path
from unittest.mock import patch,MagicMock
ROOT=Path(__file__).resolve().parents[1]/'institute_lms'
class Row(dict):
    __getattr__=dict.get

def function(file,name,env):
    tree=ast.parse((ROOT/file).read_text(encoding='utf8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    node.decorator_list=[]
    exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),env)
    return env[name]

class ProviderScope(unittest.TestCase):
    def test_teacher_scope_excludes_institute_owned_classes(self):
        f=function('learning_spaces.py','filters_for',{'provider':lambda n:Row(kind='Teacher'),'class_filters':lambda p,i:{'institute':'I','teacher':['in',['T']]}})
        self.assertEqual(f('P',None),{'institute':'I','teacher':['in',['T']],'owner_type':'Teacher'})
    def test_institute_scope_keeps_provider_boundary(self):
        f=function('learning_spaces.py','filters_for',{'provider':lambda n:Row(kind='Institute'),'class_filters':lambda p,i:{'institute':'I','public_provider':'P'}})
        self.assertEqual(f('P',None)['public_provider'],'P')
    def test_pending_slip_does_not_claim_paid_or_unlock(self):
        api=types.ModuleType('institute_lms.api');api.access=lambda r,m:{'allowed':False,'reason':'Unpaid'}
        room=Row(name='C',title='Test',teacher='T',fee=100,fee_mode='Paid')
        enrollment=Row(name='E')
        def get_value(dt,*args,**kw):return 'E' if dt=='IL Enrollment' else 'Teacher'
        def exists(dt,filters):return dt=='IL Bank Slip'
        f=types.SimpleNamespace(db=types.SimpleNamespace(get_value=get_value,exists=exists),get_doc=lambda dt,n:room if dt=='IL Classroom' else enrollment,get_all=lambda dt,**kw:['C'] if dt=='IL Classroom' else ['invoice'])
        env={'__package__':'institute_lms','frappe':f,'identity':lambda:(Row(name='I'),Row(name='S',role='Student')),'require_role':lambda m,r:None,'filters_for':lambda p,i:{'institute':'I'}}
        fn=function('learning_spaces.py','classes',env)
        with patch.dict(sys.modules,{'institute_lms.api':api}):
            row=fn('P')['classes'][0]
        self.assertEqual(row['state'],'pending');self.assertFalse(row['payment_approved'])

class NotificationScope(unittest.TestCase):
    def test_user_institute_and_profile_are_bound_parameters(self):
        api=types.ModuleType('institute_lms.api');api.identity=lambda:(Row(name='I'),Row(name='S'))
        spaces=types.ModuleType('institute_lms.learning_spaces');spaces.notification_rooms=lambda p,i:["C' OR 1=1 --"]
        db=MagicMock();db.sql.return_value=[]
        f=types.SimpleNamespace(db=db,session=Row(user='student@example.invalid'))
        fn=function('notification_service.py','inbox',{'frappe':f,'__package__':'institute_lms'})
        with patch.dict(sys.modules,{'institute_lms.api':api,'institute_lms.learning_spaces':spaces}):fn(profile='P')
        sql,params=db.sql.call_args.args
        self.assertIn('e.user=%s AND e.institute=%s',sql)
        self.assertIn('e.classroom IN %s',sql)
        self.assertNotIn("OR 1=1 --",sql)
        self.assertEqual(params[:2],('student@example.invalid','I'))
        self.assertEqual(params[3],("C' OR 1=1 --",))

class ReviewAuthority(unittest.TestCase):
    def test_teaching_access_alone_cannot_approve_money(self):
        from institute_lms.teaching_rules import capabilities
        room=Row(institute='I',owner_type='Institute',teacher='T',teacher_assignment_active=1,teacher_access='Teaching only')
        m=Row(name='T',user='teacher',role='Teacher')
        api=types.ModuleType('institute_lms.api');api.classroom_for=lambda *a:(Row(name='I'),m,room)
        teaching=types.ModuleType('institute_lms.teaching')
        def require(r,member,action):
            if not capabilities(r,member).get(action):raise PermissionError('Fee management required')
        teaching.require=require
        f=types.SimpleNamespace(PermissionError=PermissionError,throw=lambda *a:(_ for _ in ()).throw(PermissionError()))
        fn=function('commercial.py','reviewer',{'__package__':'institute_lms','frappe':f,'account_for':lambda *a:None,'locked_reason':lambda a:None})
        with patch.dict(sys.modules,{'institute_lms.api':api,'institute_lms.teaching':teaching}):
            with self.assertRaises(PermissionError):fn(Row(institute='I',classroom='C'))
            m['role']='Admin'
            self.assertEqual(fn(Row(institute='I',classroom='C'))[1].role,'Admin')

if __name__=='__main__':unittest.main()
