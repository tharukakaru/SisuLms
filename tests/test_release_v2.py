"""V2 contract/security regressions. Frappe doubles, not live DB/provider acceptance."""
import unittest,types,json
from unittest.mock import MagicMock,patch
import test_final_services as baseline
from test_final_services import Row
from institute_lms.paper_blueprint import validate,batches

class BlueprintTests(unittest.TestCase):
    def test_mixed_types_and_marks(self):
        rows,_=validate(100,[{'kind':'MCQ','count':60,'marks':2},{'kind':'True/False','count':20,'marks':1},{'kind':'Written','count':20,'marks':5}])
        self.assertEqual(len(list(batches(rows))),5)
        self.assertEqual(sum(x['count']*x['marks'] for x in rows),240)
    def test_count_mismatch(self):
        with self.assertRaises(ValueError):validate(10,[{'kind':'MCQ','count':9,'marks':1}])
    def test_executable_template_rejected(self):
        with self.assertRaises(ValueError):validate(1,template={'script':'execute'})
    def test_duplicate_kind_rejected(self):
        with self.assertRaises(ValueError):validate(2,[{'kind':'MCQ','count':1},{'kind':'MCQ','count':1}])
    def test_invalid_marks_rejected(self):
        with self.assertRaises(ValueError):validate(1,[{'kind':'Written','count':1,'marks':0}])
    def test_bounded_final_batch(self):
        rows,_=validate(41);self.assertEqual([b['count'] for b in batches(rows)],[20,20,1])

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.fixture=baseline.Boundaries();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.f=self.fixture.f;self.load=self.fixture.load
    def test_refund_requires_verified_amount_identity(self):
        m=self.load('lecture_refunds');r=Row(payment_id='paid',amount_minor=500,currency='LKR',request_key='key')
        v={'verified':True,'status':'succeeded','payment_id':'paid','amount_minor':500,'currency':'LKR','request_key':'key','reference':'refund'}
        self.assertTrue(m.confirmed(v,r))
        for key,value in [('verified',False),('amount_minor',501),('payment_id','other'),('currency','USD'),('request_key','other'),('status','pending')]:
            self.assertFalse(m.confirmed({**v,key:value},r))
    def test_refund_duplicate_does_not_reverse_again(self):
        m=self.load('lecture_refunds');r=Row(status='Succeeded',payment_id='p',amount_minor=5,currency='LKR',request_key='k');self.f.get_doc.return_value=r
        wallet=types.ModuleType('institute_lms.wallet');wallet.post=MagicMock();wallet.locked_wallet=MagicMock()
        with patch.dict('sys.modules',{'institute_lms.wallet':wallet}):m.settle('r',{'verified':True,'status':'succeeded','payment_id':'p','amount_minor':5,'currency':'LKR','request_key':'k','reference':'r'})
        wallet.post.assert_not_called();wallet.locked_wallet.assert_not_called()
    def test_refund_wrong_identity_does_not_access_wallet(self):
        m=self.load('lecture_refunds');self.f.get_doc.return_value=Row(payment_id='p',amount_minor=5,currency='LKR',request_key='k')
        with self.assertRaises(PermissionError):m.settle('r',{'verified':False})
        self.assertEqual(self.f.get_doc.call_count,1)
    def test_verified_refund_reverses_wallet_and_only_original_purchase_access(self):
        r=Row(status='Pending',name='R',order_id='O',payment_id='p',amount_minor=500,currency='LKR',request_key='k',reason='Approved full provider refund')
        order=Row(name='O',status='succeeded',payment_id='p',wallet='W',institute='I',user='student')
        access=Row(name='A',order='O',revoked=0)
        self.f.get_doc.side_effect=lambda dt,name,**kw:{'IL Lecture Refund':r,'IL Lecture Order':order,'IL Lecture Access':access}[dt]
        self.f.get_all=MagicMock(return_value=['A'])
        wallet=types.ModuleType('institute_lms.wallet');wallet.post=MagicMock();wallet.locked_wallet=MagicMock(return_value=Row(name='W'))
        events=types.ModuleType('institute_lms.product_events');events.user_event=MagicMock()
        with patch.dict('sys.modules',{'institute_lms.wallet':wallet,'institute_lms.product_events':events}):
            self.load('lecture_refunds').settle('R',{'verified':True,'status':'succeeded','payment_id':'p','amount_minor':500,'currency':'LKR','request_key':'k','reference':'provider-refund'})
        self.assertEqual(wallet.post.call_args.args[1:5],('lecture-refund:O','Reversal',-500,0))
        self.assertEqual(access.revoked,1);self.assertEqual(order.status,'refunded');self.assertEqual(r.status,'Succeeded')
        self.assertEqual(self.f.get_all.call_args.kwargs['filters'],{'order':'O','revoked':0})
    def test_foreign_refund_admin_rejected(self):
        self.fixture.api.require_role=MagicMock();self.f.get_doc.return_value=Row(institute='OTHER')
        with self.assertRaises(PermissionError):self.load('lecture_refunds').authorized('o')
    def test_recording_student_cannot_publish(self):
        self.f.get_doc.return_value=Row(institute='I',classroom='C',recording_status='Ready')
        with self.assertRaises(PermissionError):self.load('live_classes').publish_recording('x',True)
    def test_recording_requires_review(self):
        self.fixture.member.update(user='teacher',name='T',role='Teacher')
        self.f.get_doc.return_value=Row(institute='I',classroom='C',recording_status='Ready')
        with self.assertRaisesRegex(ValueError,'Review'):self.load('live_classes').publish_recording('x',False)
    def test_unreviewed_recording_denies_student_before_provider(self):
        self.f.get_doc.return_value=Row(institute='I',classroom='C',recording_status='Ready',recording_published=0)
        with self.assertRaisesRegex(ValueError,'review'):self.load('live_classes').recording('x')
        self.f.get_attr.assert_not_called()
    def test_referenced_media_is_protected(self):
        self.f.db.exists.side_effect=[False,True]
        self.assertTrue(self.load('media_reconciliation').references(Row(storage_key='key',name='object')))
    def test_media_cleanup_deletes_only_exact_versions(self):
        provider=MagicMock();provider.delete_objects.return_value={};provider.list_object_versions.side_effect=[{'Versions':[{'Key':'key','VersionId':'1'},{'Key':'key-other','VersionId':'2'}]},{}]
        self.load('media_reconciliation').remove_exact(provider,'bucket','key')
        self.assertEqual(provider.delete_objects.call_args.kwargs['Delete']['Objects'],[{'Key':'key','VersionId':'1'}])
    def test_media_cleanup_partial_failure_retains_quota(self):
        provider=MagicMock();provider.list_object_versions.return_value={'Versions':[{'Key':'key','VersionId':'1'}]};provider.delete_objects.return_value={'Errors':[{'Code':'Denied'}]}
        with self.assertRaisesRegex(ValueError,'quota'):self.load('media_reconciliation').remove_exact(provider,'bucket','key')
    def test_media_cleanup_truncated_listing_refuses_delete(self):
        provider=MagicMock();provider.list_object_versions.return_value={'IsTruncated':True}
        with self.assertRaises(ValueError):self.load('media_reconciliation').remove_exact(provider,'bucket','key')
        provider.delete_objects.assert_not_called()
    def test_print_export_escapes_template_and_question(self):
        m=self.load('paper_generator');m.export=lambda _:dict(title='<script>x</script>',status='Draft',duration_minutes=60,questions=[dict(prompt='<img onerror=x>',options=['<b>A</b>','B'],answer=0,marks=1)])
        self.f.db.get_value.return_value=None
        html=m.printable('p')['html'];self.assertNotIn('<script>',html);self.assertNotIn('<img',html);self.assertNotIn('Answer:',html)
    def test_print_answer_key_is_explicit(self):
        m=self.load('paper_generator');m.export=lambda _:dict(title='T',status='Draft',duration_minutes=60,questions=[dict(prompt='Q',options=['A','B'],answer=0,marks=1)])
        self.f.db.get_value.return_value=None
        self.assertIn('Answer: A',m.printable('p',True)['html'])
    def test_notice_includes_only_allowed_fields(self):
        m=self.load('subscription_notices');notifications=types.ModuleType('institute_lms.notification_service');notifications.EVENTS=('premium.offer',);notifications.emit=MagicMock()
        self.f.get_all=MagicMock(return_value=['M'])
        with patch.dict('sys.modules',{'institute_lms.notification_service':notifications}):
            with self.assertRaises(ValueError):m.apply('I',[{'event_type':'premium.offer','secret':'bad'}])
        notifications.emit.assert_not_called()
    def test_student_live_grant_never_has_recording_or_screen_share(self):
        from livekit import api
        m=self.load('live_provider');m.settings=lambda:(api,'wss://preview.invalid','fictional-key','fictional-secret-for-local-signature-only')
        import base64
        token=m.participant('room','user','Student',False,True)['token']
        payload=token.split('.')[1];value=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
        self.assertFalse(value['video']['roomRecord']);self.assertFalse(value['video']['roomAdmin'])
        self.assertEqual(value['video']['canPublishSources'],['camera','microphone'])

if __name__=='__main__':unittest.main()
