from pathlib import Path
import os

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get('BASE_URL', "http://127.0.0.1:4173/")
PROJECT_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = PROJECT_DIR / "screenshots"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

CASES = (
    ("desktop", 1440, 1100),
    ("tablet", 768, 900),
    ("laptop", 1024, 900),
    ("mobile", 390, 844),
    ("narrow", 360, 800),
    ("small", 320, 800),
)


def run():
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    failures = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME) if CHROME.exists() else None,
            headless=True,
        )

        for layout, width, height in CASES:
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )
            accepted_requests = {"count": 0}

            def accept_form(route):
                accepted_requests["count"] += 1
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"success":"true","message":"accepted"}',
                )

            page.route("**/formsubmit.co/ajax/**", accept_form)
            page.route("**/api/leads", accept_form)
            console_errors = []
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.emulate_media(reduced_motion="reduce")
            page.goto(BASE_URL, wait_until="networkidle")
            page.evaluate(
                """() => {
                  window.__aibEvents = [];
                  window.addEventListener('aib:analytics', event => {
                    window.__aibEvents.push(event.detail);
                  });
                }"""
            )

            page.locator("h1").wait_for(state="visible")
            if page.locator("h1").count() != 1:
                failures.append(f"{layout}: expected one H1")

            dimensions = page.evaluate(
                """() => ({
                  viewport: document.documentElement.clientWidth,
                  scroll: document.documentElement.scrollWidth,
                  logoWidth: document.querySelector('.brand__mark img').naturalWidth
                })"""
            )
            if dimensions["scroll"] > dimensions["viewport"]:
                failures.append(
                    f"{layout}: horizontal overflow "
                    f"{dimensions['scroll']} > {dimensions['viewport']}"
                )
            if dimensions["logoWidth"] <= 0:
                failures.append(f"{layout}: logo did not load")

            if page.locator('a[href="tel:+79617770220"]').count() != 1:
                failures.append(f"{layout}: public phone link is missing")
            if page.locator('a[href="mailto:etrn@corp.aib.ru"]').count() != 1:
                failures.append(f"{layout}: public email link is missing")
            if page.locator('[data-floating-cta][href="#request"]').count() != 1:
                failures.append(f"{layout}: floating CTA is missing")
            if page.locator('script[src*="mc.yandex.ru"]').count() != 0:
                failures.append(f"{layout}: analytics loaded without a counter id")
            if page.locator('.button--primary .button__icon svg').count() < 2:
                failures.append(f"{layout}: CTA SVG icons are missing")
            if "↗" in page.locator("body").inner_text():
                failures.append(f"{layout}: emoji-style CTA arrow is still present")
            flow_node_color = page.locator(".flow-node").first.evaluate(
                "node => getComputedStyle(node).color"
            )
            if flow_node_color != "rgb(23, 25, 20)":
                failures.append(f"{layout}: flow node text contrast is incorrect")
            symptom_backgrounds = page.locator(".symptom-card").evaluate_all(
                "cards => [...new Set(cards.map(card => getComputedStyle(card).backgroundColor))]"
            )
            if len(symptom_backgrounds) != 1:
                failures.append(f"{layout}: symptom cards have inconsistent default colors")

            price_text = page.locator(".price-panel").inner_text()
            for expected in ("130 000", "100% предоплата", "НДС — 5%"):
                if expected not in price_text:
                    failures.append(f"{layout}: missing price condition: {expected}")

            if "Удалённо" not in page.locator(".promise-strip").inner_text():
                failures.append(f"{layout}: remote-work advantage is missing")

            missing_anchors = page.evaluate(
                """() => [...document.querySelectorAll('a[href^="#"]')]
                  .map(a => a.getAttribute('href'))
                  .filter(href => href !== '#' && !document.querySelector(href))"""
            )
            if missing_anchors:
                failures.append(f"{layout}: broken anchors: {missing_anchors}")

            too_small = page.evaluate(
                """() => [...document.querySelectorAll(
                  '.header-cta, .button, .symptom-card, .contact-choice label, .faq-item summary'
                )].filter(el => {
                  const rect = el.getBoundingClientRect();
                  if (rect.width === 0 || rect.height === 0) return false;
                  return rect.width < 44 || rect.height < 44;
                }).map(el => `${el.tagName}.${el.className}:${Math.round(el.getBoundingClientRect().width)}x${Math.round(el.getBoundingClientRect().height)}`)"""
            )
            if too_small:
                failures.append(f"{layout}: small targets: {too_small}")

            submit = page.locator(".form-submit")
            submit.click()
            if page.locator('[aria-invalid="true"]').count() < 3:
                failures.append(f"{layout}: required-field errors were not shown")

            page.locator(".symptom-card").first.click()
            if page.locator(".symptom-card").first.get_attribute("aria-pressed") != "true":
                failures.append(f"{layout}: symptom selection failed")
            if len(page.locator("#problem").input_value()) < 20:
                failures.append(f"{layout}: symptom did not prefill the problem")
            if "Добавлено" not in page.locator(".symptom-card").first.text_content():
                failures.append(f"{layout}: selected symptom has no visible feedback")
            page.wait_for_timeout(220)
            selected_background = page.locator(".symptom-card").first.evaluate(
                "card => getComputedStyle(card).backgroundColor"
            )
            if selected_background == symptom_backgrounds[0]:
                failures.append(
                    f"{layout}: selected symptom is not visually distinct "
                    f"({selected_background} vs {symptom_backgrounds[0]})"
                )
            if not page.locator("[data-selection-toast]").is_visible():
                failures.append(f"{layout}: symptom confirmation toast is missing")
            if page.locator('[data-selection-toast] a[href="#request"]').count() != 1:
                failures.append(f"{layout}: symptom toast has no form link")
            if layout == "mobile":
                page.screenshot(
                    path=str(SCREENSHOT_DIR / "final-mobile-symptom.png"),
                    full_page=False,
                )
            page.locator("[data-selection-toast-close]").click()

            page.locator(".symptom-card").first.click()
            if page.locator(".symptom-card").first.get_attribute("aria-pressed") != "false":
                failures.append(f"{layout}: symptom deselection failed")
            if page.locator("#problem").input_value():
                failures.append(f"{layout}: symptom draft was not cleared on deselection")
            page.locator(".symptom-card").first.click()

            problem_value = page.locator("#problem").input_value()
            page.locator("#phone").fill("+7 900 123-45-67")
            page.locator("#consent").check()
            submit.click()
            page.locator(".form-status--success").wait_for()
            status = page.locator("[data-form-status]").inner_text()
            if "Заявка принята" not in status:
                failures.append(f"{layout}: confirmed success state is missing")
            if accepted_requests["count"] != 1:
                failures.append(f"{layout}: expected one accepted request")

            accepted_events = page.evaluate(
                """() => window.__aibEvents.filter(event => event.name === 'lead_accepted').length"""
            )
            if accepted_events != 1:
                failures.append(f"{layout}: lead_accepted was not emitted once")

            page.locator("#phone").fill("+7 900 123-45-67")
            page.locator("#problem").fill(problem_value)
            page.locator("#consent").check()
            submit.click()
            duplicate_status = page.locator("[data-form-status]").inner_text()
            if "уже принята" not in duplicate_status:
                failures.append(f"{layout}: duplicate submission was not blocked")
            if accepted_requests["count"] != 1:
                failures.append(f"{layout}: duplicate created another request")

            page.locator("#problem").fill(problem_value + " Дополнительная деталь.")
            submit.click()
            rate_status = page.locator("[data-form-status]").inner_text()
            if "через" not in rate_status:
                failures.append(f"{layout}: local rate limit was not applied")

            privacy_button = page.locator('[data-open-dialog="privacy-dialog"]')
            if privacy_button.count():
                privacy_button.last.click()
                if not page.locator("#privacy-dialog").evaluate("dialog => dialog.open"):
                    failures.append(f"{layout}: privacy dialog did not open")
                page.locator("#privacy-dialog .dialog-close").click()

            faq_item = page.locator(".faq-item").first
            faq_item.locator("summary").click()
            if not faq_item.evaluate("item => item.open"):
                failures.append(f"{layout}: FAQ did not open")
            if "is-expanded" not in (faq_item.get_attribute("class") or ""):
                failures.append(f"{layout}: FAQ expanded state is missing")
            if faq_item.locator(".faq-item__content").get_attribute("aria-hidden") != "false":
                failures.append(f"{layout}: FAQ content accessibility state is incorrect")
            faq_item.locator("summary").click()
            if faq_item.evaluate("item => item.open"):
                failures.append(f"{layout}: FAQ did not close with reduced motion")

            if layout == "desktop":
                page.evaluate("sessionStorage.clear()")
                page.unroute("**/formsubmit.co/ajax/**", accept_form)
                page.unroute("**/api/leads", accept_form)
                page.route("**/api/leads", lambda route: route.fulfill(status=503, content_type="application/json", body='{"success":false}'))
                page.route(
                    "**/formsubmit.co/ajax/**",
                    lambda route: route.fulfill(
                        status=503,
                        content_type="application/json",
                        body='{"success":"false","message":"temporary failure"}',
                    ),
                )
                page.locator("#problem").fill(problem_value + " Проверка ошибки сети.")
                submit.click()
                page.locator(".form-status--error").wait_for()
                error_status = page.locator("[data-form-status]").inner_text()
                if "Не удалось подтвердить" not in error_status:
                    failures.append(f"{layout}: network error state is missing")
                if not page.locator("#problem").input_value():
                    failures.append(f"{layout}: form data was lost after network error")
                console_errors[:] = [
                    message for message in console_errors if "503" not in message
                ]

            if console_errors:
                failures.append(f"{layout}: console errors: {console_errors}")

            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(800)
            page.screenshot(
                path=str(SCREENSHOT_DIR / f"final-{layout}.png"),
                full_page=False,
            )
            page.screenshot(
                path=str(SCREENSHOT_DIR / f"final-{layout}-full.png"),
                full_page=True,
            )
            if layout in {"mobile", "small"}:
                page.evaluate("window.scrollTo(0, 420)")
                page.wait_for_timeout(250)
                sticky_state = page.evaluate(
                    """() => {
                      const header = document.querySelector('.site-header--final');
                      return {
                        position: getComputedStyle(header).position,
                        top: Math.round(header.getBoundingClientRect().top),
                        bottom: Math.round(header.getBoundingClientRect().bottom)
                      };
                    }"""
                )
                if sticky_state["position"] != "relative":
                    failures.append(f"{layout}: mobile header is still sticky")
                if sticky_state["bottom"] > 0:
                    failures.append(f"{layout}: mobile header did not scroll out of view")
                if "is-visible" not in (page.locator("[data-floating-cta]").get_attribute("class") or ""):
                    failures.append(f"{layout}: floating CTA did not appear after header left")
                if page.locator("[data-floating-cta]").get_attribute("aria-hidden") != "false":
                    failures.append(f"{layout}: floating CTA has incorrect accessibility state")
                page.screenshot(
                    path=str(SCREENSHOT_DIR / f"final-{layout}-scrolled.png"),
                    full_page=False,
                )
                page.evaluate("window.scrollTo(0, 0)")
            if layout in {"desktop", "mobile"}:
                page.evaluate(
                    """() => {
                      document.activeElement?.blur();
                      document.querySelector('.site-header').style.display = 'none';
                      document.querySelector('.skip-link').style.display = 'none';
                    }"""
                )
                page.locator("#price").screenshot(
                    path=str(SCREENSHOT_DIR / f"final-{layout}-price.png")
                )
                page.locator("#request").screenshot(
                    path=str(SCREENSHOT_DIR / f"final-{layout}-form.png")
                )
            print(
                f"OK {layout}: viewport={dimensions['viewport']}, "
                f"scrollWidth={dimensions['scroll']}, logoWidth={dimensions['logoWidth']}"
            )
            page.close()

        motion_page = browser.new_page(viewport={"width": 1440, "height": 900})
        motion_page.goto(BASE_URL, wait_until="networkidle")
        motion_page.locator(".flow-visual").screenshot(
            path=str(SCREENSHOT_DIR / "final-motion-flow.png")
        )
        motion_page.locator("#scope").scroll_into_view_if_needed()
        motion_page.wait_for_timeout(850)
        if "motion-ready" not in (motion_page.locator("html").get_attribute("class") or ""):
            failures.append("motion: enhancement class is missing")
        if not motion_page.locator("#scope .scope-card").first.evaluate(
            "element => element.classList.contains('is-visible')"
        ):
            failures.append("motion: revealed card did not become visible")
        signal_animation = motion_page.locator(".flow-visual__signal").first.evaluate(
            "element => getComputedStyle(element).animationName"
        )
        if signal_animation != "signal-pulse":
            failures.append("motion: flow signal animation is missing")
        eyebrow_animation = motion_page.locator(".eyebrow span").evaluate(
            "element => getComputedStyle(element).animationName"
        )
        if eyebrow_animation != "signal-pulse":
            failures.append("motion: hero eyebrow pulse is missing")
        route_animation = motion_page.locator(".flow-visual__pulse ellipse").evaluate(
            "element => getComputedStyle(element).animationName"
        )
        if route_animation != "route-travel":
            failures.append("motion: route impulse animation is missing")

        motion_faq = motion_page.locator(".faq-item").first
        motion_faq.scroll_into_view_if_needed()
        motion_faq.locator("summary").click()
        motion_page.wait_for_timeout(380)
        if "is-expanded" not in (motion_faq.get_attribute("class") or ""):
            failures.append("motion: FAQ expanded class is missing")
        icon_transform = motion_faq.locator("summary span").evaluate(
            "element => getComputedStyle(element).transform"
        )
        if icon_transform == "none":
            failures.append("motion: FAQ icon did not rotate")
        motion_page.locator(".faq-list").screenshot(
            path=str(SCREENSHOT_DIR / "final-motion-faq.png")
        )
        motion_faq.locator("summary").click()
        motion_page.wait_for_timeout(380)
        if motion_faq.evaluate("item => item.open"):
            failures.append("motion: FAQ close animation did not finish")

        hover_scope = motion_page.locator(".scope-card").nth(1)
        hover_scope.scroll_into_view_if_needed()
        motion_page.wait_for_timeout(700)
        scope_top_before = hover_scope.bounding_box()["y"]
        hover_scope.hover()
        motion_page.wait_for_timeout(260)
        scope_top_after = hover_scope.bounding_box()["y"]
        if scope_top_after >= scope_top_before - 4:
            failures.append("hover: service card did not lift")

        hover_step = motion_page.locator(".process-list li").first
        hover_step.scroll_into_view_if_needed()
        motion_page.mouse.move(0, 0)
        motion_page.wait_for_timeout(700)
        step_background_before = hover_step.evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        hover_step.hover()
        motion_page.wait_for_timeout(240)
        step_background_after = hover_step.evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        step_number_transform = hover_step.locator(":scope > span").evaluate(
            "element => getComputedStyle(element).transform"
        )
        if step_background_after == step_background_before:
            failures.append("hover: process step background did not change")
        if step_number_transform == "none":
            failures.append("hover: process step number did not scale")

        hover_node = motion_page.locator(".flow-node").first
        hover_node.scroll_into_view_if_needed()
        hover_node.hover()
        motion_page.wait_for_timeout(220)
        fast_route_duration = motion_page.locator(".flow-visual__pulse ellipse").evaluate(
            "element => getComputedStyle(element).animationDuration"
        )
        node_transform = hover_node.evaluate(
            "element => getComputedStyle(element).transform"
        )
        if fast_route_duration != "1.45s":
            failures.append("hover: route impulse did not accelerate")
        if node_transform == "none":
            failures.append("hover: flow node did not enlarge")
        motion_page.locator(".flow-visual").screenshot(
            path=str(SCREENSHOT_DIR / "final-hover-flow.png")
        )
        motion_page.close()

        browser.close()

    if failures:
        raise SystemExit("\n".join(failures))

    print("Browser checks passed: final dark concept at 1440, 768, 390 and 320 px.")


if __name__ == "__main__":
    run()
