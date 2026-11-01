import importlib.util
import json
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from institute_lms.cybersource_contract import (session_request, request_jwt, verify_session,
    verify_transaction, b64url, unb64, minor, HOST)

REFERENCE = 'sisu-' + 'a' * 32


def transaction():
    return {'id': '12345678901234567890', 'merchantId': 'sandbox_merchant',
        'clientReferenceInformation': {'code': REFERENCE},
        'orderInformation': {'amountDetails': {'totalAmount': '100.00', 'currency': 'LKR'}},
        'applicationInformation': {'applications': [
            {'name': 'ics_auth', 'reasonCode': 100}, {'name': 'ics_bill', 'reasonCode': 100}]}}


class Contract(unittest.TestCase):
    def setUp(self):
        self.binding = dict(merchant_id='sandbox_merchant', reference=REFERENCE, amount_minor=10000, currency='LKR')

    def test_customer_payment_no_token_storage_or_recurring(self):
        r = session_request(REFERENCE, 10000, 'LKR', 'https://sandbox.example.test',
                            ['PANENTRY', 'GOOGLEPAY', 'APPLEPAY', 'CLICKTOPAY'])
        self.assertEqual(r['completeMandate']['type'], 'CAPTURE')
        self.assertEqual(r['completeMandate']['consumerAuthentication'], '3DS')
        self.assertFalse(r['completeMandate']['tms']['tokenCreate'])
        self.assertFalse(r['captureMandate']['requestSaveCredentials'])
        self.assertEqual(r['data']['clientReferenceInformation']['code'], REFERENCE)

    def test_origins_and_methods_fail_closed(self):
        for url in ('http://localhost:8000', 'https://user@site.test', 'https://site.test/path'):
            with self.assertRaises(ValueError): session_request(REFERENCE, 10, 'LKR', url, ['PANENTRY'])
        with self.assertRaises(ValueError):session_request(REFERENCE, 10, 'LKR', 'https://site.test', ['UNKNOWN'])

    def test_no_rounding_or_nonfinite_amount(self):
        for value in ('1.001', '-1', 'NaN', 'Infinity', '0', None):
            with self.assertRaises(ValueError):minor(value)

    def test_verified_auth_and_capture(self):
        self.assertEqual(verify_transaction(transaction(), self.binding), 'succeeded')

    def test_authorization_alone_does_not_grant(self):
        t = transaction();t['applicationInformation']['applications'].pop()
        self.assertEqual(verify_transaction(t, self.binding), 'pending')

    def test_capture_failure_does_not_grant(self):
        t = transaction();t['applicationInformation']['applications'][1]['reasonCode'] = 102
        self.assertEqual(verify_transaction(t, self.binding), 'pending')

    def test_bindings_cannot_be_replayed(self):
        for key, value in [('merchant_id', 'other'), ('reference', 'other'), ('amount_minor', 999), ('currency', 'USD')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_transaction(transaction(), dict(self.binding, **{key: value}))

    def test_decline_and_reversal(self):
        t = transaction();t['applicationInformation']['applications'] = [{'name':'ics_auth','reasonCode':203}]
        self.assertEqual(verify_transaction(t, self.binding), 'failed')
        t = transaction();t['applicationInformation']['applications'].append({'name':'ics_auth_reversal','reasonCode':100})
        self.assertEqual(verify_transaction(t, self.binding), 'review')

    def test_signed_request_exact_body_host_path_expiry(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        body = b'{"amount":"1.00"}'
        token = request_jwt('POST', '/uc/v1/sessions', body, 'merchant', 'key', key, now=100)
        h,p,s=token.split('.')
        key.public_key().verify(unb64(s),(h+'.'+p).encode(),padding.PKCS1v15(),hashes.SHA256())
        claims=json.loads(unb64(p));self.assertEqual(claims['request-host'],HOST)
        self.assertEqual(claims['exp'],220);self.assertEqual(claims['request-resource-path'],'/uc/v1/sessions')
        import base64,hashlib
        self.assertEqual(claims['digest'],base64.b64encode(hashlib.sha256(body).digest()).decode())
        token=request_jwt('GET','/tss/v2/transactions/1234567890',b'','merchant','key',key,now=100)
        self.assertNotIn('digest',json.loads(unb64(token.split('.')[1])))

    def test_session_signature_and_expiry(self):
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        n=key.public_key().public_numbers()
        jwk={'kty':'RSA','kid':'key','e':b64url(n.e.to_bytes(3,'big')),'n':b64url(n.n.to_bytes(256,'big'))}
        h=b64url(json.dumps({'alg':'RS256','kid':'key'}).encode())
        p=b64url(json.dumps({'iat':100,'exp':200}).encode())
        text=h+'.'+p;token=text+'.'+b64url(key.sign(text.encode(),padding.PKCS1v15(),hashes.SHA256()))
        self.assertEqual(verify_session(token,lambda _:jwk,now=150)['exp'],200)
        with self.assertRaises(ValueError):verify_session(token,lambda _:jwk,now=201)
        with self.assertRaises(InvalidSignature):verify_session(h+'.'+b64url(b'{"exp":9999}')+'.'+token.split('.')[2],lambda _:jwk,now=150)


class Row(dict):
    __getattr__=dict.get
    def __setattr__(self,k,v):self[k]=v


class Service(unittest.TestCase):
    def setUp(self):
        f=types.ModuleType('frappe');u=types.ModuleType('frappe.utils')
        f.whitelist=lambda **kw:lambda fn:fn
        f.throw=lambda msg,*a:(_ for _ in ()).throw(ValueError(msg))
        f.PermissionError=PermissionError;f.ValidationError=ValueError
        f.conf={};f.session=Row(user='student@test')
        f.db=MagicMock();f.db.get_value.return_value=None
        u.now_datetime=lambda:datetime(2026,10,30,10)
        u.get_datetime=lambda x:x;u.get_url=lambda:'https://sandbox.example.test'
        spec=importlib.util.spec_from_file_location('institute_lms._cybs_test',Path(__file__).parents[1]/'institute_lms/cybersource.py')
        self.m=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'frappe':f,'frappe.utils':u}):spec.loader.exec_module(self.m)
        self.f=f
        self.a=Row(name='attempt',reference=REFERENCE,kind='tuition',invoice='invoice',
            merchant_scope='tuition:provider',merchant_id='sandbox_merchant',amount_minor=10000,
            currency='LKR',status='pending',customer='student@test',active_key='tuition:invoice')
        f.get_doc=lambda *a,**kw:self.a
        self.m.save=lambda doc:doc
        self.m.accessible=lambda name:self.a
        self.m.settings=lambda scope:dict(merchant_id='sandbox_merchant')
        self.m.source=lambda *a,**kw:(Row(status='Unpaid'),Row(name='inst'),'scope',10000,'LKR')
        self.m.settle=MagicMock()

    def test_browser_cannot_settle_or_clear_attempt(self):
        self.m.browser_event('attempt','completed')
        self.assertEqual(self.a.status,'pending');self.assertEqual(self.a.active_key,'tuition:invoice')
        self.m.settle.assert_not_called()
        self.m.browser_event('attempt','cancelled');self.assertEqual(self.a.status,'pending')

    def test_server_report_settles_once(self):
        self.m.request=MagicMock(side_effect=[{'_embedded':{'transactionSummaries':[{'id':transaction()['id']}]}},transaction()])
        self.assertEqual(self.m.reconcile('attempt')['status'],'succeeded')
        self.assertEqual(self.m.reconcile('attempt')['status'],'succeeded')
        self.m.settle.assert_called_once();self.assertIsNone(self.a.active_key)

    def test_mismatch_never_settles(self):
        t=transaction();t['merchantId']='other'
        self.m.request=MagicMock(side_effect=[{'_embedded':{'transactionSummaries':[{'id':t['id']}]}},t])
        self.assertEqual(self.m.reconcile('attempt')['status'],'pending');self.m.settle.assert_not_called()

    def test_duplicate_transactions_require_review(self):
        self.m.request=MagicMock(return_value={'_embedded':{'transactionSummaries':[{'id':'1'},{'id':'2'}]}})
        self.assertEqual(self.m.reconcile('attempt')['status'],'pending');self.m.settle.assert_not_called()

    def test_poll_cooldown(self):
        self.a.last_checked=datetime(2026,10,30,9,59)
        self.m.request=MagicMock();self.m.reconcile('attempt');self.m.request.assert_not_called()

    def test_invoice_changed_keeps_verified_money_for_review(self):
        self.m.source=lambda *a,**kw:(Row(status='Paid'),None,'scope',10000,'LKR')
        self.m.request=MagicMock(side_effect=[{'_embedded':{'transactionSummaries':[{'id':transaction()['id']}]}},transaction()])
        self.assertEqual(self.m.reconcile('attempt')['status'],'review');self.m.settle.assert_not_called()

    def test_live_config_rejected(self):
        self.f.conf={'il_cybersource':{'enabled':True,'mode':'live'}}
        # Access the real implementation, not the test's settings stub.
        spec=importlib.util.spec_from_file_location('institute_lms._cybs_test2',Path(__file__).parents[1]/'institute_lms/cybersource.py')
        m=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':types.SimpleNamespace(now_datetime=datetime.now,get_datetime=lambda x:x,get_url=lambda:'https://site.test')}):spec.loader.exec_module(m)
        with self.assertRaises(ValueError):m.settings('platform')

    def test_other_student_and_foreign_tenant_are_denied(self):
        api=types.ModuleType('institute_lms.api')
        api.identity=lambda:(Row(name='inst'),Row(role='Student',name='member'))
        api.scoped=lambda *a:Row(student='another-member')
        # Restore the actual source function, which is stubbed in reconciliation tests.
        spec=importlib.util.spec_from_file_location('institute_lms._cybs_access',Path(__file__).parents[1]/'institute_lms/cybersource.py')
        m=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':types.SimpleNamespace(now_datetime=datetime.now,get_datetime=lambda x:x,get_url=lambda:'https://site.test'),'institute_lms.api':api}):
            spec.loader.exec_module(m)
            with self.assertRaises(ValueError):m.source('tuition','foreign')
            self.f.session.user='Guest'
            with self.assertRaises(ValueError):m.source('tuition','foreign')

    def test_network_uncertainty_keeps_invoice_unpaid(self):
        self.m.request=MagicMock(side_effect=self.m.ProviderUnavailable())
        self.assertEqual(self.m.reconcile('attempt')['status'],'pending')
        self.m.settle.assert_not_called()
        self.assertEqual(self.a.active_key,'tuition:invoice')

    def test_declined_report_releases_retry_without_access(self):
        t=transaction();t['applicationInformation']['applications']=[{'name':'ics_auth','reasonCode':203}]
        self.m.request=MagicMock(side_effect=[{'_embedded':{'transactionSummaries':[{'id':t['id']}]}},t])
        self.assertEqual(self.m.reconcile('attempt')['status'],'failed')
        self.assertIsNone(self.a.active_key);self.m.settle.assert_not_called()

    def test_business_validation_failure_retains_verified_transaction(self):
        self.m.request=MagicMock(side_effect=[{'_embedded':{'transactionSummaries':[{'id':transaction()['id']}]}},transaction()])
        self.m.settle.side_effect=ValueError('Invoice expired')
        self.assertEqual(self.m.reconcile('attempt')['status'],'review')
        self.f.db.rollback.assert_called_once_with(save_point='cybs_allocation')
        self.assertTrue(self.a.settlement_key)

    def test_transaction_lookup_identity_mismatch(self):
        t=transaction();t['id']='99999999999999999'
        self.m.request=MagicMock(side_effect=[{'_embedded':{'transactionSummaries':[{'id':transaction()['id']}]}},t])
        self.assertEqual(self.m.reconcile('attempt')['status'],'pending');self.m.settle.assert_not_called()

    def test_duplicate_start_never_returns_a_second_context(self):
        reg=types.ModuleType('institute_lms.registration');reg.limit=lambda *a:None
        self.f.db.get_value.return_value='attempt'
        self.m.request=MagicMock()
        with patch.dict(sys.modules,{'institute_lms.registration':reg}):
            r=self.m.start('tuition','invoice')
        self.assertNotIn('session',r);self.m.request.assert_not_called()

    def test_start_snapshots_server_price_before_external_call(self):
        reg=types.ModuleType('institute_lms.registration');reg.limit=lambda *a:None
        events=[]
        self.f.db.commit=lambda:events.append('commit')
        self.f.get_doc=lambda doc,*a,**kw:Row(doc,name='new') if isinstance(doc,dict) else self.a
        self.m.source=lambda *a,**kw:(Row(status='Unpaid'),Row(name='inst'),'platform',10000,'LKR')
        self.m.settings=lambda scope:dict(merchant_id='sandbox_merchant',origin='https://sandbox.example.test',methods=['PANENTRY'])
        def provider(c,method,path,body,token=False):
            self.assertEqual(events,['commit'])
            self.assertEqual(body['data']['orderInformation']['amountDetails']['totalAmount'],'100.00')
            self.assertEqual(path,'/uc/v1/sessions')
            return 'signed-session',{'exp':9999999999}
        self.m.request=provider
        with patch.dict(sys.modules,{'institute_lms.registration':reg}):
            r=self.m.start('tuition','invoice')
        self.assertEqual(r['session'],'signed-session');self.m.settle.assert_not_called()

    def test_disabled_provider_does_not_block_existing_bank_flow(self):
        self.f.conf={};self.m.assert_no_active('tuition','invoice')
        self.f.db.exists.assert_not_called()

    def test_active_attempt_blocks_alternative_settlement(self):
        self.f.conf={'il_cybersource':{'enabled':True}}
        self.f.db.exists.return_value=True
        with self.assertRaises(ValueError):self.m.assert_no_active('tuition','invoice')
