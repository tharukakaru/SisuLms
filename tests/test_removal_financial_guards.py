from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from institute_lms.hosting_removal_adapter import BenchRemovalAdapter


class FinancialRemovalGuards(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.adapter = object.__new__(BenchRemovalAdapter)
        self.adapter.root = Path(temporary.name);self.adapter.db = 'dummy'
        self.blocked = None
        self.tables = {'tabIL Account Invoice', 'tabIL Payout Request', 'tabIL Payment Attempt',
                       'tabIL Wallet', 'tabIL Invoice', 'tabIL Provider Invoice', 'tabIL Usage Invoice', 'tabIL Lecture Refund'}
        def sql(query):
            if 'information_schema.TABLES' in query:return '\n'.join(self.tables)
            if 'information_schema.COLUMNS' in query:return 'available_minor\nheld_minor'
            return '1' if self.blocked and self.blocked in query else '0'
        self.adapter.sql = sql

    def test_all_reviewed_obligations_and_balances_block(self):
        for marker in ('tabIL Account Invoice', 'tabIL Payout Request', 'tabIL Payment Attempt',
                       'tabIL Invoice', 'tabIL Provider Invoice', 'tabIL Usage Invoice', 'tabIL Lecture Refund',
                       'available_minor', 'held_minor'):
            with self.subTest(marker=marker):
                self.blocked = marker
                with self.assertRaises(ValueError):self.adapter.check_dependencies(None)

    def test_settled_finances_can_continue(self):
        self.adapter.check_dependencies(None)

    def test_unknown_schema_cannot_be_assumed_empty(self):
        self.tables.remove('tabIL Wallet')
        with self.assertRaises(ValueError):self.adapter.check_dependencies(None)
