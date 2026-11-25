"""Optional real-browser regression for Syntyr's script-free interaction recipes.

Run with a developer-installed Playwright Python environment:
  python3 tests/interaction_recipe_browser.py --browsers chromium firefox

No application JavaScript is enabled in any test context. Test-side
Playwright inspection is not application runtime behavior.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def check_native_select(page):
    page.goto((ROOT / "examples/semantic-starter.html").as_uri())
    assert not page.locator("script").count()
    combo = page.get_by_role("combobox", name="Visual style")
    combo.select_option("noir")
    assert combo.input_value() == "noir"
    page.get_by_role("textbox", name="Project name").fill("Example")
    page.get_by_role("button", name="Preview query URL").click()
    assert "style=noir" in page.url and "project=Example" in page.url, page.url


def check_native_popover(page):
    page.goto((ROOT / "examples/native-apis.html").as_uri())
    assert not page.locator("script").count()
    trigger = page.get_by_role("button", name="OPEN POPOVER")
    trigger.click()
    popover = page.locator("#native-popover")
    assert popover.evaluate("(node) => node.matches(':popover-open')"), "popover did not open"
    assert popover.get_by_role("button", name="CLOSE").is_visible()
    page.keyboard.press("Escape")
    assert not popover.evaluate("(node) => node.matches(':popover-open')"), "Escape did not dismiss"


def check_native_dialog_fallback(page):
    page.goto((ROOT / "examples/native-apis.html").as_uri())
    page.get_by_role("button", name="OPEN MODAL").click()
    dialog = page.locator("#native-dialog")
    if dialog.evaluate("(node) => node.open"):
        assert dialog.evaluate("(node) => node.matches(':modal')"), "dialog is not modal"
        page.keyboard.press("Escape")
        assert not dialog.evaluate("(node) => node.open"), "Escape did not dismiss dialog"
        return "invoker supported"
    page.get_by_text("Read system status without a modal").click()
    assert page.get_by_text("System status: operational.").is_visible(), "fallback is inaccessible"
    return "invoker unsupported; accessible disclosure fallback verified"


def check_native_table_snapshot(page):
    page.goto((ROOT / "examples/data-tables.html").as_uri())
    table = page.get_by_role("table")
    assert table.count() == 1
    header = table.get_by_role("columnheader", name="Account")
    assert header.get_attribute("aria-sort") == "ascending"
    assert table.get_by_role("row").nth(1).inner_text().startswith("Atlas Outdoor")
    assert not header.locator("a, button").count(), "static sample must not claim live sorting"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browsers", nargs="+", default=["chromium"], choices=("chromium", "firefox", "webkit"))
    args = parser.parse_args()
    with sync_playwright() as playwright:
        for engine in args.browsers:
            options = {"headless": True}
            if engine == "chromium":
                executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
                if executable:
                    options.update(executable_path=executable, args=["--no-sandbox"])
            browser = getattr(playwright, engine).launch(**options)
            try:
                for width in (375, 1280):
                    context = browser.new_context(viewport={"width": width, "height": 820},
                                                  java_script_enabled=False)
                    page = context.new_page()
                    try:
                        check_native_select(page)
                        check_native_popover(page)
                        modal = check_native_dialog_fallback(page)
                        check_native_table_snapshot(page)
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                            engine, width, "unexpected horizontal overflow"
                        )
                        print(f"PASS {engine} {width}px: select/form, popover, dialog ({modal}), static table; no JS")
                    finally:
                        context.close()
            finally:
                browser.close()


if __name__ == "__main__":
    main()
