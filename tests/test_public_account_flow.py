import hashlib
from html import escape
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock
from test_upload_provisioning import function

class PublicAccountFlowTests(TestCase):
    def test_google_existing_account_requires_matching_authenticated_identity(self):
        f=NS(session=NS(user='student',data={'il_google_session':True}),db=NS(get_value=Mock(return_value=1)))
        predicate=function('public_signup','google_identity',dict(frappe=f,enabled=lambda:True))
        self.assertTrue(predicate('student'))
        self.assertFalse(predicate('someone-else'))
        f.session.data={};self.assertFalse(predicate('student'))
    def test_confirmation_only_enqueues_after_commit(self):
        doc=Mock();f=NS(local=NS(site='sisuacademylk.com'),db=NS(exists=Mock(return_value=False)),get_doc=Mock(return_value=doc),enqueue=Mock())
        queue=function('account_confirmations','queue',dict(frappe=f,hashlib=hashlib,escape=escape))
        queue('student','registration:ST-001','Registered','Saved')
        doc.insert.assert_called_once()
        self.assertTrue(f.enqueue.call_args.kwargs['enqueue_after_commit'])
        self.assertNotIn('phone',f.enqueue.call_args.kwargs)
        f.db.exists.return_value=True;queue('student','registration:ST-001','Registered','Saved')
        self.assertEqual(f.enqueue.call_count,1)
    def test_nonpublic_confirmation_does_not_send(self):
        f=NS(local=NS(site='sandbox'),enqueue=Mock())
        queue=function('account_confirmations','queue',dict(frappe=f,hashlib=hashlib,escape=escape))
        queue('student','one','Saved','Saved');f.enqueue.assert_not_called()
