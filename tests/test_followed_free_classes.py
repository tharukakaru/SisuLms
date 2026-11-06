from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock,patch
from test_upload_provisioning import function
class FollowedFreeClasses(TestCase):
    def setUp(self):
        def fail(message):raise ValueError(message)
        self.db=Mock();self.auth=Mock()
        self.db.sql.return_value=[]
        self.mod=patch.dict('sys.modules',{'institute_lms.demo_learning':NS(decorate=lambda rows:rows)});self.mod.start();self.addCleanup(self.mod.stop)
        base=function('profiles','followed_classes',{'signed_in':self.auth,'frappe':NS(db=self.db,session=NS(user='student@example.invalid'),throw=fail)})
        self.f=function('profiles','followed_free_classes',{'followed_classes':base})
        self.all=base
    def test_public_free_cards_bound_to_current_follow(self):
        self.f(1)
        self.auth.assert_called_once()
        sql,args=self.db.sql.call_args.args
        self.assertEqual(args,('student@example.invalid',25))
        for predicate in ("c.active=1","c.published=1","c.fee_mode='Free'","c.fee=0","r.kind='Follow'","r.status='Active'","c.owner_user=p.user","c.institute=p.workspace"):
            self.assertIn(predicate,sql)
        self.assertNotIn('file_id',sql)
    def test_invalid_pages_do_not_query(self):
        for page in (-1,10001,'bad'):
            with self.assertRaises(ValueError):self.f(page)
        self.db.sql.assert_not_called()
    def test_followed_institute_includes_active_teachers_classes_and_locked_cards(self):
        self.all()
        sql,args=self.db.sql.call_args.args
        self.assertIn('t.name=c.teacher',sql)
        self.assertIn('i.workspace=c.institute',sql)
        self.assertIn('t.active=1',sql)
        self.assertNotIn("AND c.fee_mode='Free'",sql)
        self.assertEqual(args,('student@example.invalid',0))
