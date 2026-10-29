import unittest
from datetime import datetime
from institute_lms.payout_policy import month_bounds,last_week,slots_used,completed_in_month
from institute_lms.learning_rules import preferences

class LearningPayoutPolicy(unittest.TestCase):
    def test_calendar_boundaries(self):
        self.assertEqual(month_bounds(datetime(2026,12,31))[1],datetime(2027,1,1))
        self.assertFalse(last_week(datetime(2028,2,22)))
        self.assertTrue(last_week(datetime(2028,2,23)))
        self.assertTrue(last_week(datetime(2026,10,25)))
    def test_reserved_and_completed_count(self):
        rows=[dict(status='Completed',completed_at='2026-10-01 00:00:00'),dict(status='Completed',completed_at='2026-09-30 23:59:59'),dict(status='Pending'),dict(status='Rejected')]
        self.assertEqual(slots_used(rows,datetime(2026,10,16)),2)
        self.assertEqual(completed_in_month(rows,datetime(2026,10,16)),1)
        self.assertEqual(slots_used(rows,datetime(2026,11,1)),1)
    def test_preferences_private_payload_and_dates(self):
        result=preferences({'user':'someone-else','motto':'  Small steps.  ','event_title':'GCE A/L','event_date':'2028-02-29'})
        self.assertNotIn('user',result)
        self.assertEqual(result['motto'],'Small steps.')
        for payload in [{'motto':'a'*181},{'event_title':'A/L'},{'event_date':'2026-10-16'},{'event_title':'Exam','event_date':'2026-02-29'}]:
            with self.assertRaises(ValueError):preferences(payload)


    def test_countdown_visibility_preserves_saved_goal(self):
        result=preferences({'event_title':'GCE A/L','event_date':'2027-06-04','motto':'Keep going.','hide_countdown':True})
        self.assertEqual(result['hide_countdown'],1)
        self.assertEqual(result['event_date'],'2027-06-04')
        self.assertEqual(preferences({'hide_countdown':False})['hide_countdown'],0)
        for invalid in ['yes','0',2,-1,None]:
            with self.assertRaises(ValueError):preferences({'hide_countdown':invalid})
