import json
import unittest
from institute_lms.onboarding_navigation import teaching_path, profile_pending


class NavigationTests(unittest.TestCase):
    def row(self, **changes):
        data=dict(flow='public-account-v1',email='teacher@example.invalid',kind='Individual Teacher',teaching_path='institute')
        data.update(changes)
        return {'details':json.dumps(data)}

    def test_saved_choice_survives_new_browser(self):
        self.assertEqual(teaching_path([self.row()], 'teacher@example.invalid'),'institute')

    def test_wrong_account_and_unknown_paths_ignored(self):
        self.assertEqual(teaching_path([self.row()], 'other@example.invalid'),'')
        self.assertEqual(teaching_path([self.row(teaching_path='admin')], 'teacher@example.invalid'),'')

    def test_legacy_or_malformed_data_does_not_choose(self):
        for row in ({'details':'bad'}, {'details':'[]'}, self.row(flow='legacy')):
            self.assertEqual(teaching_path([row], 'teacher@example.invalid'),'')

    def test_new_profile_requires_saved_completion(self):
        row=self.row(onboarding_version=2)
        self.assertTrue(profile_pending([row]))
        self.assertFalse(profile_pending([self.row(onboarding_version=2,onboarding_profile_completed=True)]))

    def test_legacy_profiles_are_not_reset(self):
        self.assertFalse(profile_pending([self.row()]))
        self.assertFalse(profile_pending([{'details':'bad'}]))

    def test_reviewed_teacher_application_preserves_teaching_path(self):
        from institute_lms.registration_contract import registration_details
        for path in ('individual','institute'):
            details=registration_details(dict(kind='Individual Teacher',email='teacher@example.invalid',full_name='Test Teacher',teaching_path=path),None)
            self.assertEqual(teaching_path([{'details':json.dumps(details)}],details['email']),path)
        with self.assertRaises(ValueError):
            registration_details(dict(kind='Individual Teacher',email='teacher@example.invalid',full_name='Test Teacher',teaching_path='admin'),None)
