import hashlib,json,tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock
from institute_lms.hosting_retirement import RemovalIdentity,execute,verify_backups

class HostingRemoval(TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.identity=RemovalIdentity('org-'+'a'*32,'disposable.example.invalid','TEST','request_123')
  self.allow={self.identity.tenant:self.identity.hostname};self.adapter=MagicMock();self.adapter.verify_absent.return_value=True
  self.receipt={}
  for kind in ('database','public_files','private_files','configuration'):
   p=self.root/kind;p.write_bytes(b'isolated-test-artifact')
   self.receipt[kind]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  self.adapter.backup.return_value=self.receipt
 def run_worker(self):return execute(self.identity,self.adapter,self.root/'journal.json',self.root,self.allow)
 def test_success_releases_only_after_verified_absence(self):
  self.assertEqual(self.run_worker()['stage'],'completed')
  calls=[x[0] for x in self.adapter.method_calls]
  self.assertLess(calls.index('backup'),calls.index('decommission'))
  self.assertLess(calls.index('verify_absent'),calls.index('complete_registry'))
 def test_completed_retry_does_not_repeat_destruction(self):
  self.run_worker();self.run_worker();self.adapter.decommission.assert_called_once()
 def test_unsettled_obligations_stop_before_backup_or_drop(self):
  self.adapter.check_dependencies.side_effect=ValueError('obligations')
  with self.assertRaises(ValueError):self.run_worker()
  self.adapter.decommission.assert_not_called()
 def test_corrupt_backup_blocks_destruction(self):
  self.receipt['database']['sha256']='bad'
  with self.assertRaises(ValueError):self.run_worker()
  self.adapter.decommission.assert_not_called()
 def test_failed_drop_does_not_release_and_retry_reuses_backup(self):
  self.adapter.decommission.side_effect=[RuntimeError('failure'),None]
  with self.assertRaises(RuntimeError):self.run_worker()
  self.adapter.complete_registry.assert_not_called();self.run_worker();self.adapter.backup.assert_called_once()
 def test_absence_failure_does_not_release(self):
  self.adapter.verify_absent.return_value=False
  with self.assertRaises(RuntimeError):self.run_worker()
  self.adapter.complete_registry.assert_not_called()
 def test_protected_host_rejected(self):
  self.identity=RemovalIdentity(self.identity.tenant,'platform.sisuacademylk.com','TEST','request_123')
  self.allow[self.identity.tenant]=self.identity.hostname
  with self.assertRaises(ValueError):self.run_worker()
  self.adapter.authorize_request.assert_not_called()
 def test_request_change_cannot_reuse_another_journal(self):
  self.run_worker();self.identity=RemovalIdentity(self.identity.tenant,self.identity.hostname,'TEST','request_456')
  with self.assertRaises(ValueError):self.run_worker()
 def test_incomplete_receipt_rejected(self):
  del self.receipt['configuration']
  with self.assertRaises(ValueError):verify_backups(self.receipt,self.root)
 def test_unknown_tenant_rejected(self):
  self.allow={}
  with self.assertRaises(ValueError):self.run_worker()
