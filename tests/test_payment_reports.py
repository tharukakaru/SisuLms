import importlib
import sys
import types
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from institute_lms.report_dates import report_window

class ReportDates(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(report_window(today=date(2028,2,12)),(date(2028,2,1),date(2028,3,1)))
        self.assertEqual(report_window('2026-12-31','2026-12-31'),(date(2026,12,31),date(2027,1,1)))
        for args in [('2026-02-30','2026-03-01'),('2026-10-20','2026-10-01'),(None,'2026-10-01')]:
            with self.assertRaises(ValueError):report_window(*args)

class InvoiceReport(unittest.TestCase):
    def test_scopes_totals_and_pagination(self):
        f=types.ModuleType('frappe'); f.whitelist=lambda **kw:lambda fn:fn
        f.PermissionError=PermissionError
        def throw(message,kind=ValueError):raise kind(message)
        f.throw=throw; f.db=MagicMock();f.db.count.return_value=60
        f.get_all=MagicMock(return_value=[])
        api=types.ModuleType('institute_lms.api');member=types.SimpleNamespace(name='S1',role='Student')
        api.identity=lambda:(types.SimpleNamespace(name='I1'),member)
        api.room_filters=MagicMock(return_value={'teacher':'T1'})
        util=types.ModuleType('frappe.utils');util.now_datetime=lambda:datetime(2026,10,16)
        previous=sys.modules.pop('institute_lms.payment_reports',None)
        try:
            with patch.dict(sys.modules,{'frappe':f,'frappe.utils':util,'institute_lms.api':api}):
                report=importlib.import_module('institute_lms.payment_reports')
                r=report.history(status='Paid',page=1)
                self.assertEqual(r['count'],60)
                row_query=f.get_all.call_args.kwargs
                self.assertEqual(row_query['filters']['student'],'S1')
                self.assertEqual(row_query['filters']['institute'],'I1')
                self.assertEqual(row_query['filters']['due_date'],['between',['2026-10-01','2026-10-31']])
                self.assertEqual(row_query['limit_start'],25)
                member.role='Teacher';f.get_all.reset_mock()
                report.history()
                self.assertEqual(f.get_all.call_args.kwargs['filters']['classroom'],['in',['__none__']])
                api.room_filters.assert_called()
                member.role='Other'
                with self.assertRaises(PermissionError):report.history()
        finally:
            sys.modules.pop('institute_lms.payment_reports',None)
            if previous is not None:sys.modules['institute_lms.payment_reports']=previous
