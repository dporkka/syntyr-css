"""Maintainer-only native enterprise workspace browser regression."""
import os
from pathlib import Path
import re
import shutil

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "examples/enterprise-record-workspace.html").as_uri()
THEMES = ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal")
WIDTHS = (320, 390, 768, 1024, 1440, 1920)


def check_overflow(page, context):
    sizes = page.evaluate("""() => ({
        width:document.documentElement.clientWidth,
        scroll:document.documentElement.scrollWidth
    })""")
    assert sizes["scroll"] <= sizes["width"] + 1, (context, sizes)


def main():
    with sync_playwright() as p:
        executable = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
        options = {"headless": True}
        if executable:
            options.update(executable_path=executable, args=["--no-sandbox"])
        browser = p.chromium.launch(**options)
        try:
            page = browser.new_page(java_script_enabled=False)
            page.goto(PAGE)
            for theme in THEMES:
                page.locator("body").evaluate("(el, theme) => el.dataset.synTheme = theme", theme)
                for width in WIDTHS:
                    page.set_viewport_size({"width": width, "height": 900})
                    check_overflow(page, (theme, width))
                    assert page.get_by_role("table").count() == 3
            page.locator("body").evaluate("(el) => el.dataset.synTheme = 'studio'")
            page.set_viewport_size({"width": 390, "height": 720})
            # Browser-owned disclosure changes visible rows, not report totals.
            group = page.locator("#booked summary")
            group.focus()
            page.keyboard.press("Enter")
            assert not page.locator("#booked").evaluate("(el) => el.open")
            assert page.get_by_role("table").count() == 2
            assert page.locator("#potential").inner_text() == "$16,400"
            group.focus()
            page.keyboard.press("Space")
            assert page.locator("#booked").evaluate("(el) => el.open")
            assert page.get_by_role("table").count() == 3

            # Every opener names and activates its own read-only sheet, and
            # native Escape/explicit close dismiss without any client scripts.
            for index, name in enumerate(("INV-102", "INV-108", "INV-214", "INV-219", "INV-309", "INV-316")):
                opener = page.get_by_role("button", name=re.compile(name))
                opener.focus()
                page.keyboard.press("Enter")
                sheet = page.locator("#record-" + name.lower())
                assert sheet.evaluate("(el) => el.matches(':popover-open')")
                assert page.get_by_role("dialog").count() == 1
                assert sheet.get_by_role("heading", name="Record details").is_visible()
                if index % 2:
                    sheet.get_by_role("button", name="Done").click()
                else:
                    page.keyboard.press("Escape")
                assert not sheet.evaluate("(el) => el.matches(':popover-open')")
                assert opener.evaluate("(el) => document.activeElement === el")

            page.set_viewport_size({"width": 320, "height": 740})
            page.evaluate("document.documentElement.style.fontSize='64px'")
            check_overflow(page, "400% equivalent text zoom")
            page.evaluate("document.documentElement.style.fontSize=''")
            page.emulate_media(forced_colors="active")
            # Move focus by keyboard after the last mouse close action;
            # programmatic focus alone need not activate :focus-visible.
            group.focus()
            page.keyboard.press("Tab")
            page.keyboard.press("Shift+Tab")
            assert group.evaluate("(el) => document.activeElement === el && el.matches(':focus-visible') && getComputedStyle(el).outlineStyle !== 'none'")
            check_overflow(page, "forced colors")
            print("PASS Chromium: 7 themes × 6 viewports, 6 native sheets + focus return, disclosures, totals, 400% text reflow, forced colors, JavaScript disabled")
            page.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
