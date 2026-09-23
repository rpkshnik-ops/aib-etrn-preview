"""Browser checks with a local mock of Metrica; no external analytics requests."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from src.render import render_page

ROOT = Path(__file__).resolve().parent
CHROME = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
ORIGIN = 'https://landing.example.org'


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(CHROME) if CHROME.exists() else None)
        for mode in ('preview', 'staging', 'production'):
            for counter in ('', '12345678'):
                requested = []
                html = render_page({'mode': mode, 'metrica_id': counter, 'site_url': ORIGIN,
                                    'privacy_url': ORIGIN + '/privacy.pdf',
                                    'consent_url': ORIGIN + '/consent.pdf',
                                    'offer_url': ORIGIN + '/offer.pdf', 'delivery_confirmed': True})
                def intercept(route):
                    url = route.request.url
                    requested.append(url)
                    if url == ORIGIN + '/':
                        route.fulfill(content_type='text/html; charset=utf-8', body=html)
                    elif url == ORIGIN + '/app.js?v=dev':
                        route.fulfill(content_type='application/javascript', path=ROOT / 'src/app.js')
                    elif url == 'https://mc.yandex.ru/metrika/tag.js':
                        route.fulfill(content_type='application/javascript', body='''
                            window.mockMetricaCalls = (window.ym.a || []).map(args => Array.from(args));
                            window.ym = (...args) => window.mockMetricaCalls.push(args);
                        ''')
                    else:
                        route.fulfill(status=204, body='')
                page = browser.new_page()
                page.route('**/*', intercept)
                page.goto(ORIGIN + '/', wait_until='load')
                enabled = mode == 'production' and bool(counter)
                assert page.evaluate('window.aibSite.analyticsEnabled') == enabled
                if enabled:
                    page.wait_for_function('window.mockMetricaCalls?.length > 0')
                    calls = page.evaluate('window.mockMetricaCalls')
                    assert calls[0][0:2] == [int(counter), 'init']
                    assert calls[0][2]['webvisor'] is False
                    assert requested.count('https://mc.yandex.ru/metrika/tag.js') == 1
                    page.evaluate('''window.aibSite.track('form_error', {
                        fields: 'phone', contact: 'private@example.org', problem: 'private-problem'
                    })''')
                    calls = page.evaluate('window.mockMetricaCalls')
                    assert calls[-1] == [int(counter), 'reachGoal', 'form_error', {'fields': 'phone'}]
                    assert 'private' not in json.dumps(calls)
                else:
                    assert not any('mc.yandex.' in url for url in requested)
                    assert page.evaluate('typeof window.ym') == 'undefined'
                print(f'OK Metrica: mode={mode}, configured={bool(counter)}, loaded={enabled}')
                page.close()
        browser.close()


if __name__ == '__main__':
    main()
