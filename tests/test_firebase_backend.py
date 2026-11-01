import unittest
from institute_lms.firebase_backend import validate_metadata


class FirebaseMetadata(unittest.TestCase):
    def setUp(self):
        self.data = dict(type='service_account', project_id='sisu-lms',
            token_uri='https://oauth2.googleapis.com/token', private_key='placeholder-not-a-key',
            client_email='example@sisu-lms.iam.gserviceaccount.com', private_key_id='example')

    def test_expected_project(self):
        self.assertEqual(validate_metadata(self.data)['project_id'], 'sisu-lms')

    def test_wrong_project_rejected(self):
        self.data['project_id'] = 'other'
        with self.assertRaises(ValueError): validate_metadata(self.data)

    def test_browser_configuration_rejected(self):
        with self.assertRaises(ValueError): validate_metadata({'projectId': 'sisu-lms', 'apiKey': 'public'})

    def test_alternate_token_host_rejected(self):
        self.data['token_uri'] = 'https://example.org/token'
        with self.assertRaises(ValueError): validate_metadata(self.data)

    def test_missing_key_rejected(self):
        self.data.pop('private_key')
        with self.assertRaises(ValueError): validate_metadata(self.data)

    def test_no_secret_in_validation_error(self):
        self.data['project_id'] = 'sensitive-example'
        with self.assertRaises(ValueError) as error: validate_metadata(self.data)
        self.assertNotIn('sensitive-example', str(error.exception))
