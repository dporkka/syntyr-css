"""Real-browser validation for Syntyr's native console popovers; optional Playwright smoke."""
from pathlib import Path
import os
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "examples/operations-console.html").as_uri()


def validate(browser, browser_name):
    for width in (320, 390, 1280):
        context = browser.new_context(viewport={"width": width, "height": 820}, java_script_enabled=False)
        page = context.new_page()
        page.goto(PAGE)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"{browser_name}: width {width} overflow"
        page.get_by_role("button", name="Choose example workspace: Northstar infrastructure").click()
        workspaces = page.locator("#ops-workspaces")
        assert workspaces.evaluate("(element) => element.matches(\":popover-open\")"), f"{browser_name}: workspace selector failed to open"
        assert workspaces.get_by_role("link", name="Northstar infrastructure").get_attribute("aria-current") == "true"
        ws_bounds = workspaces.bounding_box()
        assert ws_bounds and ws_bounds["x"] >= 0 and ws_bounds["x"] + ws_bounds["width"] <= width + 1, (browser_name, width, ws_bounds)
        page.keyboard.press("Escape")
        assert not workspaces.evaluate("(element) => element.matches(\':popover-open\')"), f"{browser_name}: workspace selector not dismissed"
        page.get_by_role("button", name="Open quick navigation").click()
        nav = page.locator("#ops-quick-actions")
        assert nav.evaluate("(element) => element.matches(':popover-open')"), f"{browser_name}: nav failed to open"
        assert nav.get_by_role("link", name="View deployment health").is_visible()
        bounds = nav.bounding_box()
        assert bounds and bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= width + 1, (browser_name, width, bounds)
        page.keyboard.press("Escape")
        assert not nav.evaluate("(element) => element.matches(':popover-open')"), f"{browser_name}: Escape did not dismiss"
        page.get_by_role("button", name="Show Gateway API resource details").click()
        peek = page.locator("#ops-resource-peek")
        assert peek.evaluate("(element) => element.matches(':popover-open')"), f"{browser_name}: peek failed to open"
        assert peek.get_by_text("gateway-001").is_visible()
        page.get_by_role("button", name="Close details").click()
        assert not peek.evaluate("(element) => element.matches(':popover-open')"), f"{browser_name}: close failed"
        context.close()
        print(f"PASS {browser_name} {width}px: native popovers open, dismiss, and fit without JavaScript")


with sync_playwright() as p:
    for browser_name in ("chromium", "firefox"):
        driver = getattr(p, browser_name)
        kwargs = {"headless": True}
        if browser_name == "chromium":
            executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
            if executable:
                kwargs.update(executable_path=executable, args=["--no-sandbox"])
        browser = driver.launch(**kwargs)
        try:
            validate(browser, browser_name)
        finally:
            browser.close()
