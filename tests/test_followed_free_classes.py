from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock
from test_upload_provisioning import function
class FollowedFreeClasses(TestCase):
    def setUp(self):
        def fail(message):raise ValueError(message)
        self.db=Mock();self.auth=Mock()
        self.f=function('profiles','followed_free_classes',{'signed_in':self.auth,'frappe':NS(db=self.db,session=NS(user='student@example.invalid'),throw=fail)})
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
