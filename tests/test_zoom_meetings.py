import sys,types,importlib,unittest
from datetime import datetime,timedelta
from unittest.mock import MagicMock,patch
class Row(dict):
    def __getattr__(self,k):return self.get(k)
class ZoomMeetings(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe')
        def throw(text,*args):raise ValueError(text)
        self.f.throw=throw;self.f.db=MagicMock();self.f.db.get_value.return_value=None
        self.f.conf={'il_zoom_server':{'provider':dict(account_id='acct',client_id='client',client_secret='secret',host_user='host@example.test')}}
        self.session=Row(name='lesson',classroom='class',meeting_provider='Zoom',mode='Online',starts_at=datetime.now()+timedelta(days=1),ends_at=datetime.now()+timedelta(days=1,hours=1),title='Class',meeting_url='')
        self.f.get_doc=MagicMock(return_value=self.session)
        api=types.ModuleType('institute_lms.api');api.classroom_for=MagicMock(return_value=(None,Row(user='teacher'),Row(name='class')))
        commercial=types.ModuleType('institute_lms.commercial');commercial.account_for=MagicMock(return_value=Row(name='provider'));commercial.require_room=MagicMock();commercial.locked=MagicMock()
        workspace=types.ModuleType('institute_lms.workspace');workspace.record=MagicMock();workspace.DT='IL Workspace Record';self.workspace=workspace
        utils=types.ModuleType('frappe.utils');utils.now_datetime=datetime.now;utils.get_datetime=lambda x:x
        self.old=sys.modules.pop('institute_lms.zoom_meetings',None)
        self.p=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':utils,'institute_lms.api':api,'institute_lms.commercial':commercial,'institute_lms.workspace':workspace});self.p.start()
        self.mod=importlib.import_module('institute_lms.zoom_meetings')
    def tearDown(self):
        sys.modules.pop('institute_lms.zoom_meetings',None)
        if self.old:sys.modules['institute_lms.zoom_meetings']=self.old
        self.p.stop()
    def test_secure_creation_never_exposes_host_start_url(self):
        token=MagicMock(status_code=200);token.json.return_value={'access_token':'test-token'}
        meeting=MagicMock(status_code=201);meeting.json.return_value={'id':123,'join_url':'https://zoom.us/j/123?pwd=token','start_url':'https://zoom.us/secret-host'}
        with patch('requests.post',side_effect=[token,meeting]) as post:
            value=self.mod.create('lesson')
            payload=post.call_args.kwargs['json'];self.assertTrue(payload['settings']['waiting_room']);self.assertFalse(payload['settings']['join_before_host']);self.assertGreaterEqual(len(payload['password']),10)
        self.assertNotIn('start_url',value);self.assertNotIn('secret-host',str(self.workspace.record.call_args_list));self.f.db.commit.assert_called_once()
    def test_pending_request_blocks_duplicate_remote_creation(self):
        self.f.db.get_value.return_value='intent';self.f.get_doc.side_effect=[self.session,Row(payload='{"state":"Pending"}')]
        with patch('requests.post') as post:
            with self.assertRaisesRegex(ValueError,'reconciliation'):self.mod.create('lesson')
            post.assert_not_called()
    def test_missing_provider_credentials_does_not_contact_zoom(self):
        self.f.conf={}
        with patch('requests.post') as post:
            with self.assertRaisesRegex(ValueError,'Connect'):self.mod.create('lesson')
            post.assert_not_called()
