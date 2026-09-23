from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = "https://rpkshnik-ops.github.io/aib-etrn-preview/"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def run():
    failures = []
    cases = ((1440, 1100), (390, 844), (320, 800))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME) if CHROME.exists() else None,
            headless=True,
        )

        for width, height in cases:
            page = browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on(
                "console",
                lambda message: errors.append(message.text)
                if message.type == "error"
                else None,
            )
            response = page.goto(
                BASE_URL,
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            page.locator("h1").wait_for(state="visible", timeout=20_000)
            page.locator(".brand__mark img").first.wait_for(state="visible")
            page.wait_for_timeout(1_000)

            state = page.evaluate(
                """() => ({
                  viewport: document.documentElement.clientWidth,
                  scroll: document.documentElement.scrollWidth,
                  logoWidth: document.querySelector('.brand__mark img').naturalWidth,
                  h1Count: document.querySelectorAll('h1').length,
                  preview: document.body.dataset.preview,
                  formMode: document.body.dataset.formMode,
                  formEndpoint: document.body.dataset.formEndpoint
                })"""
            )
            if not response or response.status != 200:
                failures.append(f"{width}: page status is not 200")
            if state["scroll"] > state["viewport"]:
                failures.append(f"{width}: horizontal overflow")
            if state["logoWidth"] <= 0:
                failures.append(f"{width}: logo did not load")
            if state["h1Count"] != 1:
                failures.append(f"{width}: expected one H1")
            if state["preview"] != "true":
                failures.append(f"{width}: preview mode marker is missing")
            if state["formMode"] != "testing":
                failures.append(f"{width}: form testing mode marker is missing")
            if state["formEndpoint"] != "https://formsubmit.co/ajax/etrn@corp.aib.ru":
                failures.append(f"{width}: form endpoint is missing")
            if page.locator('a[href="tel:+79617770220"]').count() != 1:
                failures.append(f"{width}: phone link is missing")
            if page.locator('a[href="mailto:etrn@corp.aib.ru"]').count() != 1:
                failures.append(f"{width}: email link is missing")
            if "НДС — 5%" not in page.locator(".price-panel").inner_text():
                failures.append(f"{width}: tax condition is missing")
            if "Удалённо" not in page.locator(".promise-strip").inner_text():
                failures.append(f"{width}: remote-work advantage is missing")
            if width == 390:
                page.locator(".symptom-card").first.click()
                if page.locator(".symptom-card").first.get_attribute("aria-pressed") != "true":
                    failures.append(f"{width}: symptom selection failed")
                if not page.locator("[data-selection-toast]").is_visible():
                    failures.append(f"{width}: symptom feedback toast is missing")
                header_position = page.locator(".site-header--final").evaluate(
                    "element => getComputedStyle(element).position"
                )
                if header_position != "relative":
                    failures.append(f"{width}: mobile header is still sticky")
            if errors:
                failures.append(f"{width}: console errors: {errors}")

            print(
                f"OK {width}: status={response.status}, "
                f"scrollWidth={state['scroll']}, logoWidth={state['logoWidth']}"
            )
            page.close()

        browser.close()

    if failures:
        raise SystemExit("\n".join(failures))

    print("Public GitHub Pages check passed for the final dark preview.")


if __name__ == "__main__":
    run()
