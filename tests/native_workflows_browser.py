"""Three-engine browser smoke for Syntyr's script-free native business workflows.

Maintainer-only Playwright; launch `python3 tests/native_workflows_browser.py` after
installing browser binaries. Do not add any JavaScript runtime to the shipped CSS.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = (Path(__file__).resolve().parents[1] / "examples/native-workflows.html").as_uri()


def run():
    with sync_playwright() as p:
        for engine in ("chromium", "firefox", "webkit"):
            browser = getattr(p, engine).launch()
            try:
                for width in (320, 900):
                    page = browser.new_page(viewport={"width": width, "height": 780})
                    page.goto(URL)
                    form_id = page.locator('button[value="save"]').evaluate("e => e.form.id")
                    assert form_id == "resource-editor", (engine, width, form_id)
                    assert page.locator('button[value="save-close"]').evaluate("e => e.form.id") == form_id
                    assert page.locator('button[value="save"]').is_disabled()
                    assert page.locator('input[type="file"]').evaluate("e => e.multiple")
                    assert page.locator('.syn-form-actions').evaluate("e => getComputedStyle(e).position") == 'sticky'
                    summary = page.locator('summary').filter(has_text='West region')
                    summary.focus()
                    summary.press('Enter')
                    assert page.locator('details').last.get_attribute('open') is not None
                    page.locator('a[href="#record-rs088"]').click()
                    assert page.url.endswith('#record-rs088')
                    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                    assert overflow <= 1, (engine, width, overflow)
                    page.close()
                page = browser.new_page(viewport={"width": 320, "height": 780})
                page.goto(URL)
                page.evaluate('document.documentElement.style.fontSize = "64px"')
                overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                assert overflow <= 1, (engine, '400% text', overflow)
                page.close()
                page = browser.new_page(viewport={"width": 320, "height": 780}, forced_colors="active")
                page.goto(URL)
                assert page.locator('.syn-upload-field').evaluate("e => getComputedStyle(e).borderStyle") != 'none'
                page.close()
                print("PASS", engine, "forms, disclosure, responsive text and forced colors")
            finally:
                browser.close()


if __name__ == "__main__":
    run()
