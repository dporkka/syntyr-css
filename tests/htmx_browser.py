"""Opt-in real HTMX E2E tests. Never add HTMX to Syntyr's runtime.

Fetch pinned HTMX 2.0.8 and optional HTMX 4.0.1 development-only fixtures:
  curl -fsSL https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js -o /tmp/syntyr-htmx.min.js
  curl -fsSL https://cdn.jsdelivr.net/npm/htmx.org@4.0.1/dist/htmx.min.js -o /tmp/syntyr-htmx4.min.js
  HTMX_JS_PATH=/tmp/syntyr-htmx.min.js HTMX4_JS_PATH=/tmp/syntyr-htmx4.min.js python3 tests/htmx_browser.py
Browser setup follows tests/browser_test.py (Playwright is dev-only).
"""
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
import os
import re
import shutil
import sys
import unittest

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.htmx_server import DemoHandler


class SlowDemoHandler(DemoHandler):
    def do_GET(self):
        if self.path.startswith("/customers/search"):
            # The test explicitly opens this gate after verifying HTMX's pending state.
            if not self.server.search_response_gate.wait(timeout=10):
                self.send_error(504, "Test response gate timed out")
                return
        super().do_GET()


class HtmxBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = os.environ.get("HTMX_JS_PATH", "")
        if not fixture or not Path(fixture).is_file():
            raise unittest.SkipTest("Set HTMX_JS_PATH to a local pinned HTMX 2.0.8 fixture")
        cls.htmx_js = Path(fixture)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SlowDemoHandler)
        cls.server.search_response_gate = Event()
        cls.server.search_response_gate.set()  # Default: native form fallback returns immediately.
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.p = sync_playwright().start()
        executable = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                      or shutil.which("chromium")
                      or shutil.which("chromium-browser"))
        launch = {"headless": True}
        if executable:
            launch.update(executable_path=executable, args=["--no-sandbox"])
        engine = os.environ.get("SYNTYR_BROWSER", "chromium")
        if engine not in ("chromium", "firefox", "webkit"):
            raise ValueError(f"Unsupported SYNTYR_BROWSER={engine}")
        if engine != "chromium":
            launch.pop("executable_path", None)
            launch.pop("args", None)
        try:
            cls.browser = getattr(cls.p, engine).launch(**launch)
        except Exception:
            cls.p.stop()
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=2)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.route(
            "https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js",
            lambda route: route.fulfill(path=str(self.htmx_js), content_type="text/javascript"),
        )

    def tearDown(self):
        self.server.search_response_gate.set()  # Prevent a stranded request on failure.
        try:
            self.assertEqual(self.errors, [])
        finally:
            self.context.close()

    def test_real_htmx_request_keeps_semantic_button_styled_and_swaps_results(self):
        self.page.goto(self.base + "/examples/htmx.html")
        self.page.wait_for_function("() => typeof window.htmx !== 'undefined'")
        button = self.page.locator("#search-button")
        height = button.evaluate("e => getComputedStyle(e).minHeight")
        self.assertEqual(height, "44px")
        self.page.locator("#query").fill("Acme")
        self.server.search_response_gate.clear()
        try:
            button.click()
            self.page.wait_for_function(
                "() => document.querySelector('#search-button').classList.contains('htmx-request')"
            )
            self.assertEqual(button.evaluate("e => getComputedStyle(e).minHeight"), height)
            self.assertTrue(button.is_disabled(), "HTMX must lock the submit button during a request")
            self.assertNotEqual(button.locator(".htmx-indicator").evaluate(
                "e => getComputedStyle(e).display"), "none")
        finally:
            self.server.search_response_gate.set()
        self.page.get_by_text("Acme Corporation").wait_for()
        self.assertIn("1 customers", self.page.locator("#results").inner_text())
        self.assertFalse(button.evaluate("e => e.classList.contains('htmx-request')"))
        self.assertFalse(button.is_disabled(), "Button must re-enable after the response")
        self.assertEqual(button.evaluate("e => getComputedStyle(e).minHeight"), height)
        self.assertEqual(self.page.locator("body").get_attribute("data-syn-theme"), "studio")

    def test_search_url_is_bookmarkable_and_full_reload_restores_input(self):
        self.page.goto(self.base + "/examples/htmx.html")
        self.page.wait_for_function("() => typeof window.htmx !== 'undefined'")
        self.page.locator("#query").fill("Northstar")
        self.page.locator("#search-button").click()
        self.page.get_by_text("Northstar Media").wait_for()
        self.page.wait_for_url("**/customers/search?q=Northstar")
        self.page.reload()
        self.page.get_by_text("Northstar Media").wait_for()
        self.assertEqual(self.page.locator("#query").input_value(), "Northstar")
        self.assertEqual(self.page.locator("body").get_attribute("data-syn-theme"), "studio")

    def test_htmx_v4_migrated_markup_and_swaps_results(self):
        fixture_name = os.environ.get("HTMX4_JS_PATH", "")
        if not fixture_name or not Path(fixture_name).is_file():
            self.skipTest("Set HTMX4_JS_PATH to pinned HTMX 4.0.1 fixture")
        # Verify Syntyr markup stays intact across a real v2-to-v4 migration.
        # Only the test changes the external runtime and version-specific htmx attributes.
        html = (Path(__file__).resolve().parents[1] / "examples/htmx.html").read_text()
        html = html.replace(
            '{"includeIndicatorStyles":false,"historyRestoreAsHxRequest":false}',
            '{"includeIndicatorCSS":false}',
        )
        html = html.replace('hx-disabled-elt="#search-button"', 'hx-disable="#search-button"')
        html = html.replace(
            "https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js",
            "https://cdn.jsdelivr.net/npm/htmx.org@4.0.1/dist/htmx.min.js",
        )
        html = re.sub(r'\s+integrity="[^"]+"', "", html)
        self.page.route(
            self.base + "/examples/htmx.html",
            lambda route: route.fulfill(body=html, content_type="text/html"),
        )
        self.page.route(
            "https://cdn.jsdelivr.net/npm/htmx.org@4.0.1/dist/htmx.min.js",
            lambda route: route.fulfill(path=fixture_name, content_type="text/javascript"),
        )
        self.page.goto(self.base + "/examples/htmx.html")
        self.page.wait_for_function("() => typeof window.htmx !== 'undefined'")
        self.page.locator("#query").fill("Acme")
        button = self.page.locator("#search-button")
        self.server.search_response_gate.clear()
        try:
            button.click()
            self.page.wait_for_function(
                "() => document.querySelector('#search-button').classList.contains('htmx-request')"
            )
            self.assertTrue(button.is_disabled())
            self.assertEqual(button.evaluate("e => getComputedStyle(e).minHeight"), "44px")
        finally:
            self.server.search_response_gate.set()
        self.page.get_by_text("Acme Corporation").wait_for()
        self.assertEqual(self.page.locator("#results").count(), 1)
        self.assertEqual(self.page.locator("body").get_attribute("data-syn-theme"), "studio")
        self.assertFalse(button.is_disabled())

    def test_failed_enhanced_request_offers_real_navigation_with_preserved_query(self):
        def unavailable(route):
            if route.request.headers.get("hx-request") == "true":
                route.fulfill(status=503, body="Service unavailable",
                              content_type="text/plain")
            else:
                route.continue_()

        self.page.route("**/customers/search*", unavailable)
        self.page.goto(self.base + "/examples/htmx.html")
        self.page.wait_for_function("() => typeof window.htmx !== 'undefined'")
        self.page.locator("#query").fill("Northstar")
        self.page.locator("#search-button").click()
        error = self.page.locator("#search-error")
        error.wait_for(state="visible")
        self.assertEqual(self.page.locator("#query").input_value(), "Northstar")
        self.assertEqual(self.page.locator("#native-search-link").get_attribute("href"),
                         "/customers/search?q=Northstar")
        self.page.unroute("**/customers/search*", unavailable)
        self.page.locator("#native-search-link").click()
        self.page.wait_for_url("**/customers/search?q=Northstar")
        self.page.get_by_text("Northstar Media").wait_for()
        self.assertEqual(self.page.locator("#query").input_value(), "Northstar")

    def test_without_htmx_script_native_form_loads_complete_document(self):
        self.page.route(
            "https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js",
            lambda route: route.abort(),
        )
        self.page.goto(self.base + "/examples/htmx.html")
        self.page.locator("#query").fill("Northstar")
        self.page.locator("#search-button").click()
        self.page.wait_for_url("**/customers/search?q=Northstar")
        self.assertEqual(self.page.locator("h1").inner_text(), "Customer search")
        self.assertIn("Northstar Media", self.page.locator("#results").inner_text())
        self.assertEqual(self.page.locator("#query").input_value(), "Northstar")


if __name__ == "__main__":
    unittest.main()
