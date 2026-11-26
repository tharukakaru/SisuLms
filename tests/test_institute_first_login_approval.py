from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock
from test_upload_provisioning import function


class FirstLoginApproval(TestCase):
    def setUp(self):
        def fail(message, kind=ValueError):
            raise kind(message)
        self.f = NS(session=NS(user='owner@example.invalid'), db=MagicMock(), throw=fail,
                    PermissionError=PermissionError)
        self.f.db.exists.return_value = True
        self.f.db.get_value.return_value = NS(phone='+94770000000', verified_at='2026-11-27')
        self.profile = NS(user=self.f.session.user, kind='Institute', status='Pending',
                          name='new-profile', workspace=None, reload=MagicMock())
        self.apply = MagicMock(return_value={'ok': True, 'status': 'Verified'})
        self.approve = function('provider_review', 'approve_new_institute', {'frappe': self.f, 'apply': self.apply})

    def test_email_and_phone_verified_uses_existing_review_service(self):
        self.approve(self.profile)
        self.apply.assert_called_once_with('new-profile', 'Verified',
            'Automatically approved after verified institute onboarding.', 'Automatic institute onboarding')
        filters = self.f.db.exists.call_args.args[1]
        self.assertEqual(filters['email_verified'], 1)
        self.assertEqual(filters['status'], 'Approved')

    def test_missing_verified_email_does_not_approve(self):
        self.f.db.exists.return_value = False
        with self.assertRaises(PermissionError):self.approve(self.profile)
        self.apply.assert_not_called()

    def test_missing_or_incomplete_phone_does_not_approve(self):
        for value in (None, NS(phone='', verified_at='today'), NS(phone='123', verified_at=None)):
            self.f.db.get_value.return_value = value
            with self.assertRaises(PermissionError):self.approve(self.profile)
        self.apply.assert_not_called()

    def test_teacher_rejected_and_existing_verified_profiles_not_promoted(self):
        for kind, status in [('Teacher', 'Pending'), ('Institute', 'Rejected'), ('Institute', 'Verified')]:
            self.profile.kind, self.profile.status = kind, status
            with self.assertRaises(PermissionError):self.approve(self.profile)
        self.apply.assert_not_called()

    def test_other_users_cannot_approve_profile(self):
        for user in ('Guest', 'different@example.invalid'):
            self.f.session.user = user
            with self.assertRaises(PermissionError):self.approve(self.profile)
        self.apply.assert_not_called()

    def test_failure_is_visible_and_not_success(self):
        self.apply.return_value = {'ok': False, 'message': 'Workspace conflict'}
        with self.assertRaises(ValueError):self.approve(self.profile)
        self.profile.reload.assert_not_called()
