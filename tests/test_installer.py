import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deploy.configure import collect_smtp, domain_name, write_private_json
from backend.smtp_delivery import validate_smtp


class InstallerTest(unittest.TestCase):
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
