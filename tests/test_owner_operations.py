import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

class OwnerOperationsTests(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.PermissionError=PermissionError;self.f.conf={'il_owner_reporting_sites':['campus.example.test']}
        self.f.throw=lambda msg,kind=ValueError:(_ for _ in ()).throw(kind(msg))
        self.owner=MagicMock();platform=types.ModuleType('institute_lms.platform');platform.owner=self.owner
        self.patch=patch.dict(sys.modules,{'frappe':self.f,'institute_lms.platform':platform});self.patch.start();self.addCleanup(self.patch.stop)
        spec=importlib.util.spec_from_file_location('institute_lms.owner_operations',Path(__file__).parents[1]/'institute_lms/owner_operations.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
    def test_guest_rejected_before_report_connection(self):
        self.owner.side_effect=PermissionError
        with patch.object(self.m,'connect') as connect:
            for fn in (self.m.billing,self.m.readiness,self.m.audit,self.m.overview):
                with self.assertRaises(PermissionError):fn()
            connect.assert_not_called()
    def test_cannot_request_unconfigured_site_or_path(self):
        with patch.object(self.m,'connect') as connect:
            for site in ('other.example.test','../private','campus.example.test/extra'):
                with self.assertRaises(PermissionError):self.m.billing(site=site)
            connect.assert_not_called()
    def test_dates_inclusive_and_invalid_inputs_rejected(self):
        first,after,page=self.m.bounds('2026-11-01','2026-11-01',2)
        self.assertEqual(str(first),'2026-11-01');self.assertEqual(str(after),'2026-11-02');self.assertEqual(page,2)
        for args in [('bad','2026-11-01',0),('2026-12-01','2026-11-01',0),('2020-01-01','2026-11-01',0),('2026-11-01','2026-11-01',-1)]:
            with self.assertRaises(ValueError):self.m.bounds(*args)
    def test_fixed_read_only_queries_pagination_and_close(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect=[[{'plan':'Gold','accounts':2}],[],[{'name':str(i)} for i in range(51)]]
        with patch.object(self.m,'connect',return_value=connection):
            value=self.m.billing(start='2026-11-01',end='2026-11-02',page=1)
        self.assertEqual(len(value['rows']),50);self.assertTrue(value['has_next'])
        calls=cursor.execute.call_args_list;self.assertEqual(calls[0].args[0],'START TRANSACTION READ ONLY')
        self.assertTrue(all('Teacher' in c.args[0] and 'Institute' in c.args[0] for c in calls[1:]))
        self.assertEqual(calls[-1].args[1][-1],50);connection.close.assert_called_once()
    def test_connection_error_never_exposes_secrets(self):
        connection=MagicMock();connection.cursor.side_effect=RuntimeError('secret password')
        with patch.object(self.m,'connect',return_value=connection):
            with self.assertRaises(ValueError) as err:self.m.billing()
        self.assertNotIn('secret',str(err.exception));connection.close.assert_called_once()
    def test_unconfigured_returns_explicit_unavailable(self):
        self.f.conf={};self.assertFalse(self.m.billing()['configured'])

    def test_overview_reads_counts_and_closes_connections(self):
        self.f.db=MagicMock();self.f.db.count.return_value=2
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value={'student_memberships':12,'teachers':3}
        with patch.object(self.m,'connect',return_value=connection):value=self.m.overview()
        self.assertTrue(value['campuses'][0]['available']);self.assertEqual(value['campuses'][0]['counts']['student_memberships'],12)
        self.assertEqual(cursor.execute.call_args_list[0].args[0],'START TRANSACTION READ ONLY');connection.close.assert_called_once()
    def test_failed_campus_count_is_not_reported_as_zero(self):
        self.f.db=MagicMock()
        with patch.object(self.m,'connect',side_effect=RuntimeError('secret')):value=self.m.overview()
        row=value['campuses'][0];self.assertFalse(row['available']);self.assertNotIn('counts',row);self.assertNotIn('secret',row['message'])

class OwnerEmailCompatibilityTests(unittest.TestCase):
    def test_private_and_legacy_reset_api_and_configured_sender(self):
        f=types.ModuleType('frappe');f.whitelist=lambda **kw:lambda fn:fn;f.db=MagicMock();f.sendmail=MagicMock()
        f.throw=lambda msg:(_ for _ in ()).throw(ValueError(msg))
        with patch.dict(sys.modules,{'frappe':f}):
            spec=importlib.util.spec_from_file_location('owner_access_email',Path(__file__).parents[1]/'institute_lms/owner_access.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            for name in ('_reset_password','reset_password'):
                reset=MagicMock(return_value='https://example.test/reset?key=a&x=b')
                user=types.SimpleNamespace(name='owner@example.test',**{name:reset})
                m.queue_setup_email(user);reset.assert_called_once_with(send_email=False)
                args=f.sendmail.call_args.kwargs;self.assertTrue(args['delayed']);self.assertTrue(args['redact_message_after_send']);self.assertNotIn('sender',args)
                self.assertEqual(args['recipients'],['owner@example.test']);self.assertIn('&amp;',args['message'])
            f.db.exists.return_value=False
            with self.assertRaises(ValueError):m.queue_setup_email(user)
