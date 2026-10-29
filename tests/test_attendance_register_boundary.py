import ast,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from datetime import datetime,timedelta
source=Path(__file__).resolve().parents[1]/'institute_lms/attendance_register.py'
tree=ast.parse(source.read_text(encoding='utf-8-sig'))
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
for n in functions:n.decorator_list=[]
class Denied(Exception):pass
class Tests(unittest.TestCase):
 def setUp(self):
  self.writes=[];self.checks=[]
  self.meeting=NS(institute='i',classroom='c',status='Scheduled',starts_at=datetime(2026,1,1),name='s')
  self.room=NS(institute='i',name='c')
  def deny(message,*args):raise Denied(message)
  def exists(dt,filters):self.checks.append(filters);return filters['name']!='foreign' if dt=='IL Member' else True
  self.env={'json':__import__('json'),'frappe':NS(get_doc=lambda *a:self.meeting,throw=deny,PermissionError=Denied,db=NS(exists=exists)),
    'classroom_for':lambda *a,**k:(NS(name='i'),NS(role='Teacher'),self.room),
    'get_datetime':lambda x:x,'now_datetime':lambda:datetime(2026,1,2),'record':lambda *a:self.writes.append(a)}
  exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),self.env)
 def test_reject_duplicate(self):
  with self.assertRaises(ValueError):self.env['validate_entries']([{'student':'a','status':'Present'}]*2)
 def test_requires_explicit_status(self):
  with self.assertRaises(ValueError):self.env['validate_entries']([{'student':'a','status':''}])
 def test_session_not_started(self):
  self.meeting.starts_at=datetime(2026,1,3)
  with self.assertRaises(Denied):self.env['context']('s')
 def test_foreign_session(self):
  self.meeting.institute='other'
  with self.assertRaises(Denied):self.env['context']('s')
 def test_cancelled_session(self):
  self.meeting.status='Cancelled'
  with self.assertRaises(Denied):self.env['context']('s')
 def test_teaching_permission_enforced(self):
  def blocked(*a,**k):raise Denied('Forbidden')
  self.env['classroom_for']=blocked
  with self.assertRaises(Denied):self.env['roster']('s')
 def test_entire_page_validated_before_writes(self):
  with self.assertRaises(Denied):self.env['submit']('s',[{'student':'a','status':'Present'},{'student':'foreign','status':'Present'}])
  self.assertEqual(self.writes,[])
 def test_ended_session_editable(self):
  self.meeting.status='Completed'
  result=self.env['submit']('s',[{'student':'a','status':'Absent'}])
  self.assertEqual(result,{'saved':1});self.assertEqual(self.writes[0][3],'Absent')
if __name__=='__main__':unittest.main()
