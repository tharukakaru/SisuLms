import unittest
from institute_lms.programme_grading import module_grade, weight


class ProgrammeGradingTests(unittest.TestCase):
    def test_normalizes_before_averaging(self):
        grade = module_grade([dict(submitted=True, graded=True, score=8, maximum=10),
                              dict(submitted=True, graded=True, score=60, maximum=100)],
                             ['Present'] * 8 + ['Absent'] * 2)
        self.assertEqual(grade['score'], 71)
        self.assertFalse(grade['provisional'])

    def test_absent_student_with_zero_marks_can_complete(self):
        result = module_grade([dict(submitted=True, graded=True, score=0, maximum=100)], ['Absent'])
        self.assertTrue(result['can_complete'])
        self.assertEqual(result['score'], 0)

    def test_unmarked_submission_does_not_block_progress(self):
        result = module_grade([dict(submitted=True, graded=False)], [None])
        self.assertTrue(result['can_complete'])
        self.assertTrue(result['provisional'])
        self.assertEqual(result['pending_marks'], 1)

    def test_missing_submission_blocks_completion(self):
        self.assertFalse(module_grade([dict(submitted=False)], ['Present'])['can_complete'])

    def test_excused_and_no_sessions_reweight_assessments(self):
        rows = [dict(submitted=True, graded=True, score=75, maximum=100)]
        for attendance in ([], ['Excused']):
            self.assertEqual(module_grade(rows, attendance)['score'], 75)

    def test_attendance_unmarked_is_not_final_absence(self):
        result = module_grade([dict(submitted=True, graded=True, score=100, maximum=100)], [None])
        self.assertTrue(result['provisional'])
        self.assertTrue(result['can_complete'])

    def test_weights_are_validated(self):
        for invalid in ('nan', 'Infinity', -1, 101, 'bad'):
            with self.assertRaises(ValueError): weight(invalid)

    def test_no_evidence_does_not_invent_score(self):
        self.assertIsNone(module_grade([], [])['score'])

    def test_custom_weight(self):
        result = module_grade([dict(submitted=True, graded=True, score=80, maximum=100)], ['Absent'], 75)
        self.assertEqual(result['score'], 60)
