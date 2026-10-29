"""Executable unit/regression tests. No Frappe/MariaDB/Redis integration claims."""
import ast
import hashlib
import importlib.util
import json
import sys
import threading
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock,patch
from institute_lms.saas_rules import (CORE,AI,LIMITS,resolve,effective_state,check_capacity,
    sign,verify_manifest,notification_key,transition_payment,hostname)

ROOT=Path(__file__).resolve().parents[1]/'institute_lms'
NOW=datetime(2026,10,2,12)
class Record(dict):
    def __getattr__(self,k):return self.get(k)
    def __setattr__(self,k,v):self[k]=v

class Rules(unittest.TestCase):
    def test_starter_denies_ai(self):
        r=resolve({k:True for k in CORE},{'students':20})
        self.assertTrue(r['features']['lms']);self.assertTrue(all(not r['features'][k] for k in AI))
    def test_premium_enables_ai(self):
        r=resolve({k:True for k in CORE+AI},{'ai_credits':100})
        self.assertTrue(all(r['features'][k] for k in AI))
    def test_custom_override(self):
        r=resolve({'lms':True},{'students':10},{'features':{'ai.rag':True},'limits':{'students':55},'support_tier':'priority'})
        self.assertEqual(r['limits']['students'],55);self.assertTrue(r['features']['ai.rag']);self.assertEqual(r['support_tier'],'priority')
    def test_invalid_policy_rejected(self):
        for f,l in [({'unknown':True},{}),({'lms':'true'},{}),({}, {'students':True}),({}, {'students':-1})]:
            with self.assertRaises(ValueError):resolve(f,l)
    def test_subscription_lifecycle(self):
        end=NOW-timedelta(seconds=1);grace=NOW+timedelta(days=1)
        self.assertEqual(effective_state('active',end,grace,NOW),'grace')
        self.assertEqual(effective_state('trial',end,None,NOW),'expired')
        for state in ('suspended','cancelled','past_due','expired'):
            self.assertEqual(effective_state(state,grace,grace,NOW),state)
    def test_storage_quota_rejection_and_boundary(self):
        self.assertEqual(check_capacity(90,10,100),100)
        with self.assertRaises(ValueError):check_capacity(91,10,100)
        with self.assertRaises(ValueError):check_capacity(0,1,0)
    def test_no_negative_or_boolean_usage(self):
        for n in (-1,True,1.5):
            with self.assertRaises(ValueError):check_capacity(0,n,10)
    def manifest(self):
        return dict(tenant_id='A',site_hostname='a.example.invalid',revision=2,issued_at=str(NOW),lease_until=str(NOW+timedelta(hours=23)),features={'lms':True},limits={},state='active',enabled=True)
    def test_manifest_site_isolation(self):
        d=self.manifest();key='x'*40;signature=sign(d,key)
        verify_manifest(d,signature,key,'A','a.example.invalid',1,NOW)
        for tenant,site in [('B','a.example.invalid'),('A','b.example.invalid')]:
            with self.assertRaises(ValueError):verify_manifest(d,signature,key,tenant,site,1,NOW)
    def test_manifest_replay_tamper_expiry(self):
        d=self.manifest();key='x'*40;signature=sign(d,key)
        with self.assertRaises(ValueError):verify_manifest(d,signature,key,'A','a.example.invalid',2,NOW)
        with self.assertRaises(ValueError):verify_manifest(d,signature,key,'A','a.example.invalid',1,NOW+timedelta(minutes=6))
        d['enabled']=False
        with self.assertRaises(ValueError):verify_manifest(d,signature,key,'A','a.example.invalid',1,NOW)
    def test_payment_success_is_monotonic(self):
        for state in ('succeeded','cancelled','failed','pending'):self.assertEqual(transition_payment('succeeded',state),'succeeded')
        self.assertEqual(transition_payment('failed','succeeded'),'succeeded')
    def test_notification_key_recipient_isolation(self):
        self.assertEqual(notification_key('event','A'),notification_key('event','A'))
        self.assertNotEqual(notification_key('event','A'),notification_key('event','B'))
    def test_hostname_cannot_inject_command_or_path(self):
        for host in ('https://a.test','a.test;rm','a.test/path','-x.test','a.test:80'):
            with self.assertRaises(ValueError):hostname(host)

class Services(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.PermissionError=PermissionError;self.f.AuthenticationError=PermissionError
        self.f.throw=lambda msg,kind=ValueError:(_ for _ in ()).throw(kind(msg))
        self.f.conf=Record(encryption_key='unit-only-key',il_tenant_id='A')
        self.f.session=Record(user='student@example.invalid');self.f.local=Record(request_ip='127.0.0.1')
        self.f.db=MagicMock();self.f.get_doc=MagicMock();self.f.get_all=MagicMock(return_value=[])
        u=types.ModuleType('frappe.utils');u.now_datetime=lambda:NOW;u.get_datetime=lambda v:datetime.fromisoformat(str(v));u.get_url=lambda *a:'https://a.example.invalid'
        self.modules=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':u});self.modules.start();self.addCleanup(self.modules.stop)
    def load(self,name):
        key='institute_lms.'+name;sys.modules.pop(key,None)
        spec=importlib.util.spec_from_file_location(key,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m);return m
    def fake(self,name,**kw):
        m=types.ModuleType('institute_lms.'+name);m.__dict__.update(kw);sys.modules[m.__name__]=m;return m
    def test_wallet_filters_teacher_and_institute(self):
        m=self.load('class_billing');inst=Record(name='I',school_mode=1)
        self.assertEqual(m.settlement_filters(inst,Record(owner_type='Teacher',owner_user='T'))['institute'],['is','not set'])
        self.assertEqual(m.settlement_filters(inst,Record(owner_type='Teacher',owner_user='T'))['owner_user'],'T')
        self.assertEqual(m.settlement_filters(inst,Record(owner_type='Institute'))['institute'],'I')
        with self.assertRaises(ValueError):m.settlement_filters(inst,Record(owner_type='Teacher'))
    def enrollment(self,owner,fee,parts):
        self.fake('commercial',free_access=MagicMock())
        billing=self.load('class_billing');billing.invoice_split=MagicMock(side_effect=lambda inst,amount,user,room:dict(amount=amount))
        tree=ast.parse((ROOT/'api.py').read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='create_enrollment')
        env=dict(__name__="institute_lms.api",__package__="institute_lms",frappe=self.f,money=lambda x:Decimal(str(x)),today=lambda:'2026-10-02',getdate=lambda x:x)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'api.py','exec'),env)
        made=[]
        def doc(data):
            made.append(data);return types.SimpleNamespace(insert=lambda **kw:Record(name='E'))
        self.f.get_doc.side_effect=doc
        room=Record(name='C',owner_type=owner,fee_mode='Free' if fee==0 else 'Paid',fee=fee,reload=lambda:None)
        env['create_enrollment'](Record(name='I',school_mode=1),room,Record(name='S',user='S'),parts)
        return made,billing
    def test_school_institute_exempts(self):
        rows,billing=self.enrollment('Institute',100,[]);self.assertEqual(rows[0]['fee'],0);billing.invoice_split.assert_not_called()
    def test_school_teacher_paid_retains_invoice(self):
        rows,_=self.enrollment('Teacher',100,[dict(amount=100,due_date='2026-10-02')]);self.assertEqual(rows[0]['fee'],100);self.assertEqual(rows[1]['status'],'Unpaid')
    def test_school_teacher_missing_installments_rejected(self):
        with self.assertRaises(ValueError):self.enrollment('Teacher',100,[])
    def test_free_teacher_needs_no_wallet_or_contract(self):
        rows,billing=self.enrollment('Teacher',0,[]);self.assertEqual(rows[0]['fee'],0);billing.invoice_split.assert_not_called()
    def test_paid_content_denies_unpaid_allows_paid(self):
        from institute_lms.domain import access_decision
        e=dict(active=1,fee=100,access_override='Automatic')
        self.assertFalse(access_decision(e,[],NOW.date())[0])
        self.assertTrue(access_decision(e,[dict(status='Paid',due_date='2026-10-01')],NOW.date())[0])
    def test_native_paid_reader_reuses_access(self):
        self.fake('commercial',account_for=lambda *a:None)
        m=self.load('native_access');self.f.get_all.return_value=['C'];self.f.get_doc.return_value=Record(active=1,fee_mode='Paid')
        self.fake('saas',require=MagicMock());self.fake('retention',access_allowed=lambda d:True)
        a=self.fake('api',classroom_for=lambda n:(None,'member','room'),access=lambda r,m:dict(allowed=False))
        with self.assertRaises(PermissionError):m.require_course('course')
        a.access=lambda r,m:dict(allowed=True);m.require_course('course')
    def test_native_free_reader_keeps_upstream_authority(self):
        self.fake('commercial',account_for=lambda *a:None)
        m=self.load('native_access');self.f.get_all.return_value=['C'];self.f.get_doc.return_value=Record(active=1,fee_mode='Free',as_dict=lambda:{})
        self.fake('saas',require=MagicMock());self.fake('retention',access_allowed=lambda d:True)
        a=self.fake('api',classroom_for=MagicMock(),access=MagicMock());m.require_course('free');a.classroom_for.assert_not_called()
    def test_notification_replay_no_second_insert(self):
        self.fake('saas',managed=MagicMock());m=self.load('notification_service')
        self.f.db.sql.side_effect=[[('M',)],[('event-original',)]];self.f.get_doc.return_value=Record(institute='I')
        self.assertEqual(m.emit('I','M','announcement','K','body'),'event-original')
        self.assertEqual(self.f.get_doc.call_count,1)
    def test_foreign_notification_recipient_rejected(self):
        self.fake('saas',managed=MagicMock());m=self.load('notification_service');self.f.get_doc.return_value=Record(institute='other')
        with self.assertRaises(PermissionError):m.emit('I','M','announcement','K','body')
    def test_storage_checks_before_file_write(self):
        gate=self.fake('saas',quota=MagicMock(side_effect=ValueError('Plan limit exceeded')),managed=MagicMock());self.fake('usage',used=lambda r:90)
        m=self.load('storage');self.f.flags=Record()
        with self.assertRaises(ValueError):m.before_write(20)
        self.assertEqual(gate.quota.call_args.args[2],20)
    def test_tenant_cannot_use_platform_owner_api(self):
        self.fake('saas',managed=MagicMock(),audit=MagicMock());m=self.load('platform')
        with self.assertRaises(PermissionError):m.control()
    def test_bad_payment_signature_never_settles(self):
        self.fake('saas',managed=MagicMock(),audit=MagicMock());m=self.load('subscription_payments')
        m.config=lambda:('key','whsec_test','test');m.settle=MagicMock()
        self.f.request=Record(get_data=lambda **kw:b'{}',headers={})
        with self.assertRaises(PermissionError):m.notify()
        m.settle.assert_not_called()
    def test_verified_webhook_replay_does_not_settle_twice(self):
        self.fake('saas',managed=lambda d:d,audit=MagicMock());m=self.load('subscription_payments')
        m.config=lambda:('key','secret','test');m.verify_signature=lambda *a:True;m.valid_payment=lambda *a:True;m.settle=MagicMock()
        a=Record(name='A',amount_minor=100,currency='LKR',checkout_id='C',mode='test',status='succeeded',payment_id='P')
        self.f.get_doc.return_value=a;self.f.db.sql.return_value=[('A',)];self.f.db.exists.return_value=True
        raw=json.dumps(dict(mode='test',type='payment.succeeded',data=dict(reference='A',id='P'))).encode()
        self.f.request=Record(get_data=lambda **kw:raw,headers={})
        self.assertTrue(m.notify()['duplicate']);m.settle.assert_not_called()
    def test_signed_wrong_amount_never_activates_subscription(self):
        self.fake('saas',managed=lambda d:d,audit=MagicMock());m=self.load('subscription_payments')
        m.config=lambda:('key','secret','test');m.verify_signature=lambda *a:True;m.settle=MagicMock()
        self.f.get_doc.return_value=Record(name='A',amount_minor=2000,currency='LKR',checkout_id='C',mode='test',status='pending')
        self.f.db.sql.return_value=[('A',)]
        payment=dict(reference='A',id='pay_'+'x'*24,mode='test',object='payment',status='succeeded',currency='LKR',amountCents=1000,checkoutId='C')
        self.f.request=Record(get_data=lambda **kw:json.dumps(dict(mode='test',type='payment.succeeded',data=payment)).encode(),headers={})
        with self.assertRaises(PermissionError):m.notify()
        m.settle.assert_not_called()
    def test_verified_success_is_only_webhook_activation_branch(self):
        self.fake('saas',managed=lambda d:d,audit=MagicMock());m=self.load('subscription_payments')
        m.config=lambda:('key','secret','test');m.verify_signature=lambda *a:True;m.settle=MagicMock()
        a=Record(name='A',amount_minor=2000,currency='LKR',checkout_id='C',mode='test',status='pending')
        self.f.get_doc.side_effect=lambda *args,**kw:a if isinstance(args[0],str) else Record(args[0])
        self.f.db.sql.return_value=[('A',)];self.f.db.exists.return_value=False
        payment=dict(reference='A',id='pay_'+'x'*24,mode='test',object='payment',status='succeeded',currency='LKR',amountCents=2000,checkoutId='C')
        self.f.request=Record(get_data=lambda **kw:json.dumps(dict(mode='test',type='payment.succeeded',data=payment)).encode(),headers={})
        self.assertTrue(m.notify()['settled']);m.settle.assert_called_once();self.assertEqual(a.status,'succeeded')
    def test_quota_acquires_subscription_lock_before_counting(self):
        self.fake('commercial',account_for=lambda *a:None,locked=MagicMock(),locked_reason=MagicMock(),PLANS={})
        self.fake('api',institute=lambda:Record(name='I'))
        m=self.load('saas');events=[]
        m.state=lambda lock=False:events.append(('locked',lock)) or Record()
        m.resolved=lambda d:dict(available=True,limits={'storage_bytes':10})
        def current():events.append('count');return 9
        with self.assertRaises(ValueError):m.quota('storage_bytes',current,2)
        self.assertEqual(events,[('locked',True),'count'])
    def test_suspended_resolver_denies_features(self):
        self.fake('commercial',feature_policy=lambda:None)
        m=self.load('saas');m.resolved=lambda:dict(available=False,features={'lms':True})
        with self.assertRaises(PermissionError):m.require('lms')
    def test_otp_failed_send_still_enforces_cooldown(self):
        m=self.otp();sender=MagicMock(side_effect=ValueError('provider unavailable'))
        with self.assertRaises(ValueError):m.issue('+94771234567','SMS',sender)
        with self.assertRaises(ValueError):m.issue('+94771234567','WHATSAPP',sender)
        self.assertEqual(sender.call_count,1)
    def otp(self):
        self.fake('wallet',signed_in=lambda:None);self.fake('registration',limit=MagicMock());self.fake('profiles',write=MagicMock())
        class Cache:
            def __init__(self):self.data={};self.mutex=threading.Lock()
            def lock(self,*a,**kw):return self.mutex
            def get_value(self,k):return self.data.get(k)
            def set_value(self,k,v,**kw):self.data[k]=v
            def delete_value(self,k):self.data.pop(k,None)
        self.f.cache=Cache();return self.load('otp')
    def test_concurrent_otp_issue_sends_once(self):
        m=self.otp();sender=MagicMock()
        def issue():
            try:return m.issue('+94771234567','SMS',sender)
            except ValueError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:issue(),range(2)))
        self.assertEqual(sender.call_count,1);self.assertEqual(sum(x is not None for x in results),1)
        d=self.f.cache.data['il_phone:'+self.f.session.user+':SMS'];self.assertNotIn(sender.call_args.args[1],json.dumps(d))
        self.assertEqual(sys.modules['institute_lms.registration'].limit.call_count,3)
    def test_otp_channel_separation_and_attempt_limit(self):
        m=self.otp();sender=MagicMock();m.issue('+94771234567','WHATSAPP',sender)
        with self.assertRaises(ValueError):m.verify(sender.call_args.args[1],'SMS')
        for _ in range(5):
            with self.assertRaises(ValueError):m.verify('999999' if sender.call_args.args[1]!='999999' else '888888','WHATSAPP')
        with self.assertRaises(ValueError):m.verify(sender.call_args.args[1],'WHATSAPP')
    def test_otp_single_use(self):
        m=self.otp();sender=MagicMock();result=m.issue('+94771234567','SMS',sender)
        self.f.db.get_value.return_value=None;self.f.get_doc.return_value=Record()
        self.assertTrue(m.verify(sender.call_args.args[1],'SMS',result['challenge'])['verified'])
        with self.assertRaises(ValueError):m.verify(sender.call_args.args[1],'SMS')

if __name__=='__main__':unittest.main()
