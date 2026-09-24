"""Template/installer contract checks. A licensed CMS integration is a separate acceptance step."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from build_bitrix import native_js

ROOT = Path(__file__).resolve().parents[1]
PHP = os.environ.get('PHP_BINARY') or shutil.which('php')
if PHP and not os.environ.get('PHP_BINARY'):
    version = subprocess.check_output([PHP, '-r', 'echo PHP_MAJOR_VERSION . "." . PHP_MINOR_VERSION;'], text=True)
    if version != '8.3':
        PHP = None


class BitrixPackageTest(unittest.TestCase):
    def test_no_core_or_custom_form_processor_in_distribution(self):
        site = ROOT / 'bitrix/site'
        self.assertFalse((site / 'bitrix').exists())
        self.assertFalse((site / 'local/components').exists())
        self.assertFalse(list(site.rglob('component.php')))
        self.assertFalse(list(site.rglob('result_modifier.php')))
        for path in site.rglob('*.php'):
            text = path.read_text(encoding='utf-8')
            for forbidden in ('CFormResult::Add', 'CEvent::Send', 'mail(', '/api/leads', 'formsubmit.co'):
                self.assertNotIn(forbidden, text, str(path))

    def test_native_ui_preserves_the_component_submission(self):
        js = native_js()
        self.assertIn('DOMContentLoaded', js)
        self.assertIn('[data-bitrix-form] form', js)
        self.assertNotIn('fetch(', js)
        self.assertNotIn('form.elements.problem', js)
        self.assertNotIn('submitButton.disabled = true', js)
        self.assertIn('web_form_submit', js)
        self.assertIn('installFaqAnimations()', js)
        self.assertIn('installMetrica()', js)

    def test_bitrix_robots_allows_resources_not_private_paths(self):
        robots = (ROOT / 'bitrix/site/robots.txt').read_text()
        self.assertIn('Disallow: /bitrix/', robots)
        self.assertIn('Disallow: /local/', robots)
        self.assertIn('Allow: /bitrix/cache/css/', robots)
        self.assertIn('Allow: /local/templates/aib_etrn/assets/', robots)
        self.assertNotIn('Allow: /bitrix/cache/\n', robots)
        self.assertNotIn('Allow: /bitrix/components/\n', robots)
        self.assertIn('Disallow: /\n', (ROOT / 'bitrix/robots.staging.txt').read_text())

    @unittest.skipUnless(PHP, 'PHP 8.3 checked in Linux CI')
    def test_php_templates_keep_native_fields_errors_captcha_and_success(self):
        for case in ('base', 'errors', 'captcha', 'success', 'denied'):
            result = subprocess.run([PHP, str(ROOT / 'tests/bitrix/fixture.php'), case], capture_output=True, text=True, encoding='utf-8', check=True)
            self.assertFalse(result.stderr)
            self.assertIn('data-fixture-panel', result.stdout)
            if case == 'success':
                self.assertIn('data-bitrix-success', result.stdout)
                self.assertNotIn('name="web_form_submit"', result.stdout)
            else:
                self.assertIn('name="sessid" value="fixture-session-token"', result.stdout)
                self.assertIn('name="web_form_submit"', result.stdout)
                self.assertIn('name="form_checkbox_CONSENT[]" value="105"', result.stdout)
                self.assertIn('name="form_hidden_106" value="unchanged"', result.stdout)
            if case == 'errors':
                self.assertIn('saved@example.org', result.stdout)
                self.assertIn('Сохранённое описание', result.stdout)
                self.assertNotIn('<script>unsafe()', result.stdout)
            if case == 'captcha':
                self.assertIn('name="captcha_sid" value="fixture-captcha"', result.stdout)
                self.assertIn('name="captcha_word"', result.stdout)

    @unittest.skipUnless(PHP, 'PHP 8.3 checked in Linux CI')
    def test_installer_backup_optional_metrica_and_core_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'www'
            for name in ('header.php', 'footer.php', 'modules/main/include/prolog_before.php', 'components/bitrix/form.result.new/component.php'):
                path = root / 'bitrix' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('CORE DO NOT CHANGE', encoding='utf-8')
            (root / 'index.php').write_text('ORIGINAL INDEX', encoding='utf-8')
            command = [PHP, str(ROOT / 'bitrix/install.php'), '--root=' + str(root), '--backup-dir=' + str(base)]
            result = subprocess.run(command, input='landing.example.org\n7\n\n\nstaging\n\nyes\n', text=True, encoding='utf-8', capture_output=True, check=True)
            self.assertIn('Файлы установлены', result.stdout)
            self.assertFalse(result.stderr)
            backups = list(base.glob('aib-etrn-backup-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / 'index.php').read_text(), 'ORIGINAL INDEX')
            manifest = json.loads((backups[0] / 'manifest.json').read_text())
            self.assertIn('index.php', manifest['replaced'])
            self.assertEqual((root / 'bitrix/components/bitrix/form.result.new/component.php').read_text(), 'CORE DO NOT CHANGE')
            self.assertIn('Disallow: /\n', (root / 'robots.txt').read_text())
            config = root / 'local/php_interface/aib_etrn.php'
            self.assertIn("'metrica_id' => ''", config.read_text())
            for answer, expected in [('12345678', '12345678'), ('', '12345678'), ('-', '')]:
                subprocess.run(command + ['--analytics-only'], input=answer + '\nyes\n', text=True, encoding='utf-8', capture_output=True, check=True)
                self.assertIn("'metrica_id' => '" + expected + "'", config.read_text())
            before = config.read_bytes()
            subprocess.run(command + ['--analytics-only'], input='87654321\nno\n', text=True, encoding='utf-8', capture_output=True, check=True)
            self.assertEqual(config.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
