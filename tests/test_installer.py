import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deploy.configure import collect_metrica, collect_smtp, configure_analytics, domain_name, write_private_json
from backend.smtp_delivery import validate_smtp


class InstallerTest(unittest.TestCase):
    def test_optional_metrica_skip_set_preserve_and_disable(self):
        for previous, answer, expected in (
                ('', '', ''), ('', '   ', ''), ('', '12345678', '12345678'),
                ('12345678', '', '12345678'), ('12345678', '-', ''),
                ('12345678', '87654321', '87654321')):
            with self.subTest(previous=previous, answer=answer), patch('builtins.input', return_value=answer):
                self.assertEqual(collect_metrica(previous), expected)

    def test_invalid_metrica_can_retry_or_skip(self):
        for invalid in ('abc', '<script>12345678</script>', 'https://metrika.yandex.ru/',
                        '1234', '1234567890123', '１２３４５６７８', '123 45678'):
            with self.subTest(invalid=invalid), patch('builtins.input', side_effect=[invalid, '']), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(collect_metrica(), '')
                self.assertIn('без HTML-кода', output.getvalue())

    def test_analytics_only_preserves_other_site_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'site.local.json'
            values = {'mode': 'staging', 'site_url': 'https://site.example.org/',
                      'privacy_url': '', 'consent_url': '',
                      'offer_url': 'https://site.example.org/assets/documents/offer.pdf',
                      'delivery_confirmed': False, 'metrica_id': ''}
            path.write_text(json.dumps(values), encoding='utf-8')
            with patch('builtins.input', return_value='12345678'), patch('deploy.configure.run') as commands, \
                    contextlib.redirect_stdout(io.StringIO()):
                configure_analytics(path)
            self.assertEqual(json.loads(path.read_text()), dict(values, metrica_id='12345678'))
            self.assertEqual(commands.call_count, 2)
            self.assertEqual(commands.call_args_list[0].args[1], 'build.py')
            self.assertEqual(commands.call_args_list[1].args[:2], ('bash', 'deploy/publish.sh'))

    def test_interactive_smtp_password_not_echoed(self):
        capture = io.StringIO()
        password = 'test-$-"-quote-\\-value'
        with patch('builtins.input', side_effect=['smtp.example.org', 'ssl', '465', 'etrn@corp.aib.ru', 'etrn@corp.aib.ru']), patch('getpass.getpass', return_value=password), contextlib.redirect_stdout(capture):
            smtp = collect_smtp()
        self.assertEqual(smtp['password'], password)
        self.assertNotIn(password, capture.getvalue())
        self.assertEqual(smtp['security'], 'ssl')

    def test_atomic_private_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            cfg = {'password': 'spaces " quotes $HOME `tick` \\ slash'}
            write_private_json(path, cfg)
            self.assertEqual(json.loads(path.read_text()), cfg)
            if os.name == 'posix':
                self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_invalid_configuration(self):
        for value in ('https://example.org/', 'example.org;rm', 'YOUR-DOMAIN.ru', 'example.org/path'):
            with self.assertRaises(ValueError):
                domain_name(value)
        good = {'host': 'smtp.example.org', 'port': 587, 'security': 'starttls',
                'username': 'user', 'password': 'secret', 'from_email': 'etrn@corp.aib.ru'}
        for overrides in ({'port': 0}, {'port': '587'}, {'security': 'none'},
                          {'from_email': 'a@b.ru\nBcc: evil@example.org'}, {'host': 'https://smtp.example.org'}):
            with self.assertRaises(ValueError):
                validate_smtp(dict(good, **overrides))


if __name__ == '__main__':
    unittest.main()
