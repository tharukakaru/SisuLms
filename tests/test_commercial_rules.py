import unittest
from datetime import datetime, timedelta
from institute_lms.commercial_rules import *

class CommercialRules(unittest.TestCase):
    def test_beneficiary_accepts_frappe_document_get_interface(self):
        class DocumentLike:
            def __init__(self, **values): self.values=values
            def get(self, key): return self.values.get(key)
        self.assertEqual(beneficiary(DocumentLike(institute='SISU')), 'Institute:SISU')
        self.assertEqual(beneficiary(DocumentLike(owner_type='Teacher',owner_user='teacher')), 'Teacher:teacher')
    def grant(self,student='S',product='theory',start='2026-10-01',end='2026-10-31',**kw):
        return dict(student=student,product_key=product,starts_at=start,ends_at=end,status='Active',**kw)
    def test_theory_and_paper_charge_twice_but_weekly_sessions_once(self):
        rows=[self.grant(),self.grant(),self.grant(product='paper')]
        units=billing_units(rows,'2026-10-01','2026-11-01')
        self.assertEqual(len(units),2)
        self.assertEqual(invoice_totals('Gold',len(units))['total_minor'],1510000)
    def test_programme_modules_share_one_unit(self):
        rows=[self.grant(product='Programme:1',teacher=str(i)) for i in range(12)]
        self.assertEqual(len(billing_units(rows,'2026-10-01','2026-11-01')),1)
    def test_180_day_access_has_six_periods(self):
        rows=[self.grant(start='2026-01-01',end='2026-06-30')]
        all_units=[]
        for month in range(1,7):all_units+=billing_units(rows,f'2026-{month:02}-01',f'2026-{month+1:02}-01')
        self.assertEqual(len(all_units),6)
        self.assertEqual(len({u['charge_at'] for u in all_units}),6)
        self.assertEqual(billing_units(rows,'2026-07-01','2026-08-01'),[])
    def test_short_course_crossing_month_end_counts_once(self):
        rows=[self.grant(start='2026-10-25',end='2026-11-08')]
        self.assertEqual(len(billing_units(rows,'2026-10-01','2026-11-01')),1)
        self.assertEqual(billing_units(rows,'2026-11-01','2026-12-01'),[])
    def test_overlapping_and_contiguous_renewals_keep_original_anchor(self):
        rows=[self.grant(start='2026-10-25',end='2026-11-08'),self.grant(start='2026-11-08',end='2026-12-01'),self.grant(start='2026-11-10',end='2026-11-15')]
        units=billing_units(rows,'2026-11-01','2026-12-01')
        self.assertEqual([u['charge_at'] for u in units],['2026-11-24T00:00:00'])
    def test_partial_last_period_and_exact_end(self):
        self.assertEqual(len(billing_units([self.grant(start='2026-10-01',end='2026-10-31')],'2026-10-01','2026-11-01')),1)
        self.assertEqual(len(billing_units([self.grant(start='2026-10-01',end='2026-11-01')],'2026-10-01','2026-11-01')),2)
    def test_duration_validation(self):
        self.assertEqual(duration_days(1),1)
        self.assertEqual(duration_days(180),180)
        for days in [0,-1,1801,1.5,None,True]:
            with self.assertRaises(ValueError):duration_days(days)
    def test_boundary_and_revocation(self):
        a=self.grant(end='2026-10-01');b=self.grant(start='2026-11-01',end='2026-12-01');c=self.grant();c['status']='Revoked'
        self.assertEqual(billing_units([a,b,c],'2026-10-01','2026-11-01'),[])
    def test_package_prices(self):
        self.assertEqual(invoice_totals('Gold',200)['total_minor'],2500000)
        self.assertEqual(invoice_totals('Individual',2)['total_minor'],220000)
        self.assertEqual(invoice_totals('Platinum',0)['total_minor'],2200000)
        with self.assertRaises(ValueError):invoice_totals('Gold',-1)
    def test_seven_day_boundary_including_proof_pending(self):
        due=datetime(2026,10,8,12)
        self.assertFalse(overdue('Unpaid',due,due-timedelta(seconds=1)))
        self.assertTrue(overdue('Unpaid',due,due))
        self.assertTrue(overdue('Under review',due,due))
        self.assertFalse(overdue('Paid',due,due))
        self.assertFalse(overdue('Void',due,due))
    def test_access_windows_and_leap_year(self):
        start=datetime(2024,2,29)
        self.assertEqual(access_window('Year',start)[1],datetime(2025,2,28))
        self.assertEqual(access_window('Week',start)[1],start+timedelta(days=7))
        self.assertEqual(access_window('Month','2026-01-31')[1],datetime(2026,2,28))
        with self.assertRaises(ValueError):access_window('Course',start)
        with self.assertRaises(ValueError):access_window('Custom',start,start)
    def test_only_gold_platinum_have_online_and_news_no_ai(self):
        for name in PLANS:
            self.assertTrue(plan_features(name)['lms'])
            self.assertEqual(plan_features(name)['news'],name in ONLINE)
            self.assertFalse(plan_features(name)['ai'])
        self.assertFalse(plan_features('Gold')['watermark'])
        self.assertTrue(plan_features('Platinum')['watermark'])
    def test_recipient_comes_from_class_owner(self):
        self.assertEqual(beneficiary(dict(owner_type='Institute',institute='TA',teacher='T')),'Institute:TA')
        self.assertEqual(beneficiary(dict(owner_type='Teacher',institute='TA',owner_user='teacher')),'Teacher:teacher')
        with self.assertRaises(ValueError):beneficiary(dict(owner_type='Teacher',institute='TA'))
    def test_money_validation(self):
        self.assertEqual(money_minor('8000.25'),800025)
        for n in ['NaN','Infinity','-1','0','1.001']:
            with self.assertRaises(ValueError):money_minor(n)

if __name__=='__main__':unittest.main()
