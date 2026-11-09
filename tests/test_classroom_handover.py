import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class Row(dict):
    def __getattr__(self, key): return self.get(key)
    def __setattr__(self, key, value): self[key] = value


class Handover(unittest.TestCase):
    def setUp(self):
        self.inst = Row(name='inst')
        self.member = Row(name='teacher', user='teacher@example.test', role='Teacher')
        self.room = Row(name='room', institute='inst', owner_type='Institute', teacher='teacher',
            teacher_assignment_active=1, public_provider='profile', reload=MagicMock(), save=MagicMock(), add_comment=MagicMock())
        self.doc = Row(name='request', institute='inst', classroom='room', teacher='teacher', status='Pending', flags=Row())
        self.doc.save = MagicMock(return_value=self.doc)
        self.f = types.ModuleType('frappe')
        self.f.whitelist = lambda *a, **k: lambda fn: fn
        self.f.PermissionError = PermissionError
        def throw(message, kind=ValueError): raise kind(message)
        self.f.throw = throw
        self.f.db = MagicMock(); self.f.db.get_value.return_value = None
        self.f.get_doc = MagicMock(return_value=self.doc); self.f.get_all = MagicMock(return_value=[])
        api = types.ModuleType('institute_lms.api')
        api.identity = lambda: (self.inst, self.member)
        api.classroom_for = lambda *a, **k: (self.inst, self.member, self.room)
        def scoped(dt, name, inst):
            doc = self.room if dt == 'IL Classroom' else self.doc
            if doc.institute != inst.name: raise PermissionError()
            return doc
        api.scoped = scoped
        def require_role(member, *roles):
            if member.role not in roles: raise PermissionError()
        api.require_role = require_role
        teaching = types.ModuleType('institute_lms.teaching')
        def require(room, member, action):
            if action == 'assign' and (member.role != 'Admin' or room.owner_type != 'Institute'): raise PermissionError()
            if action == 'teach' and not room.teacher_assignment_active: raise PermissionError()
        teaching.require = require
        self.approved = teaching.approved_teacher = MagicMock(return_value=Row(name='replacement'))
        utils = types.ModuleType('frappe.utils'); utils.now_datetime = lambda: '2026-11-06'
        self.modules = patch.dict(sys.modules, {'frappe': self.f, 'frappe.utils': utils,
            'institute_lms.api': api, 'institute_lms.teaching': teaching})
        self.modules.start()
        sys.modules.pop('institute_lms.classroom_handover', None)
        self.s = importlib.import_module('institute_lms.classroom_handover')

    def tearDown(self):
        sys.modules.pop('institute_lms.classroom_handover', None)
        self.modules.stop()

    def admin(self): self.member.role = 'Admin'

    def test_request_retains_assignment_and_duplicate_returns_same_request(self):
        self.assertEqual(self.s.request_leave('room', 'Please arrange a replacement')['status'], 'Pending')
        self.room.save.assert_not_called()
        self.assertEqual(self.room.teacher, 'teacher')
        self.f.db.get_value.return_value = 'existing'
        self.doc.save.reset_mock()
        self.assertEqual(self.s.request_leave('room', 'Reason')['name'], 'existing')
        self.doc.save.assert_not_called()

    def test_request_rejects_missing_reason_wrong_teacher_personal_or_inactive(self):
        for reason in (None, '', ' ', 'a' * 1001):
            with self.assertRaises(ValueError): self.s.request_leave('room', reason)
        self.room.teacher = 'other'
        with self.assertRaises(PermissionError): self.s.request_leave('room', 'Reason')
        self.room.teacher = 'teacher'; self.room.owner_type = 'Teacher'
        with self.assertRaises(PermissionError): self.s.request_leave('room', 'Reason')
        self.room.owner_type = 'Institute'; self.room.teacher_assignment_active = 0
        with self.assertRaises(PermissionError): self.s.request_leave('room', 'Reason')

    def test_only_scoped_admin_can_review(self):
        with self.assertRaises(PermissionError): self.s.review('request', 'Approved', 'replacement')
        self.admin(); self.doc.institute = 'foreign'
        with self.assertRaises(PermissionError): self.s.review('request', 'Rejected')

    def test_reject_preserves_teacher(self):
        self.admin(); self.s.review('request', 'Rejected')
        self.assertEqual(self.doc.status, 'Rejected')
        self.room.save.assert_not_called()

    def test_approval_requires_different_approved_teacher_and_current_assignment(self):
        self.admin()
        for replacement in (None, 'teacher'):
            with self.assertRaises(ValueError): self.s.review('request', 'Approved', replacement)
        self.approved.side_effect = PermissionError()
        with self.assertRaises(PermissionError): self.s.review('request', 'Approved', 'foreign')
        self.room.save.assert_not_called()
        self.approved.side_effect = None
        self.room.teacher = 'changed'
        with self.assertRaises(ValueError): self.s.review('request', 'Approved', 'replacement')

    def test_approval_assigns_replacement_and_cannot_repeat(self):
        self.admin(); self.s.review('request', 'Approved', 'replacement')
        self.assertEqual(self.room.teacher, 'replacement')
        self.assertEqual(self.room.teacher_assignment_active, 1)
        self.assertEqual(self.doc.replacement, 'replacement')
        self.assertEqual(self.doc.status, 'Approved')
        with self.assertRaises(ValueError): self.s.review('request', 'Approved', 'third')

    def test_unknown_decision_denied(self):
        self.admin()
        with self.assertRaises(ValueError): self.s.review('request', 'Deleted')
