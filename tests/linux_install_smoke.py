"""CI-only real Linux provisioning test; prompts mocked, no external mail sent.

Run only on a disposable Ubuntu runner, after preparing /opt/aib-etrn/repo.
Never invoke on the owner's server.
"""
import json
import os
import stat
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deploy import configure


def main():
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'Disposable GitHub CI only'
    assert not configure.CONFIG_PATH.exists(), 'Refuse to overwrite existing settings'
    answers = ['landing.example.org', 'smtp.example.org', 'starttls', '587',
               'etrn@corp.aib.ru', 'etrn@corp.aib.ru', 'no', '', '', '', 'no']
    with patch.object(sys, 'argv', ['configure.py']), patch.object(sys.stdin, 'isatty', return_value=True), \
            patch('builtins.input', side_effect=answers), patch('getpass.getpass', return_value='ci-fake-password'):
        assert configure.main() == 0
    cfg = json.loads(configure.CONFIG_PATH.read_text())
    assert cfg['smtp']['password'] == 'ci-fake-password'
    assert stat.S_IMODE(configure.CONFIG_PATH.stat().st_mode) == 0o640
    assert configure.CONFIG_PATH.stat().st_uid == 0
    # Blank input retains previous values and the hidden password.
    with patch.object(sys, 'argv', ['configure.py', '--smtp-only']), \
            patch.object(sys.stdin, 'isatty', return_value=True), \
            patch('builtins.input', side_effect=['', '', '', '', '', 'no']), \
            patch('getpass.getpass', return_value=''):
        assert configure.main() == 0
    assert json.loads(configure.CONFIG_PATH.read_text()) == cfg
    site_path = configure.ROOT / 'site.local.json'
    initial_site = json.loads(site_path.read_text())
    assert initial_site['metrica_id'] == ''
    for answer, expected in [('12345678', '12345678'), ('', '12345678'), ('-', '')]:
        with patch.object(sys, 'argv', ['configure.py', '--analytics-only']), \
                patch.object(sys.stdin, 'isatty', return_value=True), \
                patch('builtins.input', return_value=answer), \
                patch('getpass.getpass', side_effect=AssertionError('Analytics must not ask for SMTP credentials')):
            assert configure.main() == 0
        assert json.loads(site_path.read_text()) == dict(initial_site, metrica_id=expected)
        assert json.loads(configure.CONFIG_PATH.read_text()) == cfg
        page = Path('/srv/aib-etrn/current/index.html').read_text()
        assert 'data-analytics-counter=""' in page, 'Staging must not send analytics'
    for attempt in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8081/healthz') as response:
                assert json.load(response)['status'] == 'ok'
            break
        except OSError:
            time.sleep(1)
    else:
        raise AssertionError('Installed API/worker did not become healthy')
    for path, expected in [('/', b'/api/leads'), ('/assets/documents/offer.pdf', b'%PDF-'),
                           ('/assets/documents/confidentiality.pdf', b'%PDF-')]:
        req = urllib.request.Request('http://127.0.0.1' + path, headers={'Host': 'landing.example.org'})
        with urllib.request.urlopen(req) as response:
            assert expected in response.read()
    subprocess.run(['bash', 'deploy/update.sh'], cwd=configure.ROOT, check=True)
    subprocess.run(['bash', 'deploy/manage.sh', 'status'], cwd=configure.ROOT, check=True)
    print('Linux install, SMTP reconfiguration, Nginx/PDFs, services and update: OK')


if __name__ == '__main__':
    main()
