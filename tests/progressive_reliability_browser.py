"""Cross-engine, script-disabled progressive-enhancement regression.

Development only: python3 tests/progressive_reliability_browser.py
Uses existing Playwright browser binaries; the application has no JS requirement.
"""
import argparse
import os
import shutil
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from examples.htmx_server import DemoHandler


def check(browser, name, base):
    context = browser.new_context(java_script_enabled=False,
                                  viewport={"width": 900, "height": 820})
    try:
        page = context.new_page()
        page.goto((ROOT / "examples/native-recipes.html").as_uri())
        field = page.locator("#example-email")
        label = page.locator('label[for="example-email"]')

        # Exercise real pointer hit testing, not element.click() from injected JS.
        for width in (900, 320):
            page.set_viewport_size({"width": width, "height": 820})
            field.blur()
            label.scroll_into_view_if_needed()
            box = label.bounding_box()
            assert box and box["width"] > 0 and box["height"] > 0, (name, width, box)
            page.mouse.click(box["x"] + box["width"] / 2,
                             box["y"] + box["height"] / 2)
            assert field.evaluate("e => document.activeElement === e"), (
                name, width, "clicking floating label must focus input")

        fallback = page.locator("#native-report-fallback")
        fallback.locator("summary").click()
        assert fallback.get_by_text("System report: operational.", exact=False).is_visible(), name

        # HTMX is unavailable by design in this context: the same GET form
        # must navigate to a complete document with submitted values.
        page.goto(base + "/examples/htmx.html")
        page.locator("#query").fill("Acme")
        page.locator("#search-button").click()
        page.wait_for_url("**/customers/search?q=Acme")
        assert page.get_by_text("Acme Corporation").is_visible(), name
        assert page.locator("#query").input_value() == "Acme", name
        assert page.locator("body.syn-root").count() == 1, name
        print("PASS", name, "native labels, disclosure, full GET fallback")
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", nargs="+",
                        choices=("chromium", "firefox", "webkit"),
                        default=("chromium", "firefox", "webkit"))
    names = parser.parse_args().browsers
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    failures = 0
    try:
        with sync_playwright() as playwright:
            for name in names:
                launch = {"headless": True}
                if name == "chromium":
                    binary = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                              or shutil.which("chromium")
                              or shutil.which("chromium-browser"))
                    if binary:
                        launch.update(executable_path=binary, args=["--no-sandbox"])
                try:
                    browser = getattr(playwright, name).launch(**launch)
                except Exception as exc:
                    failures += 1
                    print("BLOCKED", name, str(exc).splitlines()[0], flush=True)
                    continue
                try:
                    check(browser, name, f"http://127.0.0.1:{server.server_port}")
                except Exception as exc:
                    failures += 1
                    print("FAIL", name, type(exc).__name__, exc, flush=True)
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
