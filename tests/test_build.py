import tempfile
import unittest
from pathlib import Path

from build import build
from src.deployment import settings
from src.render import render_page


class BuildTest(unittest.TestCase):
    def test_metrica_is_optional_and_only_enabled_in_production(self):
        for mode in ('preview', 'staging', 'production'):
            for counter in ('', '12345678'):
                with self.subTest(mode=mode, counter=counter):
                    page = render_page({'mode': mode, 'metrica_id': counter,
                                        'site_url': 'https://landing.example.org/',
                                        'privacy_url': 'https://landing.example.org/legal/privacy.pdf',
                                        'consent_url': 'https://landing.example.org/legal/consent.pdf',
                                        'offer_url': 'https://landing.example.org/assets/documents/offer.pdf',
                                        'delivery_confirmed': True})
                    expected = counter if mode == 'production' else ''
                    self.assertIn(f'data-analytics-counter="{expected}"', page)

    def test_production_requires_actual_settings(self):
        for value in ({'mode': 'production'}, {'mode': 'unknown'}, {'site_url': 'javascript:alert(1)'},
                      {'privacy_url': '//other.example/doc'}, {'metrica_id': 'garbage'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                settings(value)

    def test_modes_and_repeat_build(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            options = {
                'mode': 'production', 'site_url': 'https://landing.example.org',
                'privacy_url': 'https://landing.example.org/legal/privacy.pdf',
                'consent_url': 'https://landing.example.org/legal/consent.pdf',
                'offer_url': 'https://landing.example.org/legal/offer.pdf',
                'delivery_confirmed': True,
            }
            build(output, options)
            page = (output / 'index.html').read_text(encoding='utf-8')
            self.assertIn('data-form-endpoint="/api/leads"', page)
            self.assertIn('rel="canonical" href="https://landing.example.org/"', page)
            self.assertIn('index, follow', page)
            self.assertEqual(page.count('href="https://landing.example.org/legal/offer.pdf"'), 2)
            self.assertIn('https://landing.example.org/sitemap.xml', (output / 'robots.txt').read_text())
            for unwanted in ('Тестовый запуск', 'тестовый email', 'На согласовании', 'Проект документа', 'Предпросмотр', 'privacy-dialog'):
                self.assertNotIn(unwanted, page)
            build(output, options)
            self.assertEqual(page, (output / 'index.html').read_text(encoding='utf-8'))
            build(output, {'mode': 'staging'})
            self.assertNotIn('<url>', (output / 'sitemap.xml').read_text())
            self.assertIn('Disallow: /', (output / 'robots.txt').read_text())
            self.assertIn('noindex', (output / 'index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
