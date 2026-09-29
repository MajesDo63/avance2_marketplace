"""Provider calls are mocked: these tests never send email or contact AWS."""
import os
import secrets
import smtplib
import unittest
from unittest.mock import MagicMock, patch
import requests
from app.correo import enviar_real
from app.notificaciones import enviar_correo_confirmacion


class CorreoReal(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'MAIL_PROVIDER': 'ses', 'MAIL_FROM': 'sender@example.invalid',
                                          'AWS_REGION': 'us-east-1', 'S3_BUCKET': 'test-receipts'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_ses_sends_to_exact_customer_with_order_body(self):
        with patch('app.correo.boto3.client') as client:
            client.return_value.send_email.return_value = {'MessageId': 'provider-id'}
            self.assertEqual(enviar_real('customer@example.invalid', 987, 'Total: 75.00'), 'provider-id')
        payload = client.return_value.send_email.call_args.kwargs
        self.assertEqual(payload['Destination'], {'ToAddresses': ['customer@example.invalid']})
        self.assertIn('#987', payload['Message']['Subject']['Data'])
        self.assertEqual(payload['Message']['Body']['Text']['Data'], 'Total: 75.00')

    def test_ses_rejection_is_not_reported_as_sent(self):
        with patch('app.correo.boto3.client') as client:
            client.return_value.send_email.side_effect = RuntimeError('provider rejected')
            with self.assertRaises(RuntimeError):
                enviar_real('customer@example.invalid', 987, 'receipt')

    def test_missing_provider_never_falls_back_to_simulation(self):
        os.environ.pop('MAIL_PROVIDER')
        with self.assertRaises(RuntimeError):
            enviar_real('customer@example.invalid', 987, 'receipt')

    def test_header_injection_and_multiple_recipients_are_rejected(self):
        with patch('app.correo.boto3.client') as client:
            for address in ['a@example.invalid\r\nBcc: b@example.invalid', 'a@example.invalid,b@example.invalid']:
                with self.assertRaises(ValueError):
                    enviar_real(address, 987, 'receipt')
        client.assert_not_called()

    def smtp_env(self):
        os.environ.update(MAIL_PROVIDER='smtp', SMTP_HOST='smtp.example.invalid', SMTP_PORT='587',
                          SMTP_USER='test', SMTP_PASSWORD=secrets.token_urlsafe(24))

    def test_smtp_authentication_happens_after_tls(self):
        self.smtp_env()
        with patch('app.correo.smtplib.SMTP') as smtp:
            server = smtp.return_value.__enter__.return_value
            server.send_message.return_value = {}
            enviar_real('customer@example.invalid', 987, 'receipt')
        calls = [call[0] for call in server.method_calls]
        self.assertLess(calls.index('starttls'), calls.index('login'))
        self.assertLess(calls.index('login'), calls.index('send_message'))
        self.assertEqual(server.send_message.call_args.args[0]['To'], 'customer@example.invalid')

    def test_tls_failure_never_authenticates_or_sends(self):
        self.smtp_env()
        with patch('app.correo.smtplib.SMTP') as smtp:
            server = smtp.return_value.__enter__.return_value
            server.starttls.side_effect = smtplib.SMTPNotSupportedError('TLS unavailable')
            with self.assertRaises(smtplib.SMTPNotSupportedError):
                enviar_real('customer@example.invalid', 987, 'receipt')
        server.login.assert_not_called()
        server.send_message.assert_not_called()

    def test_receipt_is_saved_even_when_mail_fails(self):
        with patch('app.notificaciones.cliente_s3') as s3, patch('app.notificaciones.cursor_db') as db, \
                patch('app.notificaciones.enviar_real', side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                enviar_correo_confirmacion('customer@example.invalid', 987, 'item', '75.00')
        s3.return_value.put_object.assert_called_once()
        self.assertEqual(s3.return_value.put_object.call_args.kwargs['ServerSideEncryption'], 'AES256')
        db.return_value.__enter__.return_value.execute.assert_called_once()

    def test_internal_telemetry_failure_does_not_mark_accepted_mail_as_pending(self):
        with patch('app.notificaciones.cliente_s3'), patch('app.notificaciones.cursor_db'), \
                patch('app.notificaciones.enviar_real') as send, \
                patch('app.notificaciones.requests.post', side_effect=requests.ConnectionError):
            self.assertEqual(enviar_correo_confirmacion('customer@example.invalid', 987, 'item', '75.00'),
                             'comprobantes/pedido_987.txt')
        send.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
