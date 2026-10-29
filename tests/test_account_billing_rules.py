import unittest
from datetime import datetime, timedelta
from institute_lms.account_billing_rules import amount, next_anniversary, trial_end, access_state, payment_matches

class FixedSubscriptions(unittest.TestCase):
    def test_all_teacher_prices(self):
        for country, expected in [('LK',[600,1500,4500,7500]),('IN',[900,2200,6500,11000]),('GB',[900,2200,6500,11000])]:
            for plan,cents in zip(['Individual','Silver','Gold','Platinum'],expected):
                self.assertEqual(amount('Teacher',plan,country),cents)
                self.assertEqual(amount('Institute',plan,country),cents*2)
    def test_student_rates_and_plan(self):
        self.assertEqual(amount('Student','Student','LK'),50)
        self.assertEqual(amount('Student','Student','US'),150)
        with self.assertRaises(ValueError):amount('Student','Gold','LK')
    def test_country_required_and_no_browser_markets(self):
        for value in [None,'','Sri Lanka','lk','OVERSEAS','11','💡']:
            with self.assertRaises(ValueError):amount('Teacher','Gold',value)
    def test_unknown_role_or_plan_rejected(self):
        for role,plan in [('Admin','Gold'),('Teacher','Free'),('Guest','Student')]:
            with self.assertRaises(ValueError):amount(role,plan,'LK')
    def test_trial_exact_boundary(self):
        signup=datetime(2026,10,18,9,17,42);end=trial_end(signup)
        self.assertEqual(end,datetime(2026,11,1,9,17,42))
        self.assertEqual(access_state(end-timedelta(microseconds=1),end),('Trial',True))
        self.assertEqual(access_state(end,end),('Payment required',False))
    def test_paid_expiry_and_suspension(self):
        now=datetime(2026,10,18);trial=now-timedelta(days=30)
        self.assertEqual(access_state(now,trial,now+timedelta(days=1)),('Active',True))
        self.assertFalse(access_state(now,trial,now)[1])
        self.assertEqual(access_state(now,now+timedelta(days=1),None,True),('Suspended',False))
    def test_31_anchor_recovers_after_february(self):
        january=datetime(2027,1,31,10,30)
        feb=next_anniversary(january,31)
        self.assertEqual(feb,datetime(2027,2,28,10,30))
        self.assertEqual(next_anniversary(feb,31),datetime(2027,3,31,10,30))
    def test_leap_year_and_year_rollover(self):
        self.assertEqual(next_anniversary(datetime(2028,1,31),31),datetime(2028,2,29))
        self.assertEqual(next_anniversary(datetime(2026,12,30),30),datetime(2027,1,30))
    def test_29_and_30_anchors_do_not_drift(self):
        for day in [29,30]:
            feb=next_anniversary(datetime(2027,1,day),day)
            self.assertEqual(next_anniversary(feb,day).day,day)
    def test_exact_settlement_only(self):
        self.assertTrue(payment_matches(50,50,'USD'))
        for value,currency in [(49,'USD'),(51,'USD'),(50,'LKR'),('50','USD'),(50.0,'USD'),(True,'USD')]:
            self.assertFalse(payment_matches(50,value,currency))

if __name__=='__main__':unittest.main()
