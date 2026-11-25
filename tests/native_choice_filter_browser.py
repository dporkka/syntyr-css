"""Browser smoke tests for native Syntyr choice cards, filter chips and rich rows.

Dev-only: python3 tests/native_choice_filter_browser.py
Requires Playwright browsers; consumers do not need a JavaScript runtime.
"""
import argparse
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/native-choice-filter-list.html").as_uri()


def run(engines):
    with sync_playwright() as p:
        for engine in engines:
            options = {}
            if engine == "webkit" and os.environ.get("SYNTYR_WEBKIT_EXECUTABLE"):
                options["executable_path"] = os.environ["SYNTYR_WEBKIT_EXECUTABLE"]
            browser = getattr(p, engine).launch(**options)
            try:
                for width in (320, 900):
                    page = browser.new_page(viewport={"width": width, "height": 850})
                    page.goto(URL)

                    starter = page.locator(".syn-choice-card").nth(0)
                    growth = page.locator(".syn-choice-card").nth(1)
                    assert starter.evaluate("(el) => getComputedStyle(el).display") == "grid"
                    initial_selected = starter.evaluate("(el) => getComputedStyle(el).backgroundColor")
                    initial_unselected = growth.evaluate("(el) => getComputedStyle(el).backgroundColor")
                    assert initial_selected != initial_unselected, (engine, width, "checked card styling")
                    growth.click()
                    assert page.locator('input[name="plan"][value="growth"]').is_checked()
                    assert not page.locator('input[name="plan"][value="starter"]').is_checked()
                    assert growth.evaluate("(el) => getComputedStyle(el).backgroundColor") == initial_selected

                    filter_label = page.locator(".syn-filter-choices > .syn-chip").nth(1)
                    filter_label.click()
                    assert page.locator('input[name="status"][value="active"]').is_checked()
                    assert filter_label.evaluate("(el) => getComputedStyle(el).borderTopColor") != page.locator(".syn-filter-choices > .syn-chip").first.evaluate("(el) => getComputedStyle(el).borderTopColor"), (engine, width, "filter selected border")
                    page.get_by_role("button", name="Apply filter").click()
                    assert "status=active" in page.url, (engine, width, page.url)

                    error_field = page.locator(".syn-field[data-syn-state='error']")
                    assert error_field.locator("input").get_attribute("aria-describedby") == "billing-help billing-error"
                    assert page.locator("#billing-error").is_visible()
                    row = page.locator(".syn-list-row").first
                    assert row.locator("a").count() == 2
                    assert row.locator(".syn-list-row__body").is_visible()
                    assert row.locator(".syn-list-row__actions").is_visible()

                    page.evaluate("document.body.dir = 'rtl'")
                    page.evaluate("document.documentElement.style.fontSize = '20px'")
                    overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                    assert overflow <= 2, (engine, width, "horizontal overflow", overflow)
                    page.evaluate("document.body.classList.remove('syn-root')")
                    assert starter.evaluate("(el) => getComputedStyle(el).display") != "grid", (engine, width, "scope leak")
                    page.close()
            finally:
                browser.close()
            print("PASS", engine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--browsers", nargs="+", choices=("chromium", "firefox", "webkit"),
                        default=("chromium", "firefox", "webkit"))
    run(parser.parse_args().browsers)
