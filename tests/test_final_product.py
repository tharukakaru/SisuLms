import unittest
from datetime import datetime, timedelta
from institute_lms.full_rules import final_policy, month_end, credit_check

class FinalProductPolicy(unittest.TestCase):
    def record(self, **changes):
        now=datetime(2026,10,6)
        return dict(dict(plan='PREMIUM AI',state='active',enabled=1,lease_until=now+timedelta(days=1),
            ends_at=now+timedelta(days=10),features={'lms':True,'ai.assistant':True},limits={'ai_credits':30}),**changes)
    def test_expiry_preserves_starter(self):
        p=final_policy(self.record(ends_at='2026-10-01'),datetime(2026,10,6))
        self.assertTrue(p['available']);self.assertEqual(p['plan'],'STARTER');self.assertFalse(p['features']['ai.assistant'])
    def test_disabled_organization_remains_blocked(self):
        self.assertFalse(final_policy(self.record(enabled=0),datetime(2026,10,6))['available'])
    def test_expired_signed_lease_fails_closed(self):
        self.assertFalse(final_policy(self.record(lease_until='2026-10-01'),datetime(2026,10,6))['available'])
    def test_active_premium(self):
        self.assertTrue(final_policy(self.record(),datetime(2026,10,6))['features']['ai.assistant'])
    def test_calendar_month(self):
        self.assertEqual(month_end('2027-01-31').day,28)
        self.assertEqual(month_end('2028-01-31').day,29)
    def test_shared_ignores_individual_allocation(self):
        self.assertTrue(credit_check('Shared',0,10,10,30,5))
    def test_unallocated_individual_denied(self):
        with self.assertRaisesRegex(ValueError,'No AI credits'):credit_check('Individual',0,0,0,30,1)
    def test_individual_cap(self):
        with self.assertRaisesRegex(ValueError,'Your AI'):credit_check('Individual',5,5,5,30,1)
    def test_shared_cap(self):
        with self.assertRaisesRegex(ValueError,'Organization'):credit_check('Shared',100,0,30,30,1)
