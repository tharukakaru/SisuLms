import json
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock
from test_upload_provisioning import function
class FollowStatus(TestCase):
    def setUp(self):
        self.db=Mock(return_value=[]);self.auth=Mock()
        def fail(message):raise ValueError(message)
        self.f=function('profiles','follow_status',{'signed_in':self.auth,'json':json,'frappe':NS(get_all=self.db,session=NS(user='current-user'),throw=fail)})
    def test_only_current_users_active_follows(self):
        self.f('["provider"]')
        self.auth.assert_called_once()
        self.assertEqual(self.db.call_args.kwargs['filters'],{'profile':['in',['provider']],'user':'current-user','kind':'Follow','status':'Active'})
    def test_rejects_unbounded_or_invalid_input(self):
        for value in ('bad','{}',['x']*25,[None],['']):
            with self.assertRaises(ValueError):self.f(value)
        self.db.assert_not_called()
    def test_empty_page_never_queries_all_relationships(self):
        self.assertEqual(self.f([]),[]);self.db.assert_not_called()
