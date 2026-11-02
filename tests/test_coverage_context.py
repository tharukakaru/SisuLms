from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock, patch
from test_upload_provisioning import function


class CoverageContext(TestCase):
    def setUp(self):
        self.shared=True
        self.member=NS(role='Teacher',user='teacher')
        self.identity=MagicMock(return_value=(NS(name='selected-B'),self.member))
        self.sponsor=MagicMock(return_value={'account':'institute-plan'})
        self.enabled=MagicMock(return_value=True)
        self.account=NS(role='Teacher',user='teacher',institute='original-A')
        p=patch.dict('sys.modules',{'institute_lms.api':NS(identity=self.identity),
            'institute_lms.campus_context':NS(enabled=lambda:self.shared)})
        p.start();self.addCleanup(p.stop)
        self.resolve=function('institute_coverage','for_account',{'enabled':self.enabled,'sponsor':self.sponsor})

    def test_selected_membership_not_old_billing_institute(self):
        self.resolve(self.account)
        self.sponsor.assert_called_once_with('selected-B','teacher')
        self.assertEqual(self.account.institute,'original-A')

    def test_foreign_account_not_given_current_users_coverage(self):
        self.account.user='another-teacher'
        self.assertIsNone(self.resolve(self.account))
        self.sponsor.assert_not_called()

    def test_non_teacher_membership_not_given_teacher_coverage(self):
        self.member.role='Student'
        self.assertIsNone(self.resolve(self.account))
        self.sponsor.assert_not_called()

    def test_revoked_membership_cannot_fall_back_to_original_institute(self):
        self.identity.side_effect=PermissionError('Revoked')
        with self.assertRaises(PermissionError):self.resolve(self.account)
        self.sponsor.assert_not_called()

    def test_single_institute_behavior_preserved(self):
        self.shared=False
        self.resolve(self.account)
        self.sponsor.assert_called_once_with('original-A','teacher')
        self.identity.assert_not_called()

    def test_disabled_coverage_stays_disabled(self):
        self.enabled.return_value=False
        self.assertIsNone(self.resolve(self.account))
        self.sponsor.assert_not_called()
        self.identity.assert_not_called()
