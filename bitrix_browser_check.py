"""Render our PHP templates against a fixture; never connects to a real CMS/database/mailbox."""
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
PHP = os.environ.get('PHP_BINARY') or shutil.which('php')
CHROME = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')


def main():
    if not PHP:
        raise SystemExit('Set PHP_BINARY to PHP 8.3')
    with tempfile.TemporaryDirectory() as directory:
        webroot = Path(directory) / 'site'
        shutil.copytree(ROOT / 'bitrix/site', webroot)
        config = webroot / 'local/php_interface/aib_etrn.php'
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("<?php return ['form_id' => 7];", encoding='utf-8')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        url = f'http://127.0.0.1:{port}/'
        env = dict(os.environ, AIB_FIXTURE_ROOT=str(webroot))
        with tempfile.TemporaryFile() as log:
            server = subprocess.Popen([PHP, '-S', f'127.0.0.1:{port}', str(ROOT / 'tests/bitrix/fixture.php')], env=env, stdout=log, stderr=log)
            try:
                for attempt in range(40):
                    try:
                        urllib.request.urlopen(url, timeout=1).close()
                        break
                    except OSError:
                        if server.poll() is not None:
                            log.seek(0)
                            raise AssertionError(log.read().decode('utf-8', 'replace'))
                        time.sleep(.25)
                screenshots = ROOT / 'screenshots/bitrix'
                screenshots.mkdir(parents=True, exist_ok=True)
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(executable_path=str(CHROME) if CHROME.exists() else None)
                    for width in (1440, 768, 390, 320):
                        page = browser.new_page(viewport={'width': width, 'height': 950}, reduced_motion='reduce')
                        errors = []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        page.goto(url)
                        assert page.locator('h1').count() == 1
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        problem = page.locator('[name="form_textarea_104"]')
                        page.locator('.symptom-card').first.click()
                        assert problem.input_value().startswith('Симптом:')
                        assert page.locator('.symptom-card').first.get_attribute('aria-pressed') == 'true'
                        page.locator('[name="form_text_101"]').fill('customer@example.org')
                        page.locator('[name="form_text_102"]').fill('Тест')
                        page.locator('[name="form_checkbox_CONSENT[]"]').check()
                        for link in page.locator('.form-documents a.document-link').all():
                            assert link.get_attribute('target') == '_blank'
                            response = page.request.get(url.rstrip('/') + link.get_attribute('href'))
                            assert response.ok and response.body().startswith(b'%PDF-')
                        page.locator('#request').screenshot(path=str(screenshots / f'form-{width}.png'))
                        with page.expect_navigation() as navigation:
                            page.locator('[name="web_form_submit"]').click()
                        result = navigation.value.json()
                        assert result['fixture_only'] is True
                        assert result['post']['web_form_submit'] == 'Отправить заявку'
                        assert result['post']['sessid'] == 'fixture-session-token'
                        assert result['post']['WEB_FORM_ID'] == '7'
                        assert result['post']['form_checkbox_CONSENT'] == ['105']
                        assert result['post']['form_text_101'] == 'customer@example.org'
                        assert result['post']['form_hidden_106'] == 'unchanged'
                        assert 'request_id' not in result['post']
                        assert not errors, errors
                        page.close()
                        print(f'OK Bitrix template {width}px: native POST, session/fields, PDFs, symptom selection')
                    page = browser.new_page()
                    page.goto(url + '?case=errors')
                    assert page.locator('[data-bitrix-errors]').is_visible()
                    assert page.locator('[name="form_text_101"]').input_value() == 'saved@example.org'
                    page.goto(url + '?case=success')
                    assert page.locator('[data-bitrix-success]').is_visible()
                    assert page.locator('[name="web_form_submit"]').count() == 0
                    page.goto(url + '?case=captcha')
                    assert page.locator('[name="captcha_word"]').is_visible()
                    assert page.locator('[name="captcha_sid"]').input_value() == 'fixture-captcha'
                    page.goto(url + '?case=denied')
                    assert page.locator('[name="web_form_submit"]').is_disabled()
                    browser.close()
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == '__main__':
    main()
