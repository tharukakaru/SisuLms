import unittest,types,sys,importlib
from unittest.mock import MagicMock,patch
class Row(dict):
    def __getattr__(self,key):return self.get(key)
class WorkspaceSecurity(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.PermissionError=PermissionError
        def throw(message,kind=ValueError):raise kind(message)
        self.f.throw=throw;self.f.session=Row(user='operator@example.test');self.f.db=MagicMock();self.f.db.get_value.return_value=1
        self.c=types.ModuleType('institute_lms.commercial')
        for name in ('account_access','current_account','account_for','locked','locked_reason'):setattr(self.c,name,MagicMock())
        self.patch=patch.dict(sys.modules,{'frappe':self.f,'institute_lms.commercial':self.c})
        self.patch.start();self.old=sys.modules.pop('institute_lms.workspace',None)
        self.w=importlib.import_module('institute_lms.workspace')
        self.account=Row(name='provider-A',plan='Gold',institute='A');self.c.current_account.return_value=self.account;self.c.locked_reason.return_value=None
    def tearDown(self):
        sys.modules.pop('institute_lms.workspace',None)
        if self.old:sys.modules['institute_lms.workspace']=self.old
        self.patch.stop()
    def test_provider_identity_must_be_authorized(self):
        self.c.account_access.side_effect=PermissionError('Foreign provider')
        with self.assertRaises(PermissionError):self.w.actor()
    def test_guest_is_denied_before_provider_lookup(self):
        self.f.session.user='Guest'
        with self.assertRaises(PermissionError):self.w.actor()
        self.c.current_account.assert_not_called()
    def test_foreign_expense_cannot_be_voided(self):
        self.w.actor=MagicMock(return_value=(self.account,False));self.c.locked.return_value=Row(kind='Expense',provider_account='provider-B')
        self.w.save=MagicMock()
        with self.assertRaises(PermissionError):self.w.void_expense('foreign','Valid reason')
        self.w.save.assert_not_called()
    def test_operator_cannot_void_another_operators_entry(self):
        self.w.actor=MagicMock(return_value=(self.account,True));self.c.locked.return_value=Row(kind='Expense',provider_account='provider-A',subject_user='someone-else')
        with self.assertRaises(PermissionError):self.w.void_expense('record','Valid reason')
    def test_gold_operator_seats_enforced_on_read_after_downgrade(self):
        self.w.active_operator=MagicMock(return_value=Row(name='seat-3',provider_account='provider-A'))
        self.f.get_doc=MagicMock(return_value=self.account);self.f.get_all=MagicMock(return_value=['seat-1','seat-2'])
        with self.assertRaises(PermissionError):self.w.actor(True)
    def test_view_limit_rejects_before_mutating_counter(self):
        self.c.account_for.return_value=self.account;self.w.settings_for=lambda _:dict(document_views=2)
        self.f.db.get_value.return_value='counter';self.f.get_doc=MagicMock(return_value=Row(payload='{"count":2}'));self.w.record=MagicMock()
        with self.assertRaises(PermissionError):self.w.consume_view(Row(name='room'),Row(role='Student',user='student'),'material:1','document')
        self.w.record.assert_not_called()
