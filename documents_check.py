"""Read-only browser check for document links; never submits a real lead."""
import os
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:4173/')
CHROME = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')


def main():
    (ROOT / 'screenshots').mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(CHROME) if CHROME.exists() else None)
        for width in (1440, 768, 390, 320):
            page = browser.new_page(viewport={'width': width, 'height': 950}, reduced_motion='reduce')
            page.goto(BASE_URL, wait_until='domcontentloaded', timeout=60000)
            page.locator('h1').wait_for(state='visible')
            page.locator('#problem').fill('Проверка сохранения введённого описания при чтении документов.')
            page.locator('#phone').fill('+7 900 000-00-00')
            links = page.locator('.form-documents .document-link')
            assert links.count() == 2
            for link in links.all():
                assert link.get_attribute('target') == '_blank'
                assert link.evaluate('e => e.getBoundingClientRect().height') >= 44
                response = page.request.get(urljoin(BASE_URL, link.get_attribute('href')))
                assert response.status == 200
                assert 'application/pdf' in response.headers.get('content-type', '')
                assert response.body().startswith(b'%PDF-')
            page.locator('.form-documents').scroll_into_view_if_needed()
            page.locator('.lead-form').screenshot(path=str(ROOT / 'screenshots' / f'documents-form-{width}.png'))
            before = page.locator('#problem').input_value()
            if width in (1440, 390):
                for link in links.all():
                    expected_url = urljoin(BASE_URL, link.get_attribute('href'))
                    with page.context.expect_event('response', predicate=lambda response: response.url == expected_url) as response_event:
                        with page.expect_popup() as event:
                            link.click()
                    popup = event.value
                    assert response_event.value.status == 200
                    popup.close()
                    assert page.locator('#problem').input_value() == before
                    assert page.locator('#phone').input_value() == '+7 900 000-00-00'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert page.locator('.footer-docs a[href*=".pdf"]').count() == 2
            print(f'OK {width}: 2 accessible PDFs, new tabs, form values preserved, no overflow')
            page.close()
        browser.close()


if __name__ == '__main__':
    main()
