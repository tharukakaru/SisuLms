"""Service-boundary authorization checks. Real Frappe transaction tests remain required."""
import importlib
import sys
import types
import unittest
from datetime import datetime,timedelta
from unittest.mock import MagicMock,patch

class RevisionAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names=('frappe','frappe.utils','institute_lms.wallet','institute_lms.api','institute_lms.owner_pricing','institute_lms.papers','institute_lms.registration','institute_lms.operations')
        cls.previous={k:sys.modules.get(k) for k in cls.names}
        cls.f=types.ModuleType('frappe');cls.f.whitelist=lambda **kw:lambda fn:fn;cls.f.PermissionError=PermissionError
        def throw(message,kind=ValueError):raise kind(message)
        cls.f.throw=throw
        u=types.ModuleType('frappe.utils');u.now_datetime=lambda:datetime(2026,9,27,12);u.get_datetime=lambda v:datetime.fromisoformat(str(v))
        w=types.ModuleType('institute_lms.wallet');w.owner=MagicMock();w.signed_in=MagicMock();w.audit=MagicMock()
        a=types.ModuleType('institute_lms.api')
        for n in ('identity','room_filters','classroom_for','accessible_room','require_role','scoped'):setattr(a,n,MagicMock())
        r=types.ModuleType('institute_lms.registration');r.limit=MagicMock()
        sys.modules.update({'frappe':cls.f,'frappe.utils':u,'institute_lms.wallet':w,'institute_lms.api':a,'institute_lms.registration':r})
        for n in ('institute_lms.owner_pricing','institute_lms.papers'):sys.modules.pop(n,None)
        cls.pricing=importlib.import_module('institute_lms.owner_pricing');cls.papers=importlib.import_module('institute_lms.papers')
        cls.operations=importlib.import_module('institute_lms.operations')
    @classmethod
    def tearDownClass(cls):
        for k,v in cls.previous.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
    def setUp(self):
        gate=types.ModuleType('institute_lms.saas');gate.require=MagicMock()
        accounting=types.ModuleType('institute_lms.usage');accounting.consume=MagicMock()
        modules=patch.dict(sys.modules,{'institute_lms.saas':gate,'institute_lms.usage':accounting})
        modules.start();self.addCleanup(modules.stop)
        self.f.session=types.SimpleNamespace(user='student@example.invalid');self.f.db=MagicMock();self.f.get_doc=MagicMock();self.f.get_all=MagicMock()
        self.pricing.owner.reset_mock(side_effect=True)
    def test_nonowner_cannot_assign_or_grant(self):
        self.pricing.owner.side_effect=PermissionError('owner required')
        with self.assertRaises(PermissionError):self.pricing.assign({})
        with self.assertRaises(PermissionError):self.pricing.grant('x','AI Papers','2026-10-01','why')
        self.f.get_doc.assert_not_called()
    def test_missing_and_duplicate_contracts_fail_closed(self):
        for names in ([],['a','b']):
            self.f.get_all.return_value=names
            with self.assertRaises(ValueError):self.pricing.current('x','AI Papers')
    def test_retired_usage_quote_cannot_create_charge(self):
        with self.assertRaisesRegex(ValueError, 'retired'):
            self.pricing.quote('AI Papers')
        self.f.get_doc.assert_not_called()
        self.f.db.count.assert_not_called()
    def test_quote_cross_account_and_expiry_rejected(self):
        q=types.SimpleNamespace(customer='other',status='Open',expires_at=datetime(2026,9,28))
        self.f.get_doc.return_value=q
        with self.assertRaises(ValueError):self.pricing.validate_quote('q',self.f.session.user)
        q.customer=self.f.session.user;q.expires_at=datetime(2026,9,27,12)
        with self.assertRaises(ValueError):self.pricing.validate_quote('q',self.f.session.user)
    def test_ai_generation_without_premium_stops_before_provider(self):
        self.papers.classroom_for.return_value=(types.SimpleNamespace(name='I'),types.SimpleNamespace(role='Teacher'),types.SimpleNamespace(name='C'))
        with patch.object(sys.modules['institute_lms.saas'],'require',side_effect=PermissionError('Plan feature unavailable')):
            with self.assertRaises(PermissionError):self.papers.generate('C','Fractions')
    def test_foreign_attempt_and_expired_attempt_cannot_submit(self):
        a=types.SimpleNamespace(paper='P',student='someone',status='Started',deadline=datetime(2026,9,27,11),reload=lambda:None)
        self.f.get_doc.return_value=a
        with patch.object(self.papers,'checked',return_value=(types.SimpleNamespace(),types.SimpleNamespace(name='me',role='Student'),None)):
            with self.assertRaises(PermissionError):self.papers.submit('A',[])
            a.student='me'
            with self.assertRaises(ValueError):self.papers.submit('A',[])
    def test_support_ticket_is_private_to_requester_or_institute_admin(self):
        with patch.object(self.operations,'identity',return_value=(types.SimpleNamespace(name='I'),types.SimpleNamespace(role='Teacher'))),patch.object(self.operations,'scoped',return_value=types.SimpleNamespace(requester='another-user')):
            with self.assertRaises(PermissionError):self.operations.ticket_for('private-ticket')
    def test_attendance_student_filter_cannot_be_removed_by_request(self):
        self.f.get_all.return_value=[]
        with patch.object(self.operations,'classroom_for',return_value=(types.SimpleNamespace(name='I'),types.SimpleNamespace(name='S1',role='Student'),types.SimpleNamespace(name='C1'))):
            self.operations.attendance('C1')
            self.assertEqual(self.f.get_all.call_args.kwargs['filters']['student'],'S1')
    def test_online_rejoin_does_not_overwrite_teacher_register(self):
        self.f.db.get_value.return_value='A1'
        self.f.get_doc.return_value=types.SimpleNamespace(name='A1',status='Excused')
        with patch.object(self.operations,'save') as save:
            result=self.operations.record(types.SimpleNamespace(institute='I',name='C'),types.SimpleNamespace(name='M'),'S','Present','Online','')
            self.assertEqual(result['status'],'Excused');save.assert_not_called()
