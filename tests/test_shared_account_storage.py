import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch


class Config(dict):
    __getattr__ = dict.__getitem__


class SharedStorage(TestCase):
    def setUp(self):
        self.config = Config(il_shared_campus_enabled=1, il_account_storage_bytes=1000)
        self.f = SimpleNamespace(conf=self.config, db=Mock(), throw=lambda message: (_ for _ in ()).throw(ValueError(message)))
        self.patch = patch.dict(sys.modules, {'frappe': self.f,
            'institute_lms.api': SimpleNamespace(institute=lambda: SimpleNamespace(name='joined-institute'))})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        spec = importlib.util.spec_from_file_location('institute_lms._shared_storage_test', Path(__file__).parents[1]/'institute_lms/account_storage.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_shared_site_uses_explicit_quota_without_usage_billing(self):
        self.assertTrue(self.module.configured())
        self.assertEqual(self.module.capacity(lambda: 900, 100), 1000)
        self.f.db.sql.assert_called_once()
        with self.assertRaises(ValueError):
            self.module.capacity(lambda: 900, 101)
        self.assertNotIn('il_usage_billing_enabled', self.config)

    def test_no_implicit_or_unbounded_allocation(self):
        for value in (None, True, '1000', 0, -1, 1024**4+1):
            self.config['il_account_storage_bytes'] = value
            self.assertFalse(self.module.configured())

    def test_tenant_and_control_plane_keep_existing_boundary(self):
        for flag in ('il_tenant_id', 'il_control_plane'):
            self.config[flag] = 1
            self.assertFalse(self.module.configured())
            del self.config[flag]
        self.config['il_shared_campus_enabled'] = 0
        self.assertFalse(self.module.configured())
        self.config['il_usage_billing_enabled'] = 1
        self.assertTrue(self.module.configured())
