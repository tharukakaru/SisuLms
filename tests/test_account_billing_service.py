"""Service contract tests with an in-memory Frappe boundary; no real money or data."""
import importlib
import sys
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

class Row(dict):
    def __getattr__(self,k):return self.get(k)
    def __setattr__(self,k,v):self[k]=v
    def set(self,k,v):self[k]=v

def dt(value):
    return value if isinstance(value,datetime) else datetime.fromisoformat(str(value))

class BillingService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=types.ModuleType('frappe');u=types.ModuleType('frappe.utils')
        f.whitelist=lambda **kw:lambda fn:fn
        u.get_datetime=dt;u.now_datetime=datetime.now
        with patch.dict(sys.modules,{'frappe':f,'frappe.utils':u}):
            cls.b=importlib.import_module('institute_lms.account_billing')

    def setUp(self):
        self.now=datetime(2027,1,31,10)
        self.rows={};self.sent=[];self.owner=True
        self.a=Row(doctype=self.b.ACCOUNT,name='sub-1',account_key='Student:a@test',role='Student',plan='Student',billing_country='LK',country_status='Verified',trial_until=self.now-timedelta(days=1),trial_started=self.now-timedelta(days=15),enabled=1,billing_email='a@test',display_name='Learner')
        self.rows[(self.a.doctype,self.a.name)]=self.a
        self.fake=Row(session=Row(user='a@test'),conf=Row(il_control_plane=False),utils=Row(validate_email_address=lambda *a,**k:None),PermissionError=PermissionError)
        self.fake.throw=lambda msg,*args:(_ for _ in ()).throw(ValueError(msg))
        self.fake.get_doc=self.get_doc;self.fake.get_all=self.get_all
        self.fake.db=Row(get_value=self.get_value,exists=lambda doctype,filters:bool(self.get_value(doctype,filters,'name')),sql=lambda *a,**kw:[])
        self.fake.local=Row(request=Row(path='/api/method/institute_lms.api.classrooms'))
        self.fake.form_dict=Row()
        self.patches=[patch.object(self.b,'frappe',self.fake),patch.object(self.b,'now_datetime',lambda:self.now),patch.object(self.b,'account',lambda **kw:self.a),patch.object(self.b,'save',self.save),patch.object(self.b,'queue_document',lambda bill,kind:self.sent.append((bill.name,kind))),patch.object(self.b,'require_owner',self.check_owner),patch.object(self.b,'country_code',lambda c:c if c in ('LK','US') else self.fake.throw('invalid country'))]
        for p in self.patches:p.start()
        self.addCleanup(lambda:[p.stop() for p in reversed(self.patches)])

    def check_owner(self):
        if not self.owner:raise PermissionError('Owner required')

    def test_customer_status_contains_only_applicable_prices(self):
        for role, country, expected in [('Student','LK',50),('Teacher','US',900),('Institute','LK',1200)]:
            self.a.role=role;self.a.billing_country=country
            self.a.plan='Student' if role=='Student' else 'Individual'
            result=self.b.status()
            self.assertEqual(result['account']['monthly_minor'],expected)
            self.assertEqual(result['plans'][0]['monthly_minor'],expected)
            self.assertNotIn('catalogue',result)
            self.assertNotIn('countries',result)
            for field in ('billing_country','requested_country','country_status'):
                self.assertNotIn(field,result['account'])

    def test_pending_billing_does_not_guess_a_price(self):
        self.a.billing_country=None;self.a.country_status='Pending review'
        result=self.b.status()
        self.assertIsNone(result['account']['monthly_minor'])
        self.assertFalse(result['account']['billing_ready'])
        self.assertTrue(all(p['monthly_minor'] is None for p in result['plans']))

    def test_scheduled_plan_keeps_current_price_separate(self):
        self.a.role='Teacher';self.a.plan='Individual';self.a.next_plan='Gold'
        result=self.b.public_account(self.a)
        self.assertEqual(result['monthly_minor'],600)
        self.assertEqual(result['next_monthly_minor'],4500)
    def test_opt_in_provider_price_is_lkr_without_changing_legacy_students(self):
        self.fake.conf.il_usage_billing_enabled=1
        self.a.role='Institute';self.a.plan='Individual';self.a.billing_country=None
        self.assertEqual(self.b.price(self.a,'Individual'),250000)
        self.assertEqual(self.b.currency_for(self.a),'LKR')
        self.assertEqual(self.b.price(self.a,'Platinum'),2200000)
        self.a.role='Student';self.a.plan='Student';self.a.billing_country='LK'
        self.assertEqual(self.b.currency_for(self.a),'USD')
        self.assertEqual(self.b.price(self.a,'Student'),50)

    def test_legacy_invoice_currency_not_reinterpreted_after_policy_switch(self):
        self.fake.conf.il_usage_billing_enabled=1
        self.a.role='Institute';self.a.plan='Individual'
        self.assertEqual(self.b.currency_for(self.a),'LKR')
        self.fake.conf.il_usage_billing_enabled=0
        self.assertEqual(self.b.price(self.a,'Individual'),1200)
        self.assertEqual(self.b.currency_for(self.a),'USD')

    def test_new_policy_cannot_issue_student_subscription_invoice(self):
        self.fake.conf.il_usage_billing_enabled=1
        self.a.role='Student'
        with self.assertRaisesRegex(ValueError,'paid by the provider'):
            self.b.make_invoice(self.a)

    def save(self,row):
        if not row.name:row.name='bill-'+str(len(self.rows));row.creation=self.now
        self.rows[(row.doctype,row.name)]=row
        return row
    def get_doc(self,doctype,name=None,**kwargs):
        return Row(doctype) if isinstance(doctype,dict) else self.rows[(doctype,name)]
    def get_all(self,doctype,filters=None,fields=None,pluck=None,**kwargs):
        out=[r for (d,n),r in self.rows.items() if d==doctype and all(r.get(k)==v for k,v in (filters or {}).items())]
        return [r.get(pluck) for r in out] if pluck else out
    def get_value(self,doctype,filters,field=None,**kwargs):
        if isinstance(filters,str):rows=[self.rows[(doctype,filters)]] if (doctype,filters) in self.rows else []
        else:rows=self.get_all(doctype,filters)
        return rows[0].get(field or 'name') if rows else None
    def make(self):return self.b.make_invoice(self.a)

    def test_pending_country_cannot_issue(self):
        self.a.billing_country=None;self.a.country_status='Pending review'
        with self.assertRaises(ValueError):self.make()
        self.assertEqual(len(self.rows),1)
    def test_trial_has_no_charge(self):
        self.a.trial_until=self.now+timedelta(days=3)
        with self.assertRaises(ValueError):self.make()
    def test_invoice_idempotency_and_snapshot(self):
        first=self.make();again=self.make()
        self.assertEqual(first.name,again.name)
        self.assertEqual(first.amount_minor,50)
        self.assertEqual(first.period_end,datetime(2027,2,28,10))
        self.assertEqual(first.currency,'USD')
    def test_settlement_idempotent_and_anchor_preserved(self):
        bill=self.make()
        result=self.b.record_verified_payment(bill.name,'gateway:merchant:abc',50,'USD','Card')
        self.assertEqual(result.status,'Paid');self.assertEqual(self.a.anchor_day,31)
        expiry=self.a.paid_until
        self.b.record_verified_payment(bill.name,'gateway:merchant:abc',50,'USD','Card')
        self.assertEqual(self.a.paid_until,expiry);self.assertEqual(len(self.sent),1)
        self.now=expiry
        next_bill=self.make()
        self.assertEqual(next_bill.period_end,datetime(2027,3,31,10))
    def test_wrong_payment_never_unlocks(self):
        bill=self.make()
        for cents,currency in [(49,'USD'),(150,'USD'),(50,'LKR')]:
            with self.assertRaises(ValueError):self.b.record_verified_payment(bill.name,'ref',cents,currency,'Card')
        self.assertEqual(bill.status,'Unpaid');self.assertIsNone(self.a.paid_until)
    def test_duplicate_payment_reference_rejected(self):
        bill=self.make();self.b.record_verified_payment(bill.name,'unique',50,'USD','Card')
        self.now=self.a.paid_until
        other=self.make()
        with self.assertRaises(ValueError):self.b.record_verified_payment(other.name,'unique',50,'USD','Card')
        self.assertEqual(other.status,'Unpaid')
    def test_reference_allocated_to_usage_cannot_pay_subscription(self):
        bill=self.make()
        self.fake.conf.il_usage_billing_enabled=1
        self.rows[('IL Usage Invoice','usage-1')]=Row(name='usage-1',payment_reference='bank:used')
        with self.assertRaisesRegex(ValueError,'allocated to a usage invoice'):
            self.b.record_verified_payment(bill.name,'bank:used',50,'USD','Bank')
        self.assertEqual(bill.status,'Unpaid')
        self.assertIsNone(self.a.paid_until)

    def test_country_request_cannot_apply_discount(self):
        self.a.billing_country='US'
        self.b.request_country('LK')
        self.assertEqual(self.a.billing_country,'US')
        self.assertEqual(self.a.country_status,'Change requested')
        self.assertEqual(self.b.public_account(self.a)['monthly_minor'],150)
    def test_verification_owner_only(self):
        self.owner=False
        with self.assertRaises(PermissionError):self.b.verify_country(self.a.name,'LK','Verified bank address evidence')
    def test_country_change_voids_only_unpaid(self):
        bill=self.make()
        self.b.verify_country(self.a.name,'US','Reviewed billing address evidence')
        self.assertEqual(bill.status,'Void');self.assertEqual(bill.amount_minor,50)
        self.assertEqual(self.make().amount_minor,150)
    def test_bank_confirmation_requires_owner(self):
        bill=self.make();self.owner=False
        with self.assertRaises(PermissionError):self.b.confirm_bank_payment(bill.name,'abc',50,'Bank statement checked')
        self.assertEqual(bill.status,'Unpaid')
    def test_cancel_preserves_paid_access(self):
        bill=self.make();self.b.record_verified_payment(bill.name,'first',50,'USD','Card')
        until=self.a.paid_until
        self.b.cancel(True)
        self.assertEqual(self.a.paid_until,until);self.assertTrue(self.b.state(self.a)['available'])
        self.now=until
        with self.assertRaises(ValueError):self.make()
        self.b.cancel(False)
        self.assertEqual(self.make().status,'Unpaid')
    def test_expired_invoice_cannot_unlock(self):
        bill=self.make();self.now=bill.period_end
        with self.assertRaises(ValueError):self.b.record_verified_payment(bill.name,'late',50,'USD','Card')
    def test_package_change_waits_until_renewal(self):
        self.a.role='Teacher';self.a.plan='Individual'
        bill=self.make();self.b.record_verified_payment(bill.name,'first',600,'USD','Card')
        self.b.preferences('Gold','a@test')
        self.assertEqual(self.a.plan,'Individual');self.assertEqual(self.a.next_plan,'Gold');self.assertEqual(bill.amount_minor,600)
        self.now=self.a.paid_until
        self.assertEqual(self.make().amount_minor,4500)
    def test_recovery_allowed_but_learning_denied(self):
        fake_api=types.ModuleType('institute_lms.api');fake_api.institute=lambda:Row(name='inst')
        member=Row(name='student',role='Student',user='a@test')
        self.fake.db.get_value=lambda *a,**k:member
        with patch.dict(sys.modules,{'institute_lms.api':fake_api}),patch.object(self.b,'privileged',lambda:False),patch.object(self.b,'account',lambda *a,**k:self.a):
            with self.assertRaises(ValueError):self.b.guard_request()
            self.fake.local.request.path='/api/method/institute_lms.account_billing.status'
            self.b.guard_request()
            self.fake.local.request.path='/private/files/lesson.pdf'
            with self.assertRaises(ValueError):self.b.guard_request()
    def test_document_escapes_user_content(self):
        bill=self.make();bill.billed_to='<script>alert(1)</script>'
        result=self.b.document_html(bill)
        self.assertNotIn('<script>',result);self.assertIn('&lt;script&gt;',result)

if __name__=='__main__':unittest.main()
