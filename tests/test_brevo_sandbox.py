import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
import contextlib
import io
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location('brevo_setup',Path(__file__).resolve().parents[1]/'scripts/configure-brevo-sandbox.py')
setup = importlib.util.module_from_spec(spec); spec.loader.exec_module(setup)


class BrevoSetup(unittest.TestCase):
    def test_sender_probe_never_sends_or_leaks_reply(self):
        client=MagicMock();client.has_extn.return_value=True
        client.mail.return_value=(550,b'Account not activated SECRET')
        output=io.StringIO()
        with patch.object(setup.smtplib,'SMTP') as smtp, contextlib.redirect_stdout(output):
            smtp.return_value.__enter__.return_value=client
            setup.sender_probe('private-placeholder')
        client.mail.assert_called_once_with(setup.SENDER)
        client.rcpt.assert_not_called();client.data.assert_not_called();client.sendmail.assert_not_called()
        client.rset.assert_called_once()
        self.assertIn('550',output.getvalue());self.assertNotIn('SECRET',output.getvalue())

    def test_reply_to_frappe17_plain_email_field(self):
        meta = SimpleNamespace(fields=[SimpleNamespace(fieldname=name,fieldtype='Data',options=None) for name in ('_name','email')])
        self.assertEqual(setup.reply_to_field(meta),'email')

    def test_reply_to_typed_email_and_unknown_schema(self):
        meta = SimpleNamespace(fields=[SimpleNamespace(fieldname='address',fieldtype='Data',options='Email')])
        self.assertEqual(setup.reply_to_field(meta),'address')
        meta.fields[0].options=None
        with self.assertRaises(ValueError): setup.reply_to_field(meta)

    def test_exactly_one_recipient(self):
        self.assertEqual(setup.recipient(' tester@example.org '),'tester@example.org')
        for value in ['a@example.org,b@example.org','a@example.org\r\nBcc:other@example.org','Display <a@example.org>','bad']:
            with self.assertRaises(ValueError): setup.recipient(value)

    def test_tls_before_auth_no_test_message_in_probe(self):
        client=MagicMock();client.has_extn.return_value=True
        with patch.object(setup.smtplib,'SMTP') as smtp:
            smtp.return_value.__enter__.return_value=client
            setup.probe('private-placeholder')
            smtp.assert_called_once_with('smtp-relay.brevo.com',587,timeout=30)
        names=[c[0] for c in client.method_calls]
        self.assertLess(names.index('starttls'),names.index('login'))
        client.sendmail.assert_not_called()
        context=client.starttls.call_args.kwargs['context']
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode,setup.ssl.CERT_REQUIRED)

    def test_no_tls_never_authenticates(self):
        client=MagicMock();client.has_extn.return_value=False
        with patch.object(setup.smtplib,'SMTP') as smtp:
            smtp.return_value.__enter__.return_value=client
            with self.assertRaises(ValueError):setup.probe('private-placeholder')
        client.login.assert_not_called()
