import unittest
from datetime import datetime, timedelta
from institute_lms.provider_usage_rules import usage_quote, usage_access_blocked, chargeable_start

class UsageRulesTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 11, 1)
        self.end = datetime(2026, 12, 1)
    def quote(self, rows, paid=True, plan="Individual"):
        return usage_quote("teen", plan, self.start, self.end, self.start,
                           self.start if paid else None, rows)
    def row(self, student, when, provider="teen", present=True):
        return dict(student=student, present_at=when, provider=provider, present=present)
    def test_distinct_provider_scope_and_period_boundaries(self):
        rows=[self.row("a",self.start),self.row("a",self.start+timedelta(days=2)),
              self.row("b",self.start,"other"),self.row("c",self.end),
              self.row("d",self.start-timedelta(seconds=1)),self.row("e",self.start,present=False)]
        q=self.quote(rows)
        self.assertEqual((q["quantity"],q["amount"],q["student_ids"]),(1,100,["a"]))
    def test_no_verified_payment_no_usage_charge(self):
        self.assertEqual(self.quote([self.row("a",self.start)],paid=False)["amount"],0)
    def test_trial_and_payment_both_required(self):
        later=self.start+timedelta(days=3)
        self.assertEqual(chargeable_start(self.start,later),later)
        self.assertEqual(chargeable_start(later,self.start),later)
        self.assertIsNone(chargeable_start(later,None))
    def test_rates_and_deadlines(self):
        rows=[self.row(str(n),self.start) for n in range(50)]
        for plan, expected in [("Individual",5000),("Silver",2500),("Gold",2500),("Platinum",2500)]:
            q=self.quote(rows,plan=plan)
            self.assertEqual(q["amount"],expected)
            self.assertEqual(q["estimate_at"],self.end-timedelta(days=5))
            self.assertEqual(q["due_at"],self.end+timedelta(days=10))
    def test_suspension_requires_explicit_reactivation(self):
        invoice={"due_at":self.end,"settled":False}
        self.assertFalse(usage_access_blocked(self.end-timedelta(seconds=1),[invoice]))
        self.assertTrue(usage_access_blocked(self.end,[invoice]))
        invoice["settled"]=True
        self.assertFalse(usage_access_blocked(self.end,[invoice]))
        self.assertTrue(usage_access_blocked(self.end,[invoice],suspension_recorded=True))

if __name__ == "__main__": unittest.main()
