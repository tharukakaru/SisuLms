import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

spec=importlib.util.spec_from_file_location('server_email_prepare',Path(__file__).parents[1]/'scripts/prepare-server-email.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class EmailPreparation(unittest.TestCase):
    def fake(self,key='',encrypted=0,accounts=0,missing=False):
        db=MagicMock();db.sql.return_value=[[encrypted]];db.count.return_value=accounts
        return SimpleNamespace(conf={'encryption_key':key},db=db,get_meta=lambda dt:SimpleNamespace(has_field=lambda name:not(missing and name=='smtp_server')))
    def check(self,f,initialize=False):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):result=m.target_preflight(f,'teen.sisuacademylk.com',initialize)
        self.assertNotIn('secret-value',out.getvalue())
        return result
    def test_missing_key_requires_explicit_initialization(self):
        self.assertFalse(self.check(self.fake()))
        self.assertTrue(self.check(self.fake(),True))
    def test_existing_encrypted_secrets_block_new_key(self):
        f=self.fake(encrypted=1)
        self.assertFalse(self.check(f,True))
        with self.assertRaises(ValueError):m.initialize_site_key(f,'teen.sisuacademylk.com')
    def test_existing_key_never_replaced(self):
        f=self.fake(key='secret-value',encrypted=3)
        self.assertTrue(self.check(f))
        self.assertFalse(m.initialize_site_key(f,'teen.sisuacademylk.com'))
        self.assertEqual(f.conf['encryption_key'],'secret-value')
        f.db.sql.assert_not_called()
    def test_schema_and_account_conflicts_block(self):
        self.assertFalse(self.check(self.fake(key='secret-value',missing=True),True))
        self.assertFalse(self.check(self.fake(key='secret-value',accounts=1),True))
