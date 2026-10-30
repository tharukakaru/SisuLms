"""Execute actual guard functions with doubles: no site, config writes or database."""
import ast
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

ROOT=Path(__file__).resolve().parents[1]/'institute_lms'


def function(module, name, env):
    tree=ast.parse((ROOT/(module+'.py')).read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    node.decorator_list=[]
    env.update(__name__='institute_lms.'+module,__package__='institute_lms')
    exec(compile(ast.Module(body=[node],type_ignores=[]),module+'.py','exec'),env)
    return env[name]


class UploadProvisioning(unittest.TestCase):
    def setUp(self):
        self.f=types.SimpleNamespace(conf={},flags={},db=MagicMock(),get_doc=MagicMock())
        self.f.PermissionError=PermissionError
        def throw(message,kind=ValueError):raise kind(message)
        self.f.throw=throw
        self.env={'frappe':self.f}
        self.state=function('saas','state',self.env)

    def test_institute_and_membership_do_not_substitute_for_tenant_config(self):
        self.f.db.get_value.return_value='INVTEST'
        with self.assertRaisesRegex(PermissionError,'SaaS tenant must be provisioned before use'):
            self.state()
        self.f.db.get_value.assert_not_called()

    def test_workspace_preflight_preserves_missing_tenant_error(self):
        api=types.ModuleType('institute_lms.api');api.identity=MagicMock(return_value=(types.SimpleNamespace(name='INVTEST'),types.SimpleNamespace(role='Teacher')))
        saas=types.ModuleType('institute_lms.saas');saas.resolved=lambda:self.state()
        usage=types.ModuleType('institute_lms.usage');usage.summary=MagicMock();usage.used=MagicMock()
        workspace=function('release','workspace',{'frappe':self.f})
        with patch.dict(sys.modules,{'institute_lms.api':api,'institute_lms.saas':saas,'institute_lms.usage':usage}):
            with self.assertRaisesRegex(PermissionError,'SaaS tenant must be provisioned before use'):workspace()
        api.identity.assert_called_once();usage.used.assert_not_called()

    def test_storage_hook_still_rejects_missing_provisioning_without_preflight(self):
        self.env.update(resolved=MagicMock(),check_capacity=MagicMock())
        quota=function('saas','quota',self.env)
        before_write=function('storage','before_write',{'frappe':self.f,'quota':quota,'used':MagicMock()})
        with self.assertRaisesRegex(PermissionError,'SaaS tenant must be provisioned before use'):before_write(100)
        self.env['check_capacity'].assert_not_called()

    def test_configured_tenant_must_match_subscription_and_uses_lock(self):
        self.f.conf={'il_tenant_id':'org-approved-registry-id'}
        self.f.db.get_value.return_value=None
        with self.assertRaisesRegex(PermissionError,'Subscription not configured'):self.state()
        self.f.db.get_value.assert_called_with('IL Subscription',{'tenant_id':'org-approved-registry-id'},'name')
        self.f.db.get_value.return_value='subscription-1'
        self.state(lock=True)
        self.assertIn('FOR UPDATE',self.f.db.sql.call_args.args[0])
        self.f.get_doc.assert_called_with('IL Subscription','subscription-1',for_update=True)


if __name__=='__main__':unittest.main()
