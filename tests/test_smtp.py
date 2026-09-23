"""Real local SMTP/TLS round trips; no mail goes to an external server."""
import socket
import ssl
import unittest
from email import policy
from email.parser import BytesParser
from unittest.mock import patch

import trustme
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult

from backend.smtp_delivery import DeliveryError, deliver


class Capture:
    def __init__(self):
        self.messages = []

    async def handle_DATA(self, server, session, envelope):
        self.messages.append(envelope)
        return '250 Accepted'


class SmtpTest(unittest.TestCase):
    def test_starttls_and_implicit_tls_with_auth(self):
        for mode in ('starttls', 'ssl'):
            with self.subTest(mode=mode):
                ca = trustme.CA()
                cert = ca.issue_cert('127.0.0.1')
                server_tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                cert.configure_cert(server_tls)
                client_tls = ssl.create_default_context()
                ca.configure_trust(client_tls)
                handler = Capture()
                with socket.socket() as probe:
                    probe.bind(('127.0.0.1', 0))
                    port = probe.getsockname()[1]
                def authenticate(server, session, envelope, mechanism, credentials):
                    return AuthResult(success=credentials.login == b'user' and credentials.password == b'pass', handled=False)
                options = {'tls_context': server_tls, 'require_starttls': True} if mode == 'starttls' else {'ssl_context': server_tls, 'auth_require_tls': False}
                controller = Controller(handler, hostname='127.0.0.1', port=port,
                                        authenticator=authenticate, auth_required=True, **options)
                controller.start()
                try:
                    cfg = {'origin': 'https://site.example.org', 'recipient': 'etrn@corp.aib.ru',
                           'smtp': {'host': '127.0.0.1', 'port': port, 'security': mode,
                                    'username': 'user', 'password': 'pass', 'from_email': 'etrn@corp.aib.ru'}}
                    data = {'contact_type': 'email', 'contact': 'customer@example.org', 'name': 'Тест',
                            'company': 'Компания', 'problem': 'Тест доставки заявки через защищённый канал.',
                            'page_url': cfg['origin'] + '/'}
                    with patch('backend.smtp_delivery.ssl.create_default_context', return_value=client_tls):
                        deliver(cfg, 'test-request-12345', data)
                    self.assertEqual(len(handler.messages), 1)
                    envelope = handler.messages[0]
                    self.assertEqual(envelope.rcpt_tos, ['etrn@corp.aib.ru'])
                    parsed = BytesParser(policy=policy.default).parsebytes(envelope.original_content)
                    self.assertEqual(parsed['Reply-To'], 'customer@example.org')
                    self.assertIn('Тест доставки', parsed.get_content())
                    cfg['smtp']['password'] = 'wrong-password'
                    with patch('backend.smtp_delivery.ssl.create_default_context', return_value=client_tls):
                        with self.assertRaisesRegex(DeliveryError, 'smtp_authentication_failed'):
                            deliver(cfg, 'test-request-12346', data)
                    self.assertEqual(len(handler.messages), 1)
                finally:
                    controller.stop()


if __name__ == '__main__':
    unittest.main()
