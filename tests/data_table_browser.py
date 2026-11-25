"""Optional real-browser table regression check; Playwright is maintainer-only."""
import os
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "examples/data-tables.html").as_uri()

def computed(page, selector, key):
    return page.locator(selector).first.evaluate(
        "(node, property) => getComputedStyle(node).getPropertyValue(property).trim()", key
    )

def main():
    with sync_playwright() as p:
        options = {"headless": True}
        executable = (os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                      or shutil.which("chromium") or shutil.which("chromium-browser"))
        if executable:
            options.update(executable_path=executable, args=["--no-sandbox"])
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={"width": 390, "height": 720})
        page.goto(PAGE)
        region = page.get_by_role("region", name="Scrollable sample revenue table")
        assert page.get_by_role("table").count() == 1
        assert region.count() == 1
        assert computed(page, ".syn-table--sticky thead th:first-child", "position") == "sticky"
        assert computed(page, ".syn-table-wrap--scroll", "overflow-y") == "auto"
        header = page.locator(".syn-table thead th:first-child")
        before = header.bounding_box()["y"]
        region_top = region.bounding_box()["y"]
        region.evaluate("(node) => { node.scrollTop = 150; }")
        after = header.bounding_box()["y"]
        assert abs(after - region_top) < 3, (before, after, region_top)
        assert after < before, "caption should scroll away while heading sticks"
        assert region.evaluate("(node) => node.scrollTop") > 0
        region.focus()
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)  # native smooth scrolling completes after the key event
        assert region.evaluate("(node) => node.scrollTop") > 150
        assert computed(page, ".syn-table thead th:first-child", "background-color") != "rgba(0, 0, 0, 0)"
        even = computed(page, ".syn-table tbody tr:nth-child(even)", "background-color")
        odd = computed(page, ".syn-table tbody tr:nth-child(odd)", "background-color")
        assert even != odd, ("striping not visible", even, odd)
        default_height = page.locator(".syn-table tbody tr:first-child").bounding_box()["height"]
        page.locator("body").evaluate("(node) => node.setAttribute('data-syn-density', 'spacious')")
        larger_height = page.locator(".syn-table tbody tr:first-child").bounding_box()["height"]
        assert larger_height > default_height, (default_height, larger_height)
        page.locator("body").evaluate("(node) => node.setAttribute('data-syn-theme', 'grid')")
        assert computed(page, "body", "color-scheme") == "dark"
        page.emulate_media(forced_colors="active")
        assert computed(page, ".syn-table--sticky thead th:first-child", "background-color") != "rgba(0, 0, 0, 0)"
        page.close()
        browser.close()
        print("PASS Chromium: sticky header, scroll keyboard, striping, density, themes, forced colors")

if __name__ == "__main__":
    main()
