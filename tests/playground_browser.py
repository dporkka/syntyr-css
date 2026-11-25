"""Optional real-browser exercise for the docs-only component playground.

Run: /path/to/playwright/python tests/playground_browser.py
"""
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def verify(browser, viewport):
    context = browser.new_context(viewport={"width": viewport, "height": 850})
    page = context.new_page()
    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))
    page.goto((ROOT / "docs/playground.html").as_uri(), wait_until="load")
    frame = page.frame_locator("#playground-preview")
    frame.locator(".syn-stat").first.wait_for()
    assert frame.locator(".syn-stat").count() == 3
    accent = frame.locator("body").evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()")
    assert accent == "#2458c6", ("initial studio stylesheet did not load", accent)
    page.locator("#playground-theme").select_option("grid")
    frame.locator("body[data-syn-theme='grid']").wait_for()
    accent = frame.locator("body").evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()")
    assert accent == "#76e7f7", ("grid theme CSS did not load", accent)
    page.locator("#playground-example").select_option("actions")
    frame.locator(".syn-panel").wait_for()
    panel_radius = frame.locator(".syn-panel").evaluate("e => getComputedStyle(e).borderTopLeftRadius")
    assert panel_radius == "12px", ("panel radius token not applied", panel_radius)
    editor = page.locator('#playground-editor-mount .cm-content[contenteditable="true"]')
    editor.wait_for()
    editor.click()
    page.keyboard.press('ControlOrMeta+A')
    page.keyboard.insert_text('<div id="safe">Edited HTML</div><script>parent.document.body.dataset.injected="yes"</script>')
    frame.locator("#safe").wait_for()
    assert page.locator("body").get_attribute("data-injected") is None, "sandbox permitted parent script injection"
    assert page.locator("body").evaluate("e => e.scrollWidth <= window.innerWidth + 1"), "playground overflows"
    assert not page_errors, page_errors
    context.close()


def main():
    with sync_playwright() as playwright:
        browser_name = sys.argv[1] if len(sys.argv) > 1 else "firefox"
        browser = getattr(playwright, browser_name).launch(headless=True)
        try:
            for viewport in (390, 1280):
                verify(browser, viewport)
                print(f"PASS {browser_name} {viewport}px preview/theme/edit/sandbox")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
