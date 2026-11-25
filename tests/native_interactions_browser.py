"""Optional cross-browser smoke test for script-free native interaction recipes.

Run with developer-installed Playwright:
    python3 tests/native_interactions_browser.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/native-interactions.html").as_uri()
GROUP = 'details[name="native-interaction-faq"]'


def check(browser_type, engine, width, forced_colors=False):
    browser = browser_type.launch(headless=True)
    try:
        context = browser.new_context(
            viewport={"width": width, "height": 540 if width == 360 else 800},
            java_script_enabled=False,
            reduced_motion="reduce",
            forced_colors="active" if forced_colors else "none",
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        assert page.locator("script").count() == 0
        group = page.locator(GROUP)
        assert group.count() == 3
        assert group.evaluate_all("els => els.filter(el => el.open).length") == 1
        group.nth(1).locator("summary").click()
        assert group.nth(1).get_attribute("open") is not None
        assert group.nth(0).get_attribute("open") is None
        group.nth(2).locator("summary").focus()
        page.keyboard.press("Enter")
        assert group.nth(2).get_attribute("open") is not None
        assert group.nth(1).get_attribute("open") is None

        # Invoker commands work without a framework or any inline script.
        page.get_by_role("button", name="Review a confirmation").click()
        dialog = page.locator("#native-interaction-confirm")
        assert dialog.is_visible(), (engine, "dialog did not open")
        assert dialog.evaluate("el => el.matches(':modal')")
        bounds = dialog.bounding_box()
        assert bounds is not None
        assert bounds["x"] >= -1 and bounds["x"] + bounds["width"] <= width + 1, bounds
        # Enlarged root text and short viewports must not push modal controls
        # outside the browser's bounded scrollable top layer.
        page.evaluate("document.documentElement.style.fontSize = '200%'")
        enlarged = dialog.bounding_box()
        assert enlarged["x"] >= -1 and enlarged["x"] + enlarged["width"] <= width + 1, enlarged
        assert enlarged["height"] <= page.viewport_size["height"] + 1, enlarged
        page.evaluate("document.documentElement.style.fontSize = ''")
        assert dialog.evaluate("el => getComputedStyle(el).overflowY") == "auto"
        dialog.get_by_role("button", name="Cancel").click()
        assert not dialog.is_visible(), (engine, "dialog did not close")
        page.get_by_role("button", name="Review a confirmation").click()
        page.keyboard.press("Escape")
        assert not dialog.is_visible(), (engine, "Escape did not close dialog")

        cities = page.locator("#native-interaction-city")
        assert cities.get_attribute("list") == "native-interaction-cities"
        cities.fill("Custom City")
        assert cities.input_value() == "Custom City"
        select = page.locator("#native-interaction-market")
        select.select_option("br")
        assert select.input_value() == "br"
        meter = page.locator("#native-interaction-capacity")
        assert meter.evaluate("el => el.value") == 68
        assert page.locator("#native-interaction-result").inner_text() == "42 available locations"

        # A static site can demonstrate native GET navigation without pretending
        # to return application-owned filtered results.
        query = page.locator("#native-interaction-query")
        query.fill("billboard & lighting")
        page.get_by_role("button", name="Search", exact=True).click()
        assert "q=billboard+%26+lighting" in page.url, page.url
        assert page.locator("main").is_visible()
        if forced_colors:
            assert page.evaluate("matchMedia('(forced-colors: active)').matches")
        print(f"PASS {engine} width={width} forced_colors={forced_colors}")
    finally:
        browser.close()


def check_vertical_overlays(browser_type, engine):
    # Physical size constraints must stay tied to physical viewport axes even
    # when the document uses a vertical writing mode. No application JS loads.
    browser = browser_type.launch(headless=True)
    try:
        page = browser.new_page(viewport={"width": 320, "height": 200}, java_script_enabled=False)
        page.goto(URL, wait_until="domcontentloaded")
        page.evaluate("""() => {
          const dialog = document.querySelector('#native-interaction-confirm');
          dialog.style.writingMode = 'vertical-rl';
          const content = document.createElement('p');
          content.textContent = 'A'.repeat(2000);
          content.style.overflowWrap = 'anywhere';
          dialog.append(content);
          dialog.showModal();
        }""")
        dialog = page.locator("#native-interaction-confirm")
        rect = dialog.bounding_box()
        assert rect is not None
        assert rect["height"] <= 200.01, (engine, "vertical writing mode escaped viewport", rect)
        assert rect["width"] <= 320.01, (engine, "horizontal clipping", rect)
        # A browser may apply its own modal top-layer clipping. Verify the
        # stylesheet itself imposes the physical height limit, not UA rescue.
        computed = dialog.evaluate("""el => ({
          height: getComputedStyle(el).maxHeight,
          width: getComputedStyle(el).maxWidth,
        })""")
        assert float(computed["height"].removesuffix("px")) <= 160.01, (
            engine, "Syntyr missing 80dvh physical height limit", computed
        )
        assert float(computed["width"].removesuffix("px")) <= 288.01, (
            engine, "Syntyr missing 100vw physical width limit", computed
        )
        assert dialog.evaluate("el => getComputedStyle(el).overflowY") == "auto"
        dialog.evaluate("el => el.close()")
        page.evaluate("""() => {
          const pop = document.createElement('div');
          pop.id = 'vertical-popover-smoke';
          pop.className = 'syn-popover syn-popover--anchored';
          pop.setAttribute('popover', 'manual');
          pop.style.writingMode = 'vertical-rl';
          pop.style.overflowWrap = 'anywhere';
          pop.textContent = 'A'.repeat(2000);
          document.body.append(pop);
          pop.showPopover();
        }""")
        pop = page.locator('#vertical-popover-smoke')
        pop_computed = pop.evaluate("""el => ({
          height: getComputedStyle(el).maxHeight,
          width: getComputedStyle(el).maxWidth,
        })""")
        assert float(pop_computed['height'].removesuffix('px')) <= 160.01, (
            engine, 'anchored popover lost physical height limit', pop_computed
        )
        assert float(pop_computed['width'].removesuffix('px')) <= 288.01, (
            engine, 'anchored popover lost physical width limit', pop_computed
        )
        print(f"PASS {engine} vertical writing overlays")
    finally:
        browser.close()


def check_short_corner_popover(browser_type, engine):
    # A fixed corner popover has both bottom inset and margin. Its max-height
    # must subtract those from the usable viewport even under 100px height.
    browser = browser_type.launch(headless=True)
    try:
        page = browser.new_page(viewport={"width": 320, "height": 100},
                                java_script_enabled=False)
        page.goto(URL, wait_until="domcontentloaded")
        page.evaluate("""() => {
          const pop = document.createElement('div');
          pop.id = 'short-corner-popover';
          pop.className = 'syn-popover';
          pop.setAttribute('popover', 'manual');
          pop.textContent = 'Long content '.repeat(250);
          document.body.append(pop);
          pop.showPopover();
        }""")
        pop = page.locator("#short-corner-popover")
        size = pop.bounding_box()
        computed = pop.evaluate("""el => ({
          maxHeight: getComputedStyle(el).maxHeight,
          overflow: getComputedStyle(el).overflowY
        })""")
        assert float(computed["maxHeight"].removesuffix("px")) <= 72.01, (
            engine, "corner popover height did not reserve inset and margin", computed
        )
        assert size["y"] >= -1, (engine, "corner popover clipped at top", size)
        assert computed["overflow"] == "auto", (engine, computed)
        print(f"PASS {engine} short corner popover")
    finally:
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        for engine in ("chromium", "firefox"):
            for width in (320, 360, 1280):
                check(getattr(playwright, engine), engine, width, forced_colors=False)
        check(playwright.chromium, "chromium", 360, forced_colors=True)
        for engine in ("chromium", "firefox"):
            check_vertical_overlays(getattr(playwright, engine), engine)
            check_short_corner_popover(getattr(playwright, engine), engine)
