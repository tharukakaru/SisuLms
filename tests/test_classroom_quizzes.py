"""Pure and mocked service tests. Never connects to a Frappe site/database."""
import importlib
import json
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from institute_lms.classroom_quiz_rules import normalize, grade, public_questions


def question():
    return {'prompt': 'Two plus two?', 'options': ['1', '2', '3', '4'], 'answer': 3}


class Rules(unittest.TestCase):
    def test_limits(self):
        for n in (1, 50):
            self.assertEqual(len(normalize({'title': 'Quiz', 'questions': [question() for _ in range(n)]}, True)['questions']), n)
        for n in (0, 51):
            with self.assertRaises(ValueError):
                normalize({'title': 'Quiz', 'questions': [question() for _ in range(n)]}, True)

    def test_incomplete_drafts(self):
        self.assertEqual(normalize({})['questions'], [])
        q = {'prompt': '', 'options': ['', '', '', ''], 'answer': None}
        normalize({'questions': [q]})
        with self.assertRaises(ValueError): normalize({'title': 'Quiz', 'questions': [q]}, True)

    def test_exact_options_and_single_correct(self):
        for options in ([], ['a']*3, ['a']*5, ['a', 'b', 'c', ' ']):
            with self.assertRaises(ValueError): normalize({'title': 'Quiz', 'questions': [{**question(), 'options': options}]}, True)
        for answer in (True, False, '0', [0, 1], -1, 4, None):
            with self.assertRaises(ValueError): normalize({'title': 'Quiz', 'questions': [{**question(), 'answer': answer}]}, True)

    def test_required_title_and_prompt(self):
        for data in ({'title':' ', 'questions':[question()]}, {'title':'Quiz', 'questions':[{**question(),'prompt':' '}]}):
            with self.assertRaises(ValueError): normalize(data, True)

    def test_grading_and_answer_key_projection(self):
        rows = [question(), question()]
        self.assertEqual(grade(rows, [3, 0]), {'score':1, 'total':2, 'percentage':50.0, 'correctness':[True, False]})
        self.assertEqual(set(public_questions(rows)[0]), {'prompt', 'options'})
        for answers in ([3], [3, None], [3, True], [3, 4], [3, -1]):
            with self.assertRaises(ValueError): grade(rows, answers)


class Record(dict):
    def __getattr__(self, key): return self.get(key)
    def __setattr__(self, key, value): self[key] = value


class Boundary(unittest.TestCase):
    def setUp(self):
        frappe = types.ModuleType('frappe')
        frappe.whitelist = lambda *a, **k: lambda f: f
        frappe.PermissionError = PermissionError
        def throw(message, kind=ValueError): raise kind(message)
        frappe.throw = throw
        frappe.session = Record(user='student@example.com')
        frappe.db = MagicMock()
        frappe.db.exists.return_value = False
        frappe.db.get_value.return_value = None
        frappe.db.sql.return_value = []
        frappe.get_doc = MagicMock()
        frappe.get_all = MagicMock(return_value=[])
        utils = types.ModuleType('frappe.utils'); utils.now_datetime = datetime.now
        api = types.ModuleType('institute_lms.api'); api.accessible_room = MagicMock()
        teaching = types.ModuleType('institute_lms.teaching'); teaching.rights = MagicMock(return_value={'edit':True})
        self.modules = patch.dict(sys.modules, {'frappe':frappe, 'frappe.utils':utils, 'institute_lms.api':api, 'institute_lms.teaching':teaching})
        self.modules.start()
        self.old = sys.modules.pop('institute_lms.classroom_quizzes', None)
        self.service = importlib.import_module('institute_lms.classroom_quizzes')
        self.frappe, self.api, self.teaching = frappe, api, teaching
        self.member = Record(role='Student', name='member-1', user=frappe.session.user)
        self.room = Record(name='room-1', institute='inst-1')
        api.accessible_room.return_value = (Record(name='inst-1'), self.member, self.room)
        self.quiz = Record(name='quiz-1', classroom='room-1', institute='inst-1', status='Published',
            title='Quiz', instructions='', questions=json.dumps([question()]), modified='revision-1')
        frappe.get_doc.return_value = self.quiz

    def tearDown(self):
        sys.modules.pop('institute_lms.classroom_quizzes', None)
        if self.old: sys.modules['institute_lms.classroom_quizzes'] = self.old
        self.modules.stop()

    def teacher(self):
        self.member.role = 'Teacher'

    def test_metadata_missing_schema_preserves_management_permission(self):
        self.teacher()
        self.frappe.db.exists.return_value = False
        result = self.service.metadata('room-1')
        self.assertTrue(result['can_manage'])
        self.assertFalse(result['schema_ready'])
        self.assertEqual(result['missing_schema'], [self.service.QUIZ, self.service.ATTEMPT])
        self.frappe.get_all.assert_not_called()
        self.frappe.db.get_table_columns.assert_not_called()

    def test_metadata_ready_with_no_quiz_records(self):
        self.teacher()
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/'institute_lms/institute_lms/doctype'
        def columns(doctype):
            slug=doctype.lower().replace(' ', '_')
            return [f['fieldname'] for f in json.loads((root/slug/(slug+'.json')).read_text())['fields']]
        self.frappe.db.exists.return_value = True
        self.frappe.db.table_exists.return_value = True
        self.frappe.db.get_table_columns.side_effect = columns
        result=self.service.metadata('room-1')
        self.assertEqual(result, {'can_manage':True,'schema_ready':True,'missing_schema':[]})
        self.frappe.get_all.assert_not_called()
        self.frappe.db.get_table_columns.side_effect = None
        self.frappe.db.get_table_columns.return_value = ['name']
        self.assertFalse(self.service.metadata('room-1')['schema_ready'])

    def test_metadata_rechecks_authorization_and_propagates_db_errors(self):
        self.teacher();self.teaching.rights.return_value={'edit':False}
        with self.assertRaises(PermissionError): self.service.metadata('room-1')
        self.teaching.rights.return_value={'edit':True}
        self.frappe.db.exists.side_effect=RuntimeError('connection unavailable')
        with self.assertRaises(RuntimeError): self.service.metadata('room-1')

    def test_student_draft_list_and_detail(self):
        self.service.listing('room-1')
        self.assertEqual(self.frappe.get_all.call_args.kwargs['filters']['status'], 'Published')
        self.quiz.status = 'Draft'
        for method in (self.service.detail, self.service.submissions):
            with self.assertRaises(PermissionError): method('quiz-1')

    def test_every_endpoint_rechecks_classroom_access(self):
        self.api.accessible_room.side_effect = PermissionError('Enrollment/provider/subscription denied')
        calls = [lambda:self.service.listing('room-1'),lambda:self.service.detail('quiz-1'),
                 lambda:self.service.submissions('quiz-1'),lambda:self.service.submit('quiz-1',[3]),
                 lambda:self.service.save({'classroom':'room-1'})]
        for call in calls:
            with self.assertRaises(PermissionError): call()

    def test_foreign_institute_rejected(self):
        self.quiz.institute = 'other'
        with self.assertRaises(PermissionError): self.service.detail('quiz-1')

    def test_teacher_requires_management_even_for_keys_and_results(self):
        self.teacher(); self.teaching.rights.return_value = {'edit':False}
        for call in (lambda:self.service.detail('quiz-1'),lambda:self.service.listing('room-1'),
                     lambda:self.service.submissions('quiz-1'),lambda:self.service.save({'classroom':'room-1'})):
            with self.assertRaises(PermissionError): call()

    def test_student_payload_and_results_exclude_keys(self):
        detail = self.service.detail('quiz-1')
        self.assertEqual(set(detail['questions'][0]), {'prompt','options'})
        self.service.submissions('quiz-1')
        args = self.frappe.get_all.call_args.kwargs
        self.assertEqual(args['filters']['student_user'], self.frappe.session.user)
        for field in ('snapshot','answers','correctness','student_user'):
            self.assertNotIn(field, args['fields'])

    def test_teacher_keys_and_results(self):
        self.teacher()
        self.assertEqual(self.service.detail('quiz-1')['questions'][0]['answer'],3)
        self.service.submissions('quiz-1')
        self.assertIn('snapshot', self.frappe.get_all.call_args.kwargs['fields'])

    def test_student_cannot_author(self):
        with self.assertRaises(PermissionError): self.service.save({'classroom':'room-1'})

    def test_submit_grades_on_server_and_returns_only_summary(self):
        self.frappe.get_doc.side_effect = lambda *a, **k: Record(a[0],name='submission-1') if isinstance(a[0],dict) else self.quiz
        with patch.object(self.service,'write',side_effect=lambda d:d) as write:
            result = self.service.submit('quiz-1',[3])
        self.assertEqual(result['score'],1)
        self.assertEqual(result['percentage'],100)
        self.assertNotIn('snapshot',result)
        self.assertNotIn('correctness',result)
        self.assertEqual(write.call_args.args[0].classroom,'room-1')
        self.assertEqual(write.call_args.args[0].student_user,self.frappe.session.user)

    def test_duplicate_submit_returns_original_without_write(self):
        saved = Record(name='existing',score=1,total=1,percentage=100)
        self.frappe.db.sql.side_effect = lambda sql,args: [('existing',)] if 'attempt_key=' in sql else []
        self.frappe.get_doc.side_effect = lambda dt,*a,**k: saved if dt==self.service.ATTEMPT else self.quiz
        with patch.object(self.service,'write') as write:
            self.assertEqual(self.service.submit('quiz-1',[0])['score'],1)
            write.assert_not_called()
        queries=[call.args[0] for call in self.frappe.db.sql.call_args_list]
        self.assertIn('FOR UPDATE',queries[0])
        self.assertIn('FOR UPDATE',queries[1])

    def test_cannot_edit_after_submission(self):
        self.teacher()
        self.frappe.db.sql.side_effect = lambda sql,args: [('existing',)] if 'Submission' in sql else []
        with self.assertRaisesRegex(ValueError,'cannot be edited'):
            self.service.save({'name':'quiz-1','classroom':'room-1','modified':'revision-1'})

    def test_stale_editor_rejected(self):
        self.teacher()
        with self.assertRaisesRegex(ValueError,'changed'):
            self.service.save({'name':'quiz-1','classroom':'room-1','modified':'old'})

    def test_unique_submission_constraint_and_no_generic_permissions(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/'institute_lms/institute_lms/doctype'
        schema=json.loads((root/'il_classroom_quiz_submission/il_classroom_quiz_submission.json').read_text())
        self.assertEqual(next(f for f in schema['fields'] if f['fieldname']=='attempt_key')['unique'],1)
        self.assertEqual(schema['permissions'],[])
        self.assertEqual(json.loads((root/'il_classroom_quiz/il_classroom_quiz.json').read_text())['permissions'],[])


if __name__ == '__main__': unittest.main()
