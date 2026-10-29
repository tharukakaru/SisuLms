import unittest
from datetime import datetime, timedelta
from institute_lms.material_availability import deadline,expired,require_available
class Availability(unittest.TestCase):
    def setUp(self):self.now=datetime(2026,10,27,8)
    def test_permanent_and_exact_deadline(self):
        self.assertIsNone(deadline('',self.now))
        end=deadline('10',self.now)
        self.assertFalse(expired(end,end-timedelta(microseconds=1)))
        self.assertTrue(expired(end,end))
    def test_student_denied_teacher_can_edit(self):
        end=deadline(10,self.now)
        with self.assertRaises(PermissionError):require_available(end,'Student',end)
        require_available(end,'Teacher',end)
        require_available(end,'Admin',end)
    def test_extension_reopens(self):
        later=self.now+timedelta(days=11)
        require_available(deadline(10,later),'Student',later)
        self.assertFalse(expired(None,later))
    def test_invalid_intervals(self):
        for v in (-1,0,True,'1.5','tomorrow',36501):
            with self.assertRaises(ValueError):deadline(v,self.now)
