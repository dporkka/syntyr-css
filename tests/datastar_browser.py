"""Optional real Datastar/Syntyr browser integration.

Download a PINNED development-only fixture:
  curl -fsSL https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.5/bundles/datastar.js -o /tmp/syntyr-datastar-v1.0.5.js
  DATASTAR_JS_PATH=/tmp/syntyr-datastar-v1.0.5.js python3 tests/datastar_browser.py

Browser/Playwright are test-only; Syntyr's runtime remains pure CSS.
"""
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
import os
import shutil
import sys
import unittest

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from examples.datastar_server import DemoHandler


class GatedDemoHandler(DemoHandler):
    def do_GET(self):
        if self.path.startswith("/customers/search") and "text/event-stream" in self.headers.get("Accept", ""):
            if not self.server.response_gate.wait(timeout=10):
                self.send_error(504, "Demo request gate timed out")
                return
        super().do_GET()


class DatastarBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = os.environ.get("DATASTAR_JS_PATH", "")
        if not fixture or not Path(fixture).is_file():
            raise unittest.SkipTest("Set DATASTAR_JS_PATH to pinned local Datastar v1.0.5 bundle")
        cls.script = Path(fixture)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GatedDemoHandler)
        cls.server.response_gate = Event()
        cls.server.response_gate.set()
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.p = sync_playwright().start()
        executable = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                      or shutil.which("chromium") or shutil.which("chromium-browser"))
        options = {"headless": True}
        if executable:
            options.update(executable_path=executable, args=["--no-sandbox"])
        engine = os.environ.get("SYNTYR_BROWSER", "chromium")
        if engine not in ("chromium", "firefox", "webkit"):
            raise ValueError(f"Unsupported SYNTYR_BROWSER={engine}")
        try:
            cls.browser = getattr(cls.p, engine).launch(**options)
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
        self.page.on("pageerror", lambda err: self.errors.append(str(err)))
        self.page.route(
            "https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.5/bundles/datastar.js",
            lambda route: route.fulfill(path=str(self.script), content_type="text/javascript"),
        )

    def tearDown(self):
        self.server.response_gate.set()
        try:
            self.assertEqual(self.errors, [])
        finally:
            self.context.close()

    def open_page(self):
        self.page.goto(self.url + "/examples/datastar.html")
        # The reactive aria-busy binding is written only after Datastar bootstraps.
        self.page.wait_for_function(
            "() => document.querySelector('#customer-search').getAttribute('aria-busy') === 'false'")

    def test_real_signals_indicator_and_sse_morph_preserve_theme(self):
        self.open_page()
        self.assertEqual(self.page.locator("#customer-query").get_attribute("name"), "q")
        self.page.locator("#customer-query").fill("Acme")
        root = self.page.locator("main.syn-root")
        self.assertEqual(root.get_attribute("data-syn-theme"), "studio")
        self.server.response_gate.clear()
        try:
            self.page.locator("#search-button").click()
            self.page.wait_for_function(
                "() => document.querySelector('#customer-search').getAttribute('aria-busy') === 'true'")
            self.assertTrue(self.page.locator("#search-button").is_disabled())
            self.assertTrue(self.page.locator("#search-progress").is_visible())
            self.assertEqual(self.page.locator("#search-button").get_attribute("data-syn-state"), "loading")
            self.server.response_gate.set()
            self.page.get_by_text("Acme Corporation").wait_for()
            self.page.wait_for_function(
                "() => document.querySelector('#customer-search').getAttribute('aria-busy') === 'false'")
            self.assertFalse(self.page.locator("#search-button").is_disabled())
            self.assertFalse(self.page.locator("#search-progress").is_visible())
            self.assertEqual(root.get_attribute("data-syn-theme"), "studio")
            self.assertEqual(self.page.locator("#customer-results").count(), 1)
        finally:
            self.server.response_gate.set()

    def test_native_form_works_without_datastar(self):
        no_js = self.browser.new_context(java_script_enabled=False)
        page = no_js.new_page()
        try:
            page.goto(self.url + "/examples/datastar.html")
            page.locator("#customer-query").fill("Acme")
            page.locator("#search-button").click()
            page.get_by_text("Acme Corporation").wait_for()
            self.assertIn("q=Acme", page.url)
            self.assertEqual(page.locator("#customer-query").input_value(), "Acme")
            self.assertEqual(page.locator("main.syn-root").get_attribute("data-syn-theme"), "studio")
        finally:
            no_js.close()

    def test_unpoly_state_bridge_is_scoped_and_preserves_disabled(self):
        self.open_page()
        # Use an unbound element: Datastar owns the real submit button's
        # disabled attribute and may restore its reactive value.
        self.page.evaluate("""() => {
          const button = document.createElement('button');
          button.id = 'unpoly-button';
          button.className = 'syn-button up-active';
          button.textContent = 'Other action';
          document.querySelector('main.syn-root').append(button);
          const outside = button.cloneNode(true);
          outside.id = 'outside-button';
          document.body.append(outside);
        }""")
        button = self.page.locator("#unpoly-button")
        self.assertEqual(button.evaluate("e => getComputedStyle(e).cursor"), "progress")
        button.evaluate("e => e.disabled = true")
        self.assertNotEqual(button.evaluate("e => getComputedStyle(e).cursor"), "progress")
        self.assertNotEqual(
            self.page.locator("#outside-button").evaluate("e => getComputedStyle(e).cursor"),
            "progress")
        form = self.page.locator("#customer-search")
        form.evaluate("e => e.classList.add('up-active')")
        self.assertEqual(
            self.page.locator("#search-button").evaluate("e => getComputedStyle(e).cursor"),
            "progress")


if __name__ == "__main__":
    unittest.main()
