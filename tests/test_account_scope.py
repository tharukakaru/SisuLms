import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

class AccountScope(unittest.TestCase):
    def test_controls_reuse_classroom_visibility_and_scope_enrolments(self):
        f=types.ModuleType('frappe'); f.whitelist=lambda **kw:lambda fn:fn
        f.get_all=MagicMock(side_effect=[['own-room'],[],[]]);f.session=types.SimpleNamespace(user='owner')
        api=types.ModuleType('institute_lms.api')
        inst=types.SimpleNamespace(name='I1');member=types.SimpleNamespace(name='A1',role='Admin')
        api.identity=lambda:(inst,member)
        for name in ['require_role','scoped','classroom_for','payload','set_member_active']:setattr(api,name,MagicMock())
        api.room_filters=MagicMock(return_value={'institute':'I1','active':1,'owner_type':'Institute'})
        previous=sys.modules.pop('institute_lms.accounts',None)
        try:
            with patch.dict(sys.modules,{'frappe':f,'institute_lms.api':api}):
                module=importlib.import_module('institute_lms.accounts');module.account_controls()
                api.room_filters.assert_called_once_with(inst,member)
                self.assertEqual(f.get_all.call_args_list[0].kwargs['filters']['owner_type'],'Institute')
                self.assertEqual(f.get_all.call_args_list[1].kwargs['filters']['classroom'],['in',['own-room']])
                self.assertEqual(f.get_all.call_args_list[1].kwargs['filters']['institute'],'I1')
        finally:
            sys.modules.pop('institute_lms.accounts',None)
            if previous is not None:sys.modules['institute_lms.accounts']=previous
