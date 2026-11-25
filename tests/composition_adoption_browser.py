"""Optional real-browser regression: intrinsic composition wraps on parent width.

Install Playwright only for testing: python -m pip install playwright
Then provision the browser and run: python tests/composition_adoption_browser.py
No Playwright dependency ships in @syntyr/css.
"""
from pathlib import Path
from playwright.sync_api import Error as PlaywrightError, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/composition-adoption.html").as_uri()


def check(browser_type):
    browser = browser_type.launch(headless=True)
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL)
        assert page.locator("script").count() == 0, "example must not load JS"
        assert page.locator(".syn-sidecar").evaluate(
            "(el) => getComputedStyle(el).display") == "flex"
        main = page.locator(".syn-sidecar > :first-child")
        aside = page.locator(".syn-sidecar > :last-child")
        wide_main, wide_aside = main.bounding_box(), aside.bounding_box()
        assert abs(wide_main["y"] - wide_aside["y"]) < 2, (wide_main, wide_aside)
        assert wide_main["x"] + wide_main["width"] <= wide_aside["x"] + 2
        assert page.locator(".syn-inline[style]").evaluate(
            "(el) => getComputedStyle(el).gap") == "8px"

        page.set_viewport_size({"width": 375, "height": 800})
        narrow_main, narrow_aside = main.bounding_box(), aside.bounding_box()
        assert narrow_aside["y"] >= narrow_main["y"] + narrow_main["height"] - 2, (
            narrow_main, narrow_aside
        )
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        ), "horizontal overflow on mobile"
        # A narrower embedding is independent of viewport width.
        page.set_viewport_size({"width": 1280, "height": 800})
        page.locator(".syn-sidecar").evaluate(
            "(el) => { el.style.width='345px'; el.style.maxWidth='100%'; }"
        )
        compact_main, compact_aside = main.bounding_box(), aside.bounding_box()
        assert compact_aside["y"] >= compact_main["y"] + compact_main["height"] - 2, (
            compact_main, compact_aside
        )
        # A sidecar with no aside must still constrain an unbroken identifier.
        page.evaluate("""() => {
            const sidecar = document.createElement('div');
            sidecar.className = 'syn-sidecar';
            sidecar.id = 'sidecar-single';
            sidecar.style.width = '345px';
            const content = document.createElement('div');
            content.textContent = 'identifier'.repeat(100);
            sidecar.append(content);
            document.querySelector('main').append(sidecar);
        }""")
        assert page.locator("#sidecar-single").evaluate(
            "(el) => el.scrollWidth <= el.clientWidth + 1"
        ), "main-only sidecar overflows with long unbroken content"
        print(f"PASS {browser_type.name}: wide, mobile, embedded width, no JS")
    finally:
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        check(playwright.chromium)
        check(playwright.firefox)
        try:
            check(playwright.webkit)
        except PlaywrightError as error:
            # This device lacks the WPE system library, not a CSS fallback.
            if "libevent-2.1.so.7" not in str(error):
                raise
            print("SKIP webkit: host missing libevent-2.1.so.7")
